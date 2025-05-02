import datetime
from typing import Any

from bson.objectid import ObjectId
from DataAPI.models import Coordinates, Point

from .. import exceptions as exc


class AnnotationManager:
    """Annotation management for OpenLabel"""

    def __init__(self, db_manager):
        """Initialize with database manager"""
        self.db = db_manager.db

    def create_mock_image(
        self,
        project_id: ObjectId,
        filename: str,
        width: int,
        height: int,
        user_id: ObjectId,
    ) -> ObjectId:
        """Create a mock image for testing annotations"""
        # TODO: replace iamge operations to work with MongoDB's GridFS file storage system
        image_doc = {
            "projectId": project_id,
            "filename": filename,
            "path": f"mock/{filename}",  # Mock path
            "width": width,
            "height": height,
            "fileSize": width * height * 3,  # Mock size (3 bytes per pixel)
            "uploadedBy": user_id,
            "uploadedAt": datetime.datetime.now(datetime.timezone.utc),
            "metadata": {
                "format": filename.split(".")[-1] if "." in filename else "jpg",
                "exif": {},  # Empty for mock
            },
            "status": "unprocessed",
        }

        result = self.db.images.insert_one(image_doc)
        return result.inserted_id

    def get_images_by_project(self, project_id: ObjectId) -> list[dict]:
        """Get all images in a project"""
        return list(self.db.images.find({"projectId": project_id}))

    def create_bounding_box(
        self,
        image_id: ObjectId,
        project_id: ObjectId,
        label: str,
        coordinates: Coordinates,
        user_id: ObjectId,
    ) -> ObjectId:
        """Create a bounding box annotation"""

        # Ensure the image exists
        image = self.db.images.find_one({"_id": image_id})
        if not image:
            raise exc.ResourceNotFound("Image not found")

        # Check if user has permission to annotate in this project
        project = self.db.projects.find_one({"_id": project_id})
        if not project:
            raise exc.ResourceNotFound("Project not found")

        # Simple check that coordinates are within image bounds
        if (
            coordinates.x < 0
            or coordinates.y < 0
            or coordinates.x + coordinates.width > image["width"]
            or coordinates.y + coordinates.height > image["height"]
        ):
            raise ValueError("Bounding box coordinates outside image bounds")

        now = datetime.datetime.now(datetime.timezone.utc)

        annotation = {
            "imageId": image_id,
            "projectId": project_id,
            "type": "boundingBox",
            "label": label,
            "coordinates": coordinates,
            "createdBy": user_id,
            "createdAt": now,
            "updatedAt": now,
            "attributes": {},
            "confidence": 1.0,  # Manual annotation
        }

        result = self.db.annotations.insert_one(annotation)

        # Update image status
        self.db.images.update_one({"_id": image_id}, {"$set": {"status": "annotated"}})

        return result.inserted_id

    def create_polygon(
        self,
        image_id: ObjectId,
        project_id: ObjectId,
        label: str,
        points: list[Point],
        user_id: ObjectId,
    ) -> ObjectId:
        """Create a polygon annotation"""

        # Ensure the image exists
        image = self.db.images.find_one({"_id": image_id})
        if not image:
            raise ValueError("Image not found")

        # Check if user has permission to annotate in this project
        project = self.db.projects.find_one({"_id": project_id})
        if not project:
            raise ValueError("Project not found")

        # Simple check that coordinates are within image bounds
        for point in points:
            if (
                point.x < 0
                or point.y < 0
                or point.x > image["width"]
                or point.y > image["height"]
            ):
                raise ValueError("Polygon point outside image bounds")

        annotation = {
            "imageId": image_id,
            "projectId": project_id,
            "type": "polygon",
            "label": label,
            "coordinates": {"points": points},
            "createdBy": user_id,
            "createdAt": datetime.datetime.now(datetime.timezone.utc),
            "updatedAt": datetime.datetime.now(datetime.timezone.utc),
            "attributes": {},
            "confidence": 1.0,  # Manual annotation
        }

        result = self.db.annotations.insert_one(annotation)

        # Update image status
        self.db.images.update_one({"_id": image_id}, {"$set": {"status": "annotated"}})

        return result.inserted_id

    def get_annotations_by_image(self, image_id: ObjectId) -> list[dict]:
        """Get all annotations for an image"""
        return list(self.db.annotations.find({"imageId": image_id}))

    def get_annotations_by_project(self, project_id: ObjectId) -> list[dict]:
        """Get all annotations in a project"""
        return list(self.db.annotations.find({"projectId": project_id}))

    def update_annotation(
        self, annotation_id: ObjectId, update_data: dict[str, Any], user_id: ObjectId
    ) -> bool:
        """Update an annotation"""
        annotation = self.db.annotations.find_one({"_id": annotation_id})

        if not annotation:
            raise ValueError("Annotation not found")

        # Update the updatedAt field
        update_data["updatedAt"] = datetime.datetime.now(datetime.timezone.utc)

        result = self.db.annotations.update_one(
            {"_id": annotation_id}, {"$set": update_data}
        )

        return result.modified_count > 0

    def delete_annotation(self, annotation_id: ObjectId, user_id: ObjectId) -> bool:
        """Delete an annotation"""
        annotation = self.db.annotations.find_one({"_id": annotation_id})

        if not annotation:
            raise ValueError("Annotation not found")

        result = self.db.annotations.delete_one({"_id": annotation_id})

        # Check if this was the last annotation for the image
        annotations_count = self.db.annotations.count_documents(
            {"imageId": annotation["imageId"]}
        )

        if annotations_count == 0:
            # Update image status
            self.db.images.update_one(
                {"_id": annotation["imageId"]}, {"$set": {"status": "unprocessed"}}
            )

        return result.deleted_count > 0
