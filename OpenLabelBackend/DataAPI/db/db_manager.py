from __future__ import annotations

import logging
from typing import Any

import pymongo
from bson.objectid import ObjectId
from DataAPI.models import CRUD, BaseRole, Permission, Role, RoleName
from pymongo import MongoClient

logger = logging.getLogger(__name__)

ROLES = [
    BaseRole(
        name=RoleName.ADMIN,
        permissions=[
            Permission(
                resource="users",
                actions=[CRUD.CREATE, CRUD.READ, CRUD.UPDATE, CRUD.DELETE],
            ),
            Permission(
                resource="projects",
                actions=[CRUD.CREATE, CRUD.READ, CRUD.UPDATE, CRUD.DELETE],
            ),
            Permission(
                resource="annotations",
                actions=[CRUD.CREATE, CRUD.READ, CRUD.UPDATE, CRUD.DELETE],
            ),
        ],
        description="Administrator with full access",
    ),
    BaseRole(
        name=RoleName.PROJECT_MANAGER,
        permissions=[
            Permission(resource="users", actions=[CRUD.READ]),
            Permission(
                resource="projects", actions=[CRUD.CREATE, CRUD.READ, CRUD.UPDATE]
            ),
            Permission(
                resource="annotations",
                actions=[CRUD.READ, CRUD.UPDATE],
            ),
        ],
        description="Project manager with project creation and management capabilities",
    ),
    BaseRole(
        name=RoleName.ANNOTATOR,
        permissions=[
            Permission(resource="projects", actions=[CRUD.READ]),
            Permission(
                resource="annotations",
                actions=[CRUD.CREATE, CRUD.READ, CRUD.UPDATE],
            ),
        ],
        description="Annotator with annotation capabilities",
    ),
    BaseRole(
        name=RoleName.REVIEWER,
        permissions=[
            Permission(resource="projects", actions=[CRUD.READ]),
            Permission(
                resource="annotations",
                actions=[CRUD.READ, CRUD.UPDATE],
            ),
        ],
        description="Reviewer with annotation review capabilities",
    ),
]


class MongoDBManager:
    """MongoDB database manager for OpenLabel"""

    def __init__(self, connection_uri: str, database_name: str = "openlabel_db"):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(connection_uri)
            self.db = self.client[database_name]
            # Create indexes for collections
            self._create_indexes()
            logger.info("MongoDB connection established successfully")
        except Exception as e:
            logger.exception(f"MongoDB connection failed: {str(e)}")
            raise

    def _create_indexes(self):
        """Create necessary indexes for performance optimization"""
        # Users collection indexes
        self.db.users.create_index("username", unique=True)
        self.db.users.create_index("email", unique=True)

        # Projects collection indexes
        self.db.projects.create_index("name")
        self.db.projects.create_index("createdBy")
        self.db.projects.create_index([("members.userId", pymongo.ASCENDING)])

        # Images collection indexes
        self.db.images.create_index("projectId")
        self.db.images.create_index(
            [("projectId", pymongo.ASCENDING), ("status", pymongo.ASCENDING)]
        )

        # Annotations collection indexes
        self.db.annotations.create_index("fileId")
        self.db.annotations.create_index(
            [("projectId", pymongo.ASCENDING), ("type", pymongo.ASCENDING)]
        )
        self.db.annotations.create_index(
            [("fileId", pymongo.ASCENDING), ("label", pymongo.ASCENDING)]
        )

    def initialize_roles(self):
        """Initialize default roles if they don't exist"""

        for role in ROLES:
            existing_role = self.db.roles.find_one({"name": role.name})
            if not existing_role:
                # the mode="json" ensures the Action enums are converted to normal strings
                self.db.roles.insert_one(role.model_dump(mode="json"))
                print(f"Created role: {role.name}")

    def get_roles(self) -> list[Role]:
        """Returns all initiatlized roles."""

        roles = self.db.roles.find({})

        return [Role.model_validate(role) for role in roles]

    @staticmethod
    def _convert_to_role_model(raw_role: dict[str, Any] | None) -> Role | None:
        """Converts a raw role result taken from the db.roles collection into the Role
        pydantic model, or None, if the input role was None.

        Args:
            raw_role: A single document from the db.roles collection.

        Returns:
            The converted role, or None if that was the input.
        """
        if raw_role is None:
            return None

        # rename _id key to what Role expects
        raw_role["roleId"] = raw_role.pop("_id")

        return Role.model_validate(raw_role)

    def get_role_by_id(self, role_id: ObjectId) -> Role | None:
        """Returns a single Role by its ID, or None if the role does not exist.

        Args:
            role_id: The ID of the role to fetch.
        """
        role = self.db.roles.find_one({"_id": role_id})
        return self._convert_to_role_model(role)

    def get_role_by_name(self, role_name: RoleName) -> Role | None:
        """Returns a single Role by its name, or None if the role does not exist.

        Args:
            role_id: The ID of the role to fetch.
        """
        role = self.db.roles.find_one({"name": role_name})
        return self._convert_to_role_model(role)
