import datetime
from typing import Dict, List

from bson.objectid import ObjectId

from .db_manager import MongoDBManager


class ExportManager:
    """Export functionality for OpenLabel"""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize with database manager"""
        self.db = db_manager.db

    def export_coco(self, project_id: ObjectId) -> Dict:
        """Export annotations in COCO format"""
        project = self.db.projects.find_one({"_id": project_id})
        if not project:
            raise ValueError("Project not found")

        # Get all images in project
        images = list(self.db.images.find({"projectId": project_id}))

        # Get all annotations in project
        annotations = list(self.db.annotations.find({"projectId": project_id}))

        # Get unique labels
        labels = set()
        for ann in annotations:
            labels.add(ann["label"])

        # Create categories
        categories = []
        for i, label in enumerate(sorted(labels)):
            categories.append({"id": i + 1, "name": label, "supercategory": "none"})

        # Create label to id mapping
        label_map = {cat["name"]: cat["id"] for cat in categories}

        # Format images for COCO
        coco_images = []
        for i, img in enumerate(images):
            coco_images.append(
                {
                    "id": i + 1,
                    "file_name": img["filename"],
                    "width": img["width"],
                    "height": img["height"],
                }
            )

        # Image id mapping for annotations
        img_id_map = {str(img["_id"]): i + 1 for i, img in enumerate(images)}

        # Format annotations for COCO
        coco_annotations = []
        for i, ann in enumerate(annotations):
            if ann["type"] == "boundingBox":
                x, y = ann["coordinates"]["x"], ann["coordinates"]["y"]
                w, h = ann["coordinates"]["width"], ann["coordinates"]["height"]

                coco_annotations.append(
                    {
                        "id": i + 1,
                        "image_id": img_id_map[str(ann["fileId"])],
                        "category_id": label_map[ann["label"]],
                        "bbox": [x, y, w, h],
                        "area": w * h,
                        "segmentation": [],
                        "iscrowd": 0,
                    }
                )
            elif ann["type"] == "polygon":
                # Convert points to COCO segmentation format
                points = ann["coordinates"]["points"]
                flat_points = []
                for p in points:
                    flat_points.extend([p["x"], p["y"]])
                segmentation = [flat_points]

                # Calculate bounding box from polygon points
                x_coords = [p["x"] for p in points]
                y_coords = [p["y"] for p in points]
                x, y = min(x_coords), min(y_coords)
                w, h = max(x_coords) - x, max(y_coords) - y

                coco_annotations.append(
                    {
                        "id": i + 1,
                        "image_id": img_id_map[str(ann["fileId"])],
                        "category_id": label_map[ann["label"]],
                        "bbox": [x, y, w, h],
                        "area": w * h,  # Approximate
                        "segmentation": segmentation,
                        "iscrowd": 0,
                    }
                )

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

        return coco_output

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
