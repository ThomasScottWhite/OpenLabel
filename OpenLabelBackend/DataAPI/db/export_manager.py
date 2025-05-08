import abc
import datetime
import io
import json
import logging
import math
import random
import zipfile
from pathlib import Path
from typing import Any, Literal

import yaml
from bson.objectid import ObjectId
from pymongo.database import Database

from .. import exceptions as exc
from .. import models
from ..config import CONFIG
from .annotation_manager import AnnotationManager
from .db_manager import MongoDBManager
from .file_manager import FileManager

logger = logging.getLogger(__name__)


class _ExportStrategy(abc.ABC):

    def __init__(
        self,
        db: Database,
        file_manager: FileManager,
        annotation_manager: AnnotationManager,
    ):
        """Initialize with database manager"""
        self.db = db
        self.file_man = file_manager
        self.fs = file_manager.fs
        self.ann_man = annotation_manager

    @abc.abstractmethod
    def _export(self, project: models.Project, zip_file: zipfile.ZipFile):
        """Implementation of the export format."""
        ...

    @property
    @abc.abstractmethod
    def export_format(self) -> models.ExportFormat: ...

    def export(
        self,
        project_id: ObjectId,
        directory: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> Path:
        """Exports the specified project as a ZIP file, saving it to `directory`.

        Args:
            project_id: The ID of the project to export.
            directory: The directory to save the resultant ZIP file. If None, defaults to CONFIG.temp_dir.
                Defaults to None.
            options: Any additional options to pass to the exporter. If None, no options are passed.
                Defaults to None.

        Raises:
            exc.ResourceNotFound: If the specified project does not exist.

        Returns:
            The Path to the created ZIP file.
        """
        project = self.db.projects.find_one({"_id": project_id})
        if not project:
            raise exc.ResourceNotFound("Project not found")

        project = models.Project.model_validate(project)

        if directory is None:
            directory = CONFIG.temp_dir

        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M")

        # filename format: {project_id}_{export_format}_{timestamp}.zip
        zip_path = (
            Path(CONFIG.temp_dir)
            / f"{str(project.projectId)}_{self.export_format.value}_{now_str}.zip"
        )
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        # wrap in try block to delete created file upon error
        try:
            with zipfile.ZipFile(zip_path, "w") as file:
                self._export(project, file, **options)
        except:
            zip_path.unlink(missing_ok=True)
            raise

        return zip_path


class _COCOExporter(_ExportStrategy):
    """Exports data in the COCO format:

    /
      img1.ext
      img2.ext
      img3.ext
      ...
      manifest.json

    manifest.json follows the COCO format:
    https://docs.aws.amazon.com/rekognition/latest/customlabels-dg/md-coco-overview.html
    """

    @property
    def export_format(self) -> models.ExportFormat:
        return models.ExportFormat.COCO

    def _export_images(
        self,
        zip_file: zipfile.ZipFile,
        project: models.Project,
        manifest: dict[str, Any],
    ) -> dict[str, tuple[models.FileMeta, int]]:
        """Exports a project's images in the COCO format.

        Args:
            zip_file: The ZipFile to add the image files to. Files are named based on their FileID.
            project: The project to export.
            manifest: The COCO manifest dict to write an "images" section to.

        Returns:
            A Mapping mapping File ID to a pair containing that file's meta and the generate COCO image ID.
        """
        files = self.file_man.get_files_by_project(project.projectId)

        image_map: dict[str, tuple[models.FileMeta, int]] = {}
        coco_images = []
        image_id = 0

        for f in files:
            # COCO is for image files only
            if f.type != models.DataType.IMAGE:
                continue

            # create COCO image entry
            image_map[str(f.fileId)] = (f, image_id)
            file_name = f"{str(f.fileId)}{Path(f.filename).suffix}"
            coco_images.append(
                {
                    "id": image_id,
                    "file_name": file_name,
                    "width": f.width,
                    "height": f.height,
                    "date_captured": f.createdAt.isoformat(),
                }
            )
            image_id += 1

            # Download file
            data, _ = self.file_man.download_file(f.fileId)

            # Write file to zip
            zip_file.writestr(file_name, data.getvalue())

        manifest["images"] = coco_images

        return image_map

    def _export_annotations(
        self,
        project: models.Project,
        image_map: dict[str, tuple[models.FileMeta, int]],
        manifest: dict[str, Any],
    ):
        """Exports a projects annotations in COCO format, adding them to `manifest`.

        Args:
            project: The project being exported.
            image_map: A Mapping from File ID to a pair (FileMeta, COCO image ID). Is the same as what's returned by `self._export_images`.
            manifest: The manifest dict to write the annotations to.

        Raises:
            NotImplementedError: If a specific annotation type is not supported.
        """
        raw_annotations = self.ann_man.get_annotations_by_project(project.projectId)

        categories = []
        category_id_map = {}

        # Format annotations for COCO
        coco_annotations = []
        ann_id = 0
        for ann in raw_annotations:
            # skip annotations for images not in our image map
            if str(ann.fileId) not in image_map:
                continue

            # create a COCO category for the label if one does not exist
            if ann.label not in category_id_map:
                category_id_map[ann.label] = ann_id
                categories.append(dict(id=ann_id, name=ann.label))

            # create the annotation entry
            if ann.type == models.AnnotationType.OBJECT_DETECTION:

                # convert bounding boxes to COCO format
                img, img_id = image_map[str(ann.fileId)]
                x = ann.bbox.x * img.width
                width = ann.bbox.width * img.width
                y = ann.bbox.y * img.height
                height = ann.bbox.height * img.height

                x += width / 2
                y += height / 2

                coco_annotations.append(
                    dict(
                        id=ann_id,
                        image_id=img_id,
                        category_id=category_id_map[ann.label],
                        area=width * height,
                        bbox=list(map(round, (x, y, width, height))),
                    )
                )
            else:
                raise NotImplementedError(
                    "COCO export not implemented for specified type!"
                )

            ann_id += 1

        manifest["annotations"] = coco_annotations
        manifest["categories"] = categories

    def _export_info(self, project: models.Project, manifest: dict[str, Any]):
        """Adds info section to `manifest`.

        Args:
            project: The project to export.
            manifest: The manifest dict to add info to.
        """
        info = {
            "year": datetime.datetime.now().year,
            "version": "1.0",
            "description": f"OpenLabel export - {project.name}",
            "contributor": "OpenLabel",
            "date_created": datetime.datetime.now().isoformat(),
        }

        manifest["info"] = info

    def _export(self, project: models.Project, zip_file: zipfile.ZipFile):
        # COCO manifest JSON
        manifest = {}

        self._export_info(project, manifest)
        image_map = self._export_images(zip_file, project, manifest)
        self._export_annotations(project, image_map, manifest)

        zip_file.writestr("manifest.json", json.dumps(manifest, indent=2))


_YOLO_DATA_SUBDIR = Literal["train", "val"]


class _YOLOExporter(_ExportStrategy):
    """Exoprts in the YOLO format:

    /
      data.yaml
      images/
        train/
          img1.ext
          img2.ext
          ...
        val/
          img3.ext
          ...
      labels/
        train/
          img1.txt
          img2.txt
          ...
        val/
          img3.txt
          ...

    See more: https://docs.ultralytics.com/datasets/detect/
    """

    @property
    def export_format(self) -> models.ExportFormat:
        return models.ExportFormat.YOLO

    def _export_images(
        self,
        project: models.Project,
        zip_file: zipfile.ZipFile,
        validation_ratio: float,
    ) -> dict[str, _YOLO_DATA_SUBDIR]:
        """Exports the project's images to the provided ZIP file.

        Args:
            project: The project to export.
            zip_file: The ZipFile to save data to.
            validation_ratio: The percentage of the dataset to use as validation data.

        Returns:
            A mapping from FileID (as str) to its subdirectory.
        """

        files = self.file_man.get_files_by_project(project.projectId)

        # shuffle files so sampling is random
        random.shuffle(files)

        val_count = math.ceil(validation_ratio * len(files))

        # zip data with the subirectory they'll be associated with
        chunks = zip(("train", "val"), (files[val_count:], files[:val_count]))

        image_map: dict[str, _YOLO_DATA_SUBDIR] = {}

        for subdir, file_subset in chunks:
            for file in file_subset:
                id_str = str(file.fileId)
                if file.type != models.DataType.IMAGE:
                    logger.warning(
                        f"Skipping file {id_str} in {self.export_format.value} export because it is not an image!"
                    )
                    continue

                image_map[id_str] = subdir
                file_name = f"{id_str}{Path(file.filename).suffix}"

                data, _ = self.file_man.download_file(file.fileId)

                zip_file.writestr(f"images/{subdir}/{file_name}", data.getvalue())

        return image_map

    def _collect_annotations(
        self,
        project: models.Project,
    ) -> tuple[dict[str, list[str]], dict[int, str]]:
        """Collects and formats annotations for YOLO annotation export.

        Args:
            project: The project to collect annotations from.

        Returns:
            A pair where the first element is a mapping from FileID (as str) to a list of YOLO-formatted annotations
                and the second element maps annotation class ID to its string name.
        """
        annotations = self.ann_man.get_annotations_by_project(project.projectId)

        formatted_annotations: dict[str, list[str]] = {}

        ann_id = 0
        name_mapping: dict[str, int] = {}
        for ann in annotations:
            # create new YOLO annotation name
            if ann.label not in name_mapping:
                name_mapping[ann.label] = ann_id
                ann_id += 1

            # create the annotation entry
            if ann.type == models.AnnotationType.OBJECT_DETECTION:

                # our annotations are stored in the format YOLO likes, so just convert to str
                bbox = ann.bbox
                yolo_annotation = f"{name_mapping[ann.label]} {bbox.x} {bbox.y} {bbox.width} {bbox.height}"

                file_id_str = str(ann.fileId)
                if file_id_str not in formatted_annotations:
                    formatted_annotations[file_id_str] = [yolo_annotation]
                else:
                    formatted_annotations[file_id_str].append(yolo_annotation)
            else:
                logger.warning(
                    f"YOLO export not supported for annotation type {ann.type.value}"
                )

        # reverse the keys/values of name_mapping to match expected output
        return formatted_annotations, {id_: name for name, id_ in name_mapping.items()}

    def _save_annotations(
        self,
        zip_file: zipfile.ZipFile,
        annotations: dict[str, list[str]],
        image_dirs: dict[str, _YOLO_DATA_SUBDIR],
    ):
        """Saves the provided annotations to the provided ZIP file.

        Args:
            zip_file: The file to save the YOLO annotations to.
            annotations: A mapping from FileIds (as str) to their corresponding YOLO-formatted annotations.
                Essentially expects the annotations output from self._collect_annotations.
            image_dirs: A mapping from FileIds (as str) to the subdirectory they were stored under.
                Essentially expects the output of self._export_images.
        """

        for file_id, ann in annotations.items():
            if file_id not in image_dirs:
                logger.warning(f"File {file_id} not found in image map; skipping...")
                continue

            file_name = f"{file_id}.txt"
            content = "\n".join(ann)

            zip_file.writestr(f"labels/{image_dirs[file_id]}/{file_name}", content)

    def _export(
        self,
        project: models.Project,
        zip_file: zipfile.ZipFile,
        validation_ratio: float = 0.1,
    ):
        """Exports a project in YOLO format.

        Args:
            project: The project to export.
            zip_file: The ZIP file to export the project to.
            validation_ratio: The percentage of data to use as validation data. Must be in [0, 1]. Defaults to 0.1.

        Raises:
            ValueError: If validation_ratio is not in the interval [0, 1].
        """
        if not 0.0 <= validation_ratio <= 1.0:
            raise ValueError("Validation ration must be between 0 and 1.")

        manifest = dict(path=".", train="images/train", val="images/val")

        image_dirs = self._export_images(project, zip_file, validation_ratio)
        annotations, name_map = self._collect_annotations(project)
        self._save_annotations(zip_file, annotations, image_dirs)

        manifest["names"] = name_map

        # yaml library does not have a dumps function, so have to dump to buffer manually instead
        yaml_buffer = io.StringIO()
        yaml.dump(manifest, yaml_buffer)

        zip_file.writestr("data.yaml", yaml_buffer.getvalue())


class _ClassificationExporter(_ExportStrategy):
    """Exports in the following format:

    data/
      classname1/
        datafile_marked_as_classname1_1.ext
        datafile_marked_as_classname1_2.ext
        ...
      classname1/
        datafile_marked_as_classname2_2.ext
      ...
    """

    @property
    def export_format(self) -> models.ExportFormat:
        return models.ExportFormat.CLASSIFICATION

    def _export(self, project: models.Project, zip_file: zipfile.ZipFile):

        annotations = self.ann_man.get_annotations_by_project(project.projectId)

        for ann in annotations:
            if not ann.type == models.AnnotationType.CLASSIFICATION:
                continue

            data, file = self.file_man.download_file(ann.fileId)

            zip_file.writestr(
                f"data/{ann.label.strip()}/{file.filename}", data.getvalue()
            )


class ExportManager:
    """Export functionality for OpenLabel"""

    def __init__(
        self,
        db_manager: MongoDBManager,
        file_manager: FileManager,
        annotation_manager: AnnotationManager,
    ):
        """Initialize with database manager"""
        self.db = db_manager.db
        self.file_man = file_manager
        self.fs = file_manager.fs
        self.ann_man = annotation_manager

    def export_project(
        self,
        project_id: ObjectId,
        format: models.ExportFormat,
        export_dir: str | None = None,
        export_options: dict[str, Any] | None = None,
    ) -> Path:
        """Exports the specified project as the provided format, saving to a ZIP file.

        Args:
            project_id: The ID of the project to export.
            format: The format in which to export the project.
            export_dir: The directory in which to export the project. If None, the default temp_dir from the project
                configuration will be used. Defaults to None.
            export_options: Any additional options to pass to the exporter. If None, no options are passed.
                Defaults to None.

        Returns:
            The Path to the created ZIP file containing the exported data.
        """

        exporter: _ExportStrategy

        if export_options is None:
            export_options = {}

        if format == models.ExportFormat.COCO:
            exporter = _COCOExporter(self.db, self.file_man, self.ann_man)
        elif format == models.ExportFormat.YOLO:
            exporter = _YOLOExporter(self.db, self.file_man, self.ann_man)
        elif format == models.ExportFormat.CLASSIFICATION:
            exporter = _ClassificationExporter(self.db, self.file_man, self.ann_man)
        else:
            raise NotImplementedError("Specified format is not supported!")

        return exporter.export(project_id, export_dir, export_options)
