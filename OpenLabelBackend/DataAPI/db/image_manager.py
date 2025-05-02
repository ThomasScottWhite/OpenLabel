from io import BytesIO
from typing import BinaryIO

import gridfs
import gridfs.errors
from bson.objectid import ObjectId

from .. import exceptions as exc
from .. import models
from . import _utils as utils
from .db_manager import MongoDBManager


class ImageManager:
    """Annotation management for OpenLabel"""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize with database manager"""
        self.db = db_manager.db
        self.fs = gridfs.GridFSBucket(self.db, "images")

    def upload_image(
        self,
        file: BinaryIO,
        project_id: ObjectId,
        creator_id: ObjectId,
        filename: str,
        width: int,
        height: int,
        content_type: str,
        status: models.ImageStatus = models.ImageStatus.UNPROCESSED,
    ):
        utils.project_exists(self.db, project_id, True)
        utils.user_exists(self.db, creator_id, True)

        meta = dict(
            projectId=project_id,
            createdBy=creator_id,
            filename=filename,
            width=width,
            height=height,
            contentType=content_type,
            status=status,
        )

        with self.fs.open_upload_stream(filename, metadata=meta) as grid_in:
            grid_in.write(file.read())
            file_id = grid_in._id

        return models.ImageMeta(**meta, imageId=file_id)

    def download_image(
        self, image_id: ObjectId
    ) -> tuple[BytesIO, models.ImageMeta] | None:

        details: gridfs.GridOut | None = None
        for thing in self.fs.find({"_id": image_id}).limit(-1):
            details = thing

        if details is None:
            return None

        buffer = BytesIO()
        self.fs.download_to_stream(image_id, buffer)

        return buffer, models.ImageMeta.from_grid_out(details)

    def get_image_by_id(self, image_id: ObjectId) -> models.ImageMeta | None:
        for details in self.fs.find({"_id": image_id}).limit(-1):
            return models.ImageMeta.from_grid_out(details)
        return None

    def get_images_by_project(
        self, project_id: ObjectId, limit: int = 0
    ) -> list[models.ImageMeta]:

        utils.project_exists(self.db, project_id, True)

        metas: list[models.ImageMeta] = []

        for details in self.fs.find({"metadata.projectId": project_id}).limit(limit):
            metas.append(models.ImageMeta.from_grid_out(details))

        return metas

    def delete_image(self, image_id: ObjectId):

        try:
            self.fs.delete(image_id)
            # TODO: also have to delete associated annotations
        except gridfs.errors.NoFile:
            raise exc.ResourceNotFound(
                f"Could not delete image with ID '{str(image_id)}' because it does not exist."
            )
