from __future__ import annotations

import logging

import pymongo
from pymongo import MongoClient

from DataAPI.models import CRUD, Permission, Role

ROLES = [
    Role(
        name="admin",
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
    Role(
        name="project_manager",
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
    Role(
        name="annotator",
        permissions=[
            Permission(resource="projects", actions=[CRUD.READ]),
            Permission(
                resource="annotations",
                actions=[CRUD.CREATE, CRUD.READ, CRUD.UPDATE],
            ),
        ],
        description="Annotator with annotation capabilities",
    ),
    Role(
        name="reviewer",
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
            logging.info("MongoDB connection established successfully")
        except Exception as e:
            logging.error(f"MongoDB connection failed: {str(e)}")
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
        self.db.annotations.create_index("imageId")
        self.db.annotations.create_index(
            [("projectId", pymongo.ASCENDING), ("type", pymongo.ASCENDING)]
        )
        self.db.annotations.create_index(
            [("imageId", pymongo.ASCENDING), ("label", pymongo.ASCENDING)]
        )

    def initialize_roles(self):
        """Initialize default roles if they don't exist"""

        for role in ROLES:
            existing_role = self.db.roles.find_one({"name": role.name})
            if not existing_role:
                # the mode="json" ensures the Action enums are converted to normal strings
                self.db.roles.insert_one(role.model_dump(mode="json"))
                print(f"Created role: {role.name}")
