import datetime

from bson.objectid import ObjectId
from pymongo.client_session import ClientSession

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

    def _create_annotation(
        self, annotation: models.Annotation, session: ClientSession | None = None
    ) -> ObjectId:
        """Helper function that creates an annotation based on an Annotation object.

        Args:
            annotation: The annotation to create.
            session: The pymongo ClientSession to use. Defaults to None.

        Returns:
            The ID of the inserted annotation.
        """
        result = self.db.annotations.insert_one(
            annotation.model_dump(exclude=["annotationId"]), session=session
        )

        # Update image status
        self.db.files.update_one(
            {"_id": annotation.fileId},
            {"$set": {"metadata.status": models.FileStatus.ANNOTATED.value}},
            session=session,
        )

        return result.inserted_id

    def _verify_existence(
        self,
        project_id: ObjectId,
        file_id: ObjectId,
        session: ClientSession | None = None,
    ):
        """Checks for the existence of the provided file and project.

        Args:
            project_id: The project ID.
            file: The file ID
            session: The pymongo ClientSession to use. Defaults to None.

        Raises:
            exc.ResourceNotFound: If either the provided file or project does not exist.
        """
        # Ensure the file exists
        if not self.file_man.get_file_by_id(file_id, session=session):
            raise exc.ResourceNotFound(f"Image with ID '{str(file_id)}' not found")

        # Check if user has permission to annotate in this project
        _utils.project_exists(self.db, project_id, error=True, session=session)

    def create_object_detection_annotation(
        self,
        file_id: ObjectId,
        project_id: ObjectId,
        label: str,
        bbox: models.BBox,
        created_by: ObjectId,
        session: ClientSession | None = None,
    ) -> ObjectId:
        """Creates an object detection annotation.

        Args:
            file_id: The ID of the file the annotation corresponds with.
            project_id: The ID of the project the annotation corresponds with.
            created_by: The ID of the user that created the annotation.
            label: The annotation label
            bbox: The bounding box encompassing the object this annotation labels.
            session: The pymongo ClientSession to use. Defaults to None.

        Returns:
            The ID of the inserted annotation.
        """

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

        return self._create_annotation(annotation, session=session)

    def create_segmentation_annotation(
        self,
        file_id: ObjectId,
        project_id: ObjectId,
        created_by: ObjectId,
        label: str,
        points: list[models.Point],
        session: ClientSession | None = None,
    ) -> ObjectId:
        """Creates a segmentation annotation.

        Args:
            file_id: The ID of the file the annotation corresponds with.
            project_id: The ID of the project the annotation corresponds with.
            created_by: The ID of the user that created the annotation.
            label: The annotation label.
            points: A list of points forming the polygon segmenting the image.
            session: The pymongo ClientSession to use. Defaults to None.

        Returns:
            The ID of the inserted annotation.
        """

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

        return self._create_annotation(annotation, session=session)

    def create_classification_annotation(
        self,
        file_id: ObjectId,
        project_id: ObjectId,
        created_by: ObjectId,
        label: str,
        session: ClientSession | None = None,
    ) -> ObjectId:
        """Creates a classification annotation.

        Args:
            file_id: The ID of the file the annotation corresponds with.
            project_id: The ID of the project the annotation corresponds with.
            created_by: The ID of the user that created the annotation.
            label: The annotation label
            session: The pymongo ClientSession to use. Defaults to None.

        Returns:
            The ID of the inserted annotation.
        """

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

        return self._create_annotation(annotation, session=session)

    def get_annotations_by_file(
        self, file_id: ObjectId, limit: int = 0, session: ClientSession | None = None
    ) -> list[models.Annotation]:
        """Returns a list of all annotations for a file.

        Args:
            file_id: The ID of the file to fetch annotations for.
            limit: The maximum number of annotations to return. Defaults to 0.
            session: The pymongo ClientSession to use. Defaults to None.
        """
        annotations = self.db.annotations.find(
            {"fileId": file_id}, session=session
        ).limit(limit)
        return [
            models.get_annotation_model(ann["type"]).model_validate(ann)
            for ann in annotations
        ]

    def get_annotations_by_project(
        self, project_id: ObjectId, limit: int = 0, session: ClientSession | None = None
    ) -> list[models.Annotation]:
        """Returns a list of all annotations for a project.

        Args:
            project_id: The ID of the project to fetch annotations for.
            limit: A limit to how many annotations can be returned. Defaults to 0.
            session: The pymongo ClientSession to use. Defaults to None.
        """
        annotations = self.db.annotations.find(
            {"projectId": project_id}, session=session
        ).limit(limit)
        return [
            models.get_annotation_model(ann["type"]).model_validate(ann)
            for ann in annotations
        ]

    def get_annotation_by_id(
        self, annotation_id: ObjectId, session: ClientSession | None = None
    ) -> models.Annotation | None:
        """Returns the annotation corresponding to the provided annotation_id, or None if it does not exist.

        Args:
            annotation_id: The ID of the annotation to fetch.
            session: The pymongo ClientSession to use. Defaults to None.
        """
        ann = self.db.annotations.find_one({"_id": annotation_id}, session=session)

        if ann is None:
            return None

        return models.get_annotation_model(ann["type"]).model_validate(ann)

    def update_annotation(
        self,
        annotation_id: ObjectId,
        update_data: models.UpdateAnnotation,
        session: ClientSession | None = None,
    ) -> bool:
        """Updates an annotation.

        Args:
            annotation_id: The ID of the annotation to update.
            update_data: A specification of what to update, interpretted as a patch/partial update.
            session: The pymongo ClientSession to use. Defaults to None.

        Raises:
            exc.ResourceNotFound: If the annotation to update does not exist.

        Returns:
            True if something was updated, False otherwise.
        """

        annotation = self.get_annotation_by_id(annotation_id)
        if not annotation:
            raise exc.ResourceNotFound(
                f"Annotation with ID {str(annotation_id)} does not exist"
            )

        update_data = update_data.model_dump(exclude_unset=True)

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

        result = self.db.annotations.update_one(
            {"_id": annotation_id}, instruction, session=session
        )

        return result.modified_count > 0

    def delete_annotation(
        self, annotation_id: ObjectId, session: ClientSession | None = None
    ) -> bool:
        """Deletes an annotation by ID.

        Args:
            annotation_id: The ID of the annotation to delete.
            session: The pymongo ClientSession to use. Defaults to None.

        Raises:
            exc.ResourceNotFound: If the specified annotation does not exist.

        Returns:
            True if something was deleted, False otherwise.
        """
        annotation = self.get_annotation_by_id(annotation_id, session=session)

        if not annotation:
            raise exc.ResourceNotFound(
                f"Annotation with ID `{str(annotation_id)}` not found"
            )

        result = self.db.annotations.delete_one({"_id": annotation_id}, session=session)

        # Check if this was the last annotation for the image
        annotations_count = self.db.annotations.count_documents(
            {"fileId": annotation["fileId"]}, session=session
        )

        if annotations_count == 0:
            # Update image status
            self.db.files.update_one(
                {"_id": annotation["fileId"]},
                {"$set": {"metadata.status": models.FileStatus.UNANNOTATED.value}},
                session=session,
            )

        return result.deleted_count > 0
