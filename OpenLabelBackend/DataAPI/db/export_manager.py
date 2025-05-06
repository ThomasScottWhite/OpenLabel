import datetime
import json
import zipfile
from pathlib import Path
from typing import Dict, List

from bson.objectid import ObjectId

from .. import exceptions as exc
from .. import models
from ..config import CONFIG
from .annotation_manager import AnnotationManager
from .db_manager import MongoDBManager
from .file_manager import FileManager


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

    def export_coco(self, project_id: ObjectId) -> Path:
        """Export annotations in COCO format"""

        # TODO: would probably want to verify that disk has enough space to create dataset
        # TODO: batching this would also be awesome

        project: models.Project = self.db.projects.find_one({"_id": project_id})
        if not project:
            raise exc.ResourceNotFound("Project not found")

        # Get all images in project
        files = self.file_man.get_files_by_project(project_id)

        # Get all annotations in project
        raw_annotations = self.ann_man.get_annotations_by_project(project_id)

        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M")

        zip_path = Path(CONFIG.temp_dir) / f"{str(project['_id'])}_COCO_{now_str}.zip"
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        # Format images for COCO
        image_map: dict[str, tuple[models.FileMeta, int]] = {}
        coco_images = []
        image_id = 0

        # TODO: this could probably unironically benefit from the Template pattern
        # like, have persistent procedure of saving files, annotations, etc.
        try:
            with zipfile.ZipFile(zip_path, "w") as f:
                for file in files:
                    # COCO is for image files only
                    if file.type != models.DataType.IMAGE:
                        continue

                    # create COCO image entry
                    image_map[str(file.fileId)] = (file, image_id)
                    file_name = f"{str(file.fileId)}{Path(file.filename).suffix}"
                    coco_images.append(
                        {
                            "id": image_id,
                            "file_name": file_name,
                            "width": file.width,
                            "height": file.height,
                            "date_captured": file.createdAt.isoformat(),
                        }
                    )
                    image_id += 1

                    # Download file
                    data, _ = self.file_man.download_file(file.fileId)

                    # Write file to zip
                    f.writestr(file_name, data.getvalue())

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

                # Construct final COCO format
                coco_output = {
                    "info": {
                        "year": datetime.datetime.now().year,
                        "version": "1.0",
                        "description": f"OpenLabel export - {project['name']}",
                        "contributor": "OpenLabel",
                        "date_created": datetime.datetime.now().isoformat(),
                    },
                    "images": coco_images,
                    "annotations": coco_annotations,
                    "categories": categories,
                }

                f.writestr("manifest.json", json.dumps(coco_output, indent=2))
        except:
            zip_path.unlink()
            raise

        return zip_path

    def export_yolo(self, project_id: ObjectId) -> Dict[str, List[str]]:
        """Export annotations in YOLO format"""

        # TODO: implemenet this

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
