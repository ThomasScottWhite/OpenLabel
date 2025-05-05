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
        """Uploads a single file to the database.

        Args:
            file: The file to upload.
            project_id: The ID of the project the file belongs to.
            creator_id: The ID of the user that uploaded the file.
            filename: The name of the file.
            content_type: The MIME type of the file.
            status: The status of the file. Defaults to models.FileStatus.UNANNOTATED.
            session: The pymongo ClientSession to use. Defaults to None.

        Raises:
            exc.InvalidFileFormat: If the `content_type` is not supported.
            exc.InvalidFileFormat: If corrupted/malformatted file is provided.

        Returns:
            The resultant metadata for the uploaded file.
        """
        try:
            file_type = models.DataType.from_mime(content_type)
        except ValueError as e:
            raise exc.InvalidFileFormat(str(e))

        _utils.project_exists(self.db, project_id, True, session=session)
        _utils.user_exists(self.db, creator_id, True, session=session)

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
        file.seek(0)  # Ensure reading from beginning
        with self.fs.open_upload_stream(filename, metadata=meta) as grid_in:
            grid_in.write(file.read())
            file_id = grid_in._id

        return models.get_filemeta_model(content_type)(
            **meta, fileId=file_id, filename=filename
        )

    def _upload_files(
        self, files: list[dict[str, Any]], session: ClientSession | None
    ) -> list[models.FileMeta]:
        """Implementation of `upload_files`."""
        metas: list[models.FileMeta] = []

        if session:
            with session.start_transaction():
                for file in files:
                    meta = self.upload_file(**file, session=session)
                    metas.append(meta)
        else:
            for file in files:
                meta = self.upload_file(**file, session=None)
                metas.append(meta)

        return metas

    def upload_files(
        self, files: list[dict[str, Any]], session: ClientSession | None = None
    ) -> list[models.FileMeta]:
        """Uploads multiple files at once.

        Args:
            files: A list of dictionaries with keys and values compatible with the `upload_file` method.
            session: The pymongo ClientSession to use. Defaults to None.

        Returns:
            A list of file metadatas corresponding to the uploaded files.
        """
        return self._upload_files(files, session)


    def download_file(
        self, file_id: ObjectId
    ) -> tuple[BytesIO, models.FileMeta] | None:
        """Downloads a file.

        Args:
            file_id: The ID of the file to download.

        Returns:
            A pair containing (file data, file metadata), or None if the file does not exist.
        """

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

    def get_file_by_id(
        self, file_id: ObjectId, session: ClientSession | None = None
    ) -> models.FileMeta | None:
        """Returns a single file based on its ID, or None if the file does not exist.

        Args:
            file_id: The ID of the file to fetch.
            session: The pymongo ClientSession to use. Only applies to non-file system related queries
                since GridFS does not support sessions.Defaults to None.
        """
        for details in self.fs.find({"_id": file_id}, session=session).limit(-1):
            content_type = details.metadata["contentType"]
            return models.get_filemeta_model(content_type).from_grid_out(details)
        return None

    def get_files_by_project(
        self, project_id: ObjectId, limit: int = 0, session: ClientSession | None = None
    ) -> list[models.FileMeta]:
        """Returns a list of FileMeta associated with a project.

        Args:
            project_id: The ID of the project for which to fetch file metadata.
            limit: The maximum number of metadatas to return. Defaults to 0.
            session: The pymongo ClientSession to use. Only applies to non-file system related queries
                since GridFS does not support sessions.Defaults to None.
        """

        _utils.project_exists(self.db, project_id, True, session=session)

        metas: list[dict[str, Any]] = []

        for details in self.fs.find({"metadata.projectId": project_id}).limit(limit):

            content_type = details.metadata["contentType"]
            meta = models.get_filemeta_model(content_type).from_grid_out(details)
            metas.append(meta)

        return metas

    def delete_file(self, file_id: ObjectId, session: ClientSession | None = None):
        """Deletes the specified file.

        Args:
            file_id: The ID of the file to delete.
            session: The pymongo ClientSession to use. Only applies to non-file system related queries
                since GridFS does not support sessions.Defaults to None.

        Raises:
            exc.ResourceNotFound: If the specified image does not exist.
        """

        try:
            # GridFS does not support multi-document sessions
            self.fs.delete(file_id)
        except gridfs.errors.NoFile:
            raise exc.ResourceNotFound(
                f"Could not delete image with ID '{str(file_id)}' because it does not exist."
            )

        self.db.annotations.delete_many({"fileId": file_id}, session=session)
