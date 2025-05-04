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

    def _create_annotation(self, annotation: models.Annotation) -> ObjectId:
        result = self.db.annotations.insert_one(
            annotation.model_dump(exclude=["annotationId"])
        )

        # Update image status
        self.db.images.update_one(
            {"_id": annotation.fileId},
            {"$set": {"status": models.FileStatus.ANNOTATED.value}},
        )

        return result.inserted_id

    def _verify_existence(self, project_id: ObjectId, file: ObjectId):
        # Ensure the file exists
        if not self.file_man.get_file_by_id(file):
            raise exc.ResourceNotFound(f"Image with ID '{str(file)}' not found")

        # Check if user has permission to annotate in this project
        _utils.project_exists(self.db, project_id, error=True)

    def create_object_detection_annotation(
        self,
        file_id: ObjectId,
        project_id: ObjectId,
        label: str,
        bbox: models.BBox,
        created_by: ObjectId,
    ) -> ObjectId:
        """Create a bounding box annotation"""

        # ensure existence of project and file
        self._verify_existence(project_id, file_id)

        # Simple check that coordinates are within image bounds
        # if (
        #     coordinates.x < 0
        #     or coordinates.y < 0
        #     or coordinates.x + coordinates.width > image["width"]
        #     or coordinates.y + coordinates.height > image["height"]
        # ):
        #     raise ValueError("Bounding box coordinates outside image bounds")
        annotation = models.ObjectDetectionAnnotation(
            annotationId=ObjectId(),
            fileId=file_id,
            projectId=project_id,
            createdBy=created_by,
            label=label,
            confidence=1.0,
            bbox=bbox,
        )

        return self._create_annotation(annotation)

    def create_segmentation_annotation(
        self,
        file_id: ObjectId,
        project_id: ObjectId,
        created_by: ObjectId,
        label: str,
        points: list[models.Point],
    ) -> ObjectId:
        """Create a polygon annotation"""

        # ensure existence of project and file
        self._verify_existence(project_id, file_id)

        annotation = models.SegmentationAnnotation(
            annotationId=ObjectId(),
            fileId=file_id,
            projectId=project_id,
            createdBy=created_by,
            label=label,
            points=points,
            confidence=1.0,
        )

        return self._create_annotation(annotation)

    def create_classification_annotation(
        self,
        file_id: ObjectId,
        project_id: ObjectId,
        created_by: ObjectId,
        label: str,
    ) -> ObjectId:
        """Create a polygon annotation"""

        # ensure existence of project and file
        self._verify_existence(project_id, file_id)

        annotation = models.ClassificationAnnotation(
            annotationId=ObjectId(),
            fileId=file_id,
            projectId=project_id,
            createdBy=created_by,
            label=label,
            confidence=1.0,
        )

        return self._create_annotation(annotation)

    def get_annotations_by_file(
        self, file_id: ObjectId, limit: int = 0
    ) -> list[models.Annotation]:
        """Get all annotations for an image"""
        annotations = self.db.annotations.find({"fileId": file_id}).limit(limit)
        return [
            models.get_annotation_model(ann["type"]).model_validate(ann)
            for ann in annotations
        ]

    def get_annotations_by_project(
        self, project_id: ObjectId, limit: int = 0
    ) -> list[models.Annotation]:
        """Get all annotations in a project"""
        annotations = self.db.annotations.find({"projectId": project_id}).limit(limit)
        return [
            models.get_annotation_model(ann["type"]).model_validate(ann)
            for ann in annotations
        ]

    def get_annotation_by_id(self, annotation_id: ObjectId) -> models.Annotation | None:
        """Gets a single annotation by ID"""
        ann = self.db.annotations.find_one({"_id": annotation_id})

        if ann is None:
            return None

        return models.get_annotation_model(ann["type"]).model_validate(ann)

    def update_annotation(
        self, annotation_id: ObjectId, update_data: models.UpdateAnnotation
    ) -> bool:
        """Update an annotation"""

        annotation = self.get_annotation_by_id(annotation_id)
        if not annotation:
            raise exc.ResourceNotFound(
                f"Annotation with ID {str(annotation_id)} does not exist"
            )

        try:
            update_data = update_data.model_dump(exclude_unset=True)
        except:
            raise exc.InvalidPatchMap("Invalid patch map.")

        # Update the updatedAt field
        update_data["updatedAt"] = datetime.datetime.now(datetime.timezone.utc)

        # do type conversion (both for "type" field and the annotation, if needed)
        unset = {}
        if "type" in update_data:
            new_type = update_data["type"]
            update_data["type"] = new_type.value

            if new_type != annotation.type:
                if annotation.type == models.AnnotationType.OBJECT_DETECTION:
                    unset = {"bbox": ""}
                elif annotation.type == models.AnnotationType.SEGMENTATION:
                    unset = {"points": ""}

        instruction = {"$set": update_data}

        if unset:
            instruction["$unset"] = unset

        result = self.db.annotations.update_one({"_id": annotation_id}, instruction)

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
            {"fileId": annotation["fileId"]}
        )

        if annotations_count == 0:
            # Update image status
            self.db.images.update_one(
                {"_id": annotation["fileId"]},
                {"$set": {"metadata.status": models.FileStatus.UNANNOTATED.value}},
            )

        return result.deleted_count > 0
