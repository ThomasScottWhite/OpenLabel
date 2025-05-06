import abc
import datetime
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from bson.objectid import ObjectId
from pymongo.database import Database

from .. import exceptions as exc
from .. import models
from ..config import CONFIG
from .annotation_manager import AnnotationManager
from .db_manager import MongoDBManager
from .file_manager import FileManager


class _Exporter(abc.ABC):

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
    def _export(self, project: models.Project, zip_file: zipfile.ZipFile): ...

    @property
    @abc.abstractmethod
    def export_format(self) -> models.ExportFormat: ...

    def export(self, project_id: ObjectId, directory: str | None = None) -> Path:
        project = self.db.projects.find_one({"_id": project_id})
        if not project:
            raise exc.ResourceNotFound("Project not found")

        project = models.Project.model_validate(project)

        if directory is None:
            directory = CONFIG.temp_dir

        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M")

        zip_path = (
            Path(CONFIG.temp_dir)
            / f"{str(project.projectId)}_{self.export_format.value}_{now_str}.zip"
        )
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, "w") as file:
                self._export(project, file)
        except:
            zip_path.unlink()
            raise

        return zip_path


class _COCOExporter(_Exporter):

    @property
    def export_format(self) -> models.ExportFormat:
        return models.ExportFormat.COCO

    def _export_images(
        self,
        zip_file: zipfile.ZipFile,
        project: models.Project,
        manifest: dict[str, Any],
    ) -> dict[str, tuple[models.FileMeta, int]]:
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
        info = {
            "year": datetime.datetime.now().year,
            "version": "1.0",
            "description": f"OpenLabel export - {project.name}",
            "contributor": "OpenLabel",
            "date_created": datetime.datetime.now().isoformat(),
        }

        manifest["info"] = info

    def _export(self, project: models.Project, zip_file: zipfile.ZipFile):
        # Get all images in project

        # Get all annotations in project

        # Construct final COCO format

        manifest = {}

        self._export_info(project, manifest)
        image_map = self._export_images(zip_file, project, manifest)
        self._export_annotations(project, image_map, manifest)

        zip_file.writestr("manifest.json", json.dumps(manifest, indent=2))


class _YOLOExporter(_Exporter):

    @property
    def export_format(self) -> models.ExportFormat:
        return models.ExportFormat.YOLO

    # def _export(self, project: models.Project, zip_file: zipfile.ZipFile):
    #     raise

    # TODO: this is the old YOLO export code; needs to be updated
    def export_yolo(self, project_id: ObjectId) -> Dict[str, List[str]]:
        """Export annotations in YOLO format"""

        project = self.db.projects.find_one({"_id": project_id})
        if not project:
            raise ValueError("Project not found")

        # Get all images in project
        images = list(self.db.images.find({"projectId": project_id}))

        # Create a map of image ID to image data
        image_map = {str(img["_id"]): img for img in images}

        # Get unique labels across all annotations
        all_annotations = list(self.db.annotations.find({"projectId": project_id}))
        labels = sorted(set(ann["label"] for ann in all_annotations))

        # Create label to index mapping (YOLO uses numeric class indices)
        label_map = {label: i for i, label in enumerate(labels)}

        # Generate YOLO annotations by image
        yolo_annotations = {}

        for image_id, image in image_map.items():
            # Get annotations for this image
            image_annotations = [
                a for a in all_annotations if str(a["fileId"]) == image_id
            ]

            # Format annotations for YOLO
            yolo_lines = []

            for ann in image_annotations:
                if ann["type"] == "boundingBox":
                    # YOLO format: <class_id> <center_x> <center_y> <width> <height>
                    # All values are normalized to [0, 1]
                    x = ann["coordinates"]["x"]
                    y = ann["coordinates"]["y"]
                    w = ann["coordinates"]["width"]
                    h = ann["coordinates"]["height"]

                    # Calculate center points and normalize
                    center_x = (x + w / 2) / image["width"]
                    center_y = (y + h / 2) / image["height"]
                    norm_width = w / image["width"]
                    norm_height = h / image["height"]

                    class_id = label_map[ann["label"]]

                    yolo_lines.append(
                        f"{class_id} {center_x:.6f} {center_y:.6f} {norm_width:.6f} {norm_height:.6f}"
                    )

                elif ann["type"] == "polygon":
                    # YOLO v5+ supports polygons using a different format
                    # For simplicity, we'll convert polygon to bounding box for basic YOLO format
                    points = ann["coordinates"]["points"]
                    x_coords = [p["x"] for p in points]
                    y_coords = [p["y"] for p in points]

                    # Calculate bounding box
                    x = min(x_coords)
                    y = min(y_coords)
                    w = max(x_coords) - x
                    h = max(y_coords) - y

                    # Calculate center points and normalize
                    center_x = (x + w / 2) / image["width"]
                    center_y = (y + h / 2) / image["height"]
                    norm_width = w / image["width"]
                    norm_height = h / image["height"]

                    class_id = label_map[ann["label"]]

                    yolo_lines.append(
                        f"{class_id} {center_x:.6f} {center_y:.6f} {norm_width:.6f} {norm_height:.6f}"
                    )

            # Store annotations for this image
            if yolo_lines:
                yolo_annotations[image["filename"]] = yolo_lines

        # Generate a classes.txt file
        classes_txt = [f"{label}\n" for label in labels]

        # Include the classes file in the result
        yolo_annotations["classes.txt"] = classes_txt

        return yolo_annotations


class _ClassificationExporter(_Exporter):

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
    ) -> Path:
        """Exports the specified project as the provided format, saving to a ZIP file.

        Args:
            project_id: The ID of the project to export.
            format: The format in which to export the project.
            export_dir: The directory in which to export the project. If None, the default temp_dir from the project
                configuration will be used. Defaults to None.

        Returns:
            The Path to the created ZIP file containing the exported data.
        """

        exporter: _Exporter

        if format == models.ExportFormat.COCO:
            exporter = _COCOExporter(self.db, self.file_man, self.ann_man)
        elif format == models.ExportFormat.YOLO:
            exporter = _YOLOExporter(self.db, self.file_man, self.ann_man)
        elif format == models.ExportFormat.CLASSIFICATION:
            exporter = _ClassificationExporter(self.db, self.file_man, self.ann_man)
        else:
            raise NotImplementedError("Specified format is not supported!")

        return exporter.export(project_id, export_dir)
