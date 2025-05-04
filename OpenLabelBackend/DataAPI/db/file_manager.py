from io import BytesIO
from typing import Any, BinaryIO

import gridfs
import gridfs.errors
from bson.objectid import ObjectId
from PIL import Image
from pymongo.client_session import ClientSession

from .. import exceptions as exc
from .. import models
from . import _utils
from .db_manager import MongoDBManager


class FileManager:
    """Annotation management for OpenLabel"""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize with database manager"""
        self.db = db_manager.db
        self.client = db_manager.client
        self.fs = gridfs.GridFSBucket(self.db, "files")

    def upload_file(
        self,
        file: BinaryIO,
        project_id: ObjectId,
        creator_id: ObjectId,
        filename: str,
        content_type: str,
        status: models.FileStatus = models.FileStatus.UNANNOTATED,
        session: ClientSession | None = None,
    ) -> models.FileMeta:
        try:
            file_type = models.DataType.from_mime(content_type)
        except ValueError as e:
            raise exc.InvalidFileFormat(str(e))

        _utils.project_exists(self.db, project_id, True)
        _utils.user_exists(self.db, creator_id, True)

        # get file size
        file.seek(0, 2)
        filesize = file.tell()
        file.seek(0)

        # collected currently known meta
        meta = dict(
            projectId=project_id,
            createdBy=creator_id,
            contentType=content_type,
            type=file_type.value,
            size=filesize,
            status=status,
        )

        # Collect
        if file_type == models.DataType.IMAGE:
            try:
                image = Image.open(file)
                width, height = image.size
                meta["width"] = width
                meta["height"] = height
            except Exception:
                raise exc.InvalidFileFormat("Could not process image")
        elif file_type == models.DataType.VIDEO:
            # TODO: video support
            raise NotImplementedError("Videos have not been implemented yet.")

        # upload the file
        with self.fs.open_upload_stream(
            filename, metadata=meta, session=session
        ) as grid_in:
            grid_in.write(file.read())
            file_id = grid_in._id

        return models.get_filemeta_model(content_type)(
            **meta, fileId=file_id, filename=filename
        )

    def upload_files(self, files: list[dict[str, Any]]) -> list[models.FileMeta]:
        metas: list[models.FileMeta] = []

        with self.client.start_session() as session:
            with session.start_transaction():
                # TODO: batching would be epic here
                # NOTE: we should probably remake everything using the asynchronous stuff eventually
                for file in files:
                    meta = self.upload_file(**file, session=session)
                    metas.append(meta)

        return metas

    def download_file(
        self, file_id: ObjectId
    ) -> tuple[BytesIO, models.FileMeta] | None:

        details: gridfs.GridOut | None = None
        for thing in self.fs.find({"_id": file_id}).limit(-1):
            details = thing

        if details is None:
            return None

        buffer = BytesIO()
        self.fs.download_to_stream(file_id, buffer)

        return (
            buffer,
            models.get_filemeta_model(details.metadata["contentType"]).from_grid_out(
                details
            ),
        )

    def get_file_by_id(self, file_id: ObjectId) -> models.FileMeta | None:
        for details in self.fs.find({"_id": file_id}).limit(-1):
            content_type = details.metadata["contentType"]
            return models.get_filemeta_model(content_type).from_grid_out(details)
        return None

    def get_files_by_project(
        self, project_id: ObjectId, limit: int = 0
    ) -> list[models.FileMeta]:

        _utils.project_exists(self.db, project_id, True)

        metas: list[dict[str, Any]] = []

        for details in self.fs.find({"metadata.projectId": project_id}).limit(limit):

            content_type = details.metadata["contentType"]
            meta = models.get_filemeta_model(content_type).from_grid_out(details)
            metas.append(meta)

        return metas

    def delete_file(self, file_id: ObjectId):

        try:
            self.fs.delete(file_id)
        except gridfs.errors.NoFile:
            raise exc.ResourceNotFound(
                f"Could not delete image with ID '{str(file_id)}' because it does not exist."
            )

        self.db.annotations.delete_many({"fileId": file_id})
