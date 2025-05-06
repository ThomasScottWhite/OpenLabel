"""
MongoDB managers for OpenLabel project.

This package contains the database managers for the OpenLabel project,
providing database operations for users, projects, annotations, and exports.
"""

from typing import Final

from DataAPI.config import CONFIG

from .annotation_manager import AnnotationManager
from .db_manager import MongoDBManager
from .export_manager import ExportManager
from .file_manager import FileManager
from .project_manager import ProjectManager
from .user_manager import UserManager

manager: Final[MongoDBManager] = MongoDBManager(CONFIG.mongo_uri, CONFIG.database_name)
manager.initialize_roles()

file: Final[FileManager] = FileManager(manager)
annotation: Final[AnnotationManager] = AnnotationManager(manager, file)
export: Final[ExportManager] = ExportManager(manager, file, annotation)
project: Final[ProjectManager] = ProjectManager(manager)
user: Final[UserManager] = UserManager(manager)

__all__ = [
    "MongoDBManager",
    "UserManager",
    "ProjectManager",
    "AnnotationManager",
    "ExportManager",
]
