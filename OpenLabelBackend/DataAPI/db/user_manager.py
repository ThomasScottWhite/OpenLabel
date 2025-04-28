import datetime
from typing import Any, Dict, List, Optional

import bcrypt
from bson.objectid import ObjectId


class UserManager:
    """User management for OpenLabel"""

    def __init__(self, db_manager):
        """Initialize with database manager"""
        self.db = db_manager.db

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role_name: str = "annotator",
    ) -> ObjectId:
        """Create a new user"""
        # Check if username or email already exists
        if self.db.users.find_one({"username": username}):
            raise ValueError(f"Username '{username}' already exists")

        if self.db.users.find_one({"email": email}):
            raise ValueError(f"Email '{email}' already exists")

        # Get role ID
        role = self.db.roles.find_one({"name": role_name})
        if not role:
            raise ValueError(f"Role '{role_name}' does not exist")

        # Hash the password
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        user_doc = {
            "username": username,
            "email": email,
            "password": hashed_pw,
            "firstName": first_name,
            "lastName": last_name,
            "roleId": role["_id"],
            "createdAt": datetime.datetime.now(datetime.timezone.utc),
            "lastLogin": None,
            "isActive": True,
        }

        result = self.db.users.insert_one(user_doc)

        # Create default user preferences
        self.create_default_preferences(result.inserted_id)

        return result.inserted_id

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user with username and password"""
        user = self.db.users.find_one({"username": username})
        if not user:
            return None

        if bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            # Update last login time
            self.db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"lastLogin": datetime.datetime.now(datetime.timezone.utc)}},
            )
            return user
        return None

    def get_user_by_id(self, user_id: ObjectId) -> Optional[Dict]:
        """Get user by ID"""
        return self.db.users.find_one({"_id": user_id})

    def get_users(self, limit: int = 100) -> List[Dict]:
        """Get list of users"""
        return list(self.db.users.find().limit(limit))

    def update_user(self, user_id: ObjectId, update_data: Dict) -> bool:
        """Update user information"""
        # Don't allow updating username or email to existing values
        if "username" in update_data:
            existing = self.db.users.find_one(
                {"username": update_data["username"], "_id": {"$ne": user_id}}
            )
            if existing:
                raise ValueError(f"Username '{update_data['username']}' already exists")

        if "email" in update_data:
            existing = self.db.users.find_one(
                {"email": update_data["email"], "_id": {"$ne": user_id}}
            )
            if existing:
                raise ValueError(f"Email '{update_data['email']}' already exists")

        # Hash password if it's being updated
        if "password" in update_data:
            update_data["password"] = bcrypt.hashpw(
                update_data["password"].encode("utf-8"), bcrypt.gensalt()
            )

        # Update role if specified by name
        if "role_name" in update_data:
            role_name = update_data.pop("role_name")
            role = self.db.roles.find_one({"name": role_name})
            if not role:
                raise ValueError(f"Role '{role_name}' does not exist")
            update_data["roleId"] = role["_id"]

        result = self.db.users.update_one({"_id": user_id}, {"$set": update_data})

        return result.modified_count > 0

    def create_default_preferences(self, user_id: ObjectId) -> ObjectId:
        """Create default preferences for a new user"""
        preferences = {
            "userId": user_id,
            "keyboardShortcuts": {
                "createBox": "b",
                "createPolygon": "p",
                "deleteAnnotation": "d",
                "saveAnnotation": "ctrl+s",
                "nextImage": "right",
                "prevImage": "left",
            },
            "uiPreferences": {
                "theme": "light",
                "language": "en",
                "annotationDefaultColor": "#FF0000",
            },
        }

        result = self.db.userPreferences.insert_one(preferences)
        return result.inserted_id

    def get_user_preferences(self, user_id: ObjectId) -> Optional[Dict]:
        """Get user preferences"""
        return self.db.userPreferences.find_one({"userId": user_id})

    def update_user_preferences(self, user_id: ObjectId, preferences: Dict) -> bool:
        """Update user preferences"""
        result = self.db.userPreferences.update_one(
            {"userId": user_id}, {"$set": preferences}
        )
        return result.modified_count > 0
