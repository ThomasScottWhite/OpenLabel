import datetime
from typing import Any, Mapping

from bson.objectid import ObjectId

from .. import exceptions as exc
from .. import models
from . import _utils
from .db_manager import MongoDBManager
from .file_manager import FileManager


class AnnotationManager:
    """Annotation management for OpenLabel"""

    def __init__(self, db_manager: MongoDBManager, file_manager: FileManager):
        """Initialize with database manager"""
        self.db = db_manager.db
        self.file_man = file_manager
        self.fs = file_manager.fs

    def _create_annotation(self, annotation: models.BaseAnnotatation) -> ObjectId:
        result = self.db.annotations.insert_one(annotation.model_dump())

        # Update image status
        self.db.images.update_one(
            {"_id": annotation.fileId},
            {"$set": {"status": models.FileStatus.ANNOTATED.value}},
        )

        return result.inserted_id

    def create_bounding_box(
        self,
        image_id: ObjectId,
        project_id: ObjectId,
        label: str,
        coordinates: models.Coordinates,
        user_id: ObjectId,
    ) -> ObjectId:
        """Create a bounding box annotation"""

        # Ensure the image exists
        if not self.file_man.get_file_by_id(image_id):
            raise exc.ResourceNotFound(f"Image with ID '{str(image_id)}' not found")

        # Check if user has permission to annotate in this project
        _utils.project_exists(self.db, project_id, error=True)

        # Simple check that coordinates are within image bounds
        # if (
        #     coordinates.x < 0
        #     or coordinates.y < 0
        #     or coordinates.x + coordinates.width > image["width"]
        #     or coordinates.y + coordinates.height > image["height"]
        # ):
        #     raise ValueError("Bounding box coordinates outside image bounds")

        annotation = models.BoundingBoxAnnotation(
            fileId=image_id,
            projectId=project_id,
            label=label,
            coordinates=coordinates,
            createdBy=user_id,
            confidence=1.0,
        )

        return self._create_annotation(annotation)

    def create_polygon(
        self,
        image_id: ObjectId,
        project_id: ObjectId,
        label: str,
        points: list[models.Point],
        user_id: ObjectId,
    ) -> ObjectId:
        """Create a polygon annotation"""

        # Ensure the image exists
        if not self.file_man.get_file_by_id(image_id):
            raise exc.ResourceNotFound(f"Image with ID '{str(image_id)}' not found")

        # Check if user has permission to annotate in this project
        _utils.project_exists(self.db, project_id, error=True)

        annotation = models.PolygonAnnotation(
            fileId=image_id,
            projectId=project_id,
            label=label,
            coordinates=models.Points(points=points),
            createdBy=user_id,
            confidence=1.0,
        )

        return self._create_annotation(annotation)

    def get_annotations_by_file(self, image_id: ObjectId, limit: int = 0) -> list[dict]:
        """Get all annotations for an image"""
        return list(self.db.annotations.find({"imageId": image_id}).limit(limit))

    def get_annotations_by_project(
        self, project_id: ObjectId, limit: int = 0
    ) -> list[dict]:
        """Get all annotations in a project"""
        return list(self.db.annotations.find({"projectId": project_id}).limit(limit))

    def get_annotation_by_id(self, annotation_id: ObjectId) -> dict[str, Any] | None:
        """Gets a single annotation by ID"""
        return self.db.annotations.find_one({"_id": annotation_id})

    def update_annotation(
        self, annotation_id: ObjectId, update_data: Mapping[str, Any]
    ) -> bool:
        """Update an annotation"""

        annotation = self.db.annotations.find_one({"_id": annotation_id})
        if not annotation:
            raise exc.ResourceNotFound(
                f"Annotation with ID {str(annotation_id)} does not exist"
            )

        try:
            update_data = models.UpdateAnnotation(**update_data).model_dump(
                exclude_unset=True
            )
        except:
            raise exc.InvalidPatchMap("Invalid patch map.")

        if "coordinates" in update_data:
            if type(update_data["coordinates"]) is dict:
                update_data["type"] = models.AnnotationType.BOUNDING_BOX.value
            else:
                update_data["type"] = models.AnnotationType.POLYGON.value

        # Update the updatedAt field
        update_data["updatedAt"] = datetime.datetime.now(datetime.timezone.utc)

        result = self.db.annotations.update_one(
            {"_id": annotation_id}, {"$set": update_data}
        )

        return result.modified_count > 0

    def delete_annotation(self, annotation_id: ObjectId) -> bool:
        """Delete an annotation"""
        annotation = self.get_annotation_by_id(annotation_id)

        if not annotation:
            raise exc.ResourceNotFound(
                f"Annotation with ID `{str(annotation_id)}` not found"
            )

        result = self.db.annotations.delete_one({"_id": annotation_id})

        # Check if this was the last annotation for the image
        annotations_count = self.db.annotations.count_documents(
            {"imageId": annotation["imageId"]}
        )

        if annotations_count == 0:
            # Update image status
            self.db.images.update_one(
                {"_id": annotation["imageId"]},
                {"$set": {"metadata.status": models.FileStatus.UNANNOTATED.value}},
            )

        return result.deleted_count > 0
