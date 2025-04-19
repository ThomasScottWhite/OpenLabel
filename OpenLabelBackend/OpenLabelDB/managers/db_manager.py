import pymongo
from pymongo import MongoClient
import logging
from typing import Dict, List, Optional, Any
from bson.objectid import ObjectId

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
        self.db.images.create_index([("projectId", pymongo.ASCENDING), 
                                     ("status", pymongo.ASCENDING)])
        
        # Annotations collection indexes
        self.db.annotations.create_index("imageId")
        self.db.annotations.create_index([("projectId", pymongo.ASCENDING), 
                                         ("type", pymongo.ASCENDING)])
        self.db.annotations.create_index([("imageId", pymongo.ASCENDING), 
                                         ("label", pymongo.ASCENDING)])
    
    def initialize_roles(self):
        """Initialize default roles if they don't exist"""
        roles = [
            {
                "name": "admin",
                "permissions": [
                    {"resource": "users", "actions": ["create", "read", "update", "delete"]},
                    {"resource": "projects", "actions": ["create", "read", "update", "delete"]},
                    {"resource": "annotations", "actions": ["create", "read", "update", "delete"]}
                ],
                "description": "Administrator with full access"
            },
            {
                "name": "project_manager",
                "permissions": [
                    {"resource": "users", "actions": ["read"]},
                    {"resource": "projects", "actions": ["create", "read", "update"]},
                    {"resource": "annotations", "actions": ["read", "update"]}
                ],
                "description": "Project manager with project creation and management capabilities"
            },
            {
                "name": "annotator",
                "permissions": [
                    {"resource": "projects", "actions": ["read"]},
                    {"resource": "annotations", "actions": ["create", "read", "update"]}
                ],
                "description": "Annotator with annotation capabilities"
            },
            {
                "name": "reviewer",
                "permissions": [
                    {"resource": "projects", "actions": ["read"]},
                    {"resource": "annotations", "actions": ["read", "update"]}
                ],
                "description": "Reviewer with annotation review capabilities"
            }
        ]
        
        for role in roles:
            existing_role = self.db.roles.find_one({"name": role["name"]})
            if not existing_role:
                self.db.roles.insert_one(role)
                print(f"Created role: {role['name']}")