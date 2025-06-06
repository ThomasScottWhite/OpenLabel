import datetime
from typing import Any, Mapping

import bcrypt
from bson.objectid import ObjectId

from .. import auth_utils, models
from ..exceptions import (
    EmailAlreadyExists,
    InvalidPatchMap,
    ResourceNotFound,
    RoleNotFound,
    UserAlreadyExists,
)
from .db_manager import MongoDBManager


class UserManager:
    """User management for OpenLabel"""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize with database manager"""
        self.db = db_manager.db

    def _get_role_id_by_name(self, role_name: str) -> ObjectId | None:
        """Returns the ID of the role with name `role_name` if it exists, else `None`

        Args:
            role_name: The name of the role for which to fetch the ID.
        """
        # TODO: replace with new role tech when its created
        role = self.db.roles.find_one({"name": role_name})
        if not role:
            return None

        return role["_id"]

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role_name: str = "annotator",
    ) -> str:
        """Creates a new user.

        Args:
            username: The username of the new user. Must be unique from other users.
            email: The email of the new user. Must be unique from other users.
            password: The password of the new user.
            first_name: The first name of the new user.
            last_name: The last name of the new user.
            role_name: The role the user takes globally. Defaults to "annotator".

        Raises:
            UserAlreadyExists: If the provided username is already taken.
            EmailAlreadyExists: If the provided email is already in use.
            RoleNotFound: If the provided role is invalid.

        Returns:
            An auth token equivalent to if the user logged in.
        """
        # TODO: consider making custom errors for better communication with routes
        # Check if username or email already exists
        if self.db.users.find_one({"username": username}):
            raise UserAlreadyExists(f"Username '{username}' already exists")

        if self.db.users.find_one({"email": email}):
            raise EmailAlreadyExists(f"Email '{email}' already exists")

        role_id = self._get_role_id_by_name(role_name)
        if role_id is None:
            raise RoleNotFound(f"Role '{role_name}' does not exist")

        # Hash the password
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        user = models.User(
            username=username,
            email=email,
            password=hashed_pw,
            firstName=first_name,
            lastName=last_name,
            roleId=role_id,
            isActive=True,
            lastLogin=datetime.datetime.now(datetime.timezone.utc),
        )

        result = self.db.users.insert_one(user.model_dump())

        self.create_default_preferences(result.inserted_id)

        # we don't need to check password, so just generate auth token immediately
        return auth_utils.generate_token(str(result.inserted_id))

    def login(self, username: str, password: str) -> str | None:
        """Authenticates the user and returns an auth token if successful."""
        user = self.db.users.find_one({"username": username})
        if not user:
            return None

        if bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            self.db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"lastLogin": datetime.datetime.now(datetime.timezone.utc)}},
            )
            token = auth_utils.generate_token(user["_id"])

            return token
            # return {
            #     "token": token,
            #     "user_id": str(user["_id"]),
            #     "username": user["username"]
            # }
        return None

    def get_user_by_id(self, user_id: ObjectId) -> dict | None:
        """Returns a single user object matching the provided ID, or `None` if the user does not exist

        Args:
            user_id: The user ID of the user to fetch.
        """
        return self.db.users.find_one({"_id": user_id})

    def get_user_by_username(self, username: str) -> dict | None:
        """Returns a single user object matching the provided username, or `None` if the user does not exist

        Args:
            username: The username of the user to fetch.
        """
        return self.db.users.find_one({"username": username})

    def get_users(self, limit: int = 100) -> list[dict]:
        """Returns a list of users matching the provided search criteria.

        Args:
            limit: The maximum number of users to return. Defaults to 100.
        """
        return list(self.db.users.find().limit(limit))

    def update_user(self, user_id: ObjectId, update_data: Mapping[str, Any]) -> bool:
        """Updates a user based on the provided update_data. Updates are partial,
        merely overriding the keys provided.

        Args:
            user_id: The user ID of the user to update.
            update_data: A mapping containing the fields to update and their new values.
                Must match the naming used within the database. The only exception is that
                `role_name` can be used to change roles rather than specifing a role ID.

        Raises:
            InvalidPatchMap: If invalid keys are provided.
            UserAlreadyExists: When changing username, raises if the new username is already taken.
            EmailAlreadyExists: When changing email, raises if the new email is already being used.
            RoleNotFound: When changing role, raises if the provided `role_name` is invalid.

        Returns:
            True if the user was updated, else False.
        """

        invalid_keys = set(update_data.keys()) - (
            set(models.User.model_fields.keys()) | {"role_name"}
        )
        if invalid_keys:
            raise InvalidPatchMap(f"Invalid user keys: {', '.join(invalid_keys)}")

        # Don't allow updating username or email to existing values
        if "username" in update_data:
            existing = self.db.users.find_one(
                {"username": update_data["username"], "_id": {"$ne": user_id}}
            )
            if existing:
                raise UserAlreadyExists(
                    f"Username '{update_data['username']}' already exists"
                )

        if "email" in update_data:
            existing = self.db.users.find_one(
                {"email": update_data["email"], "_id": {"$ne": user_id}}
            )
            if existing:
                raise EmailAlreadyExists(
                    f"Email '{update_data['email']}' already exists"
                )

        # Hash password if it's being updated
        if "password" in update_data:
            update_data["password"] = bcrypt.hashpw(
                update_data["password"].encode("utf-8"), bcrypt.gensalt()
            )

        # Update role if specified by name
        if "role_name" in update_data:
            role_name = update_data.pop("role_name")
            role_id = self._get_role_id_by_name(role_name)

            if role_id is None:
                raise RoleNotFound(f"Role '{role_name}' does not exist")

            update_data["roleId"] = role_id

        result = self.db.users.update_one({"_id": user_id}, {"$set": update_data})

        return result.modified_count > 0

    def create_default_preferences(self, user_id: ObjectId) -> ObjectId:
        """Sets the default preferences for a user.

        Args:
            user_id: The user to assign default preferences to.

        Returns:
            The ID of the created preferences.
        """
        preferences = models.UserPreferences(
            userId=user_id,
            keyboardShortcuts=models.KeyboardShortcuts(),
            uiPreferences=models.UIPreferences(),
        )
        preferences = dict(preferences)
        for key in ("keyboardShortcuts", "uiPreferences"):
            preferences[key] = dict(preferences[key])

        result = self.db.userPreferences.insert_one(preferences)
        return result.inserted_id

    def get_user_preferences(self, user_id: ObjectId) -> dict | None:
        """Returns the preferences for user with ID `user_id`, or None if no
        such preferences exist.

        Args:
            user_id: The user ID of the user to fetch preferences for.
        """
        return self.db.userPreferences.find_one({"userId": user_id})

    def update_user_preferences(
        self, user_id: ObjectId, preferences: Mapping[str, Any]
    ) -> bool:
        """Updates the user preferences of a user.

        Args:
            user_id: The user ID of the user whose preferences you wish to modify.
            preferences: The new preferences (partial update).

        Raises:
            ValueError: If there are no preferences associated with `user_id`.

        Returns:
            True if the preferences were updated, else False.
        """
        old: dict = self.db.userPreferences.find_one({"userId": user_id})

        if not old:
            raise ResourceNotFound(f"User {user_id} does not have preferences.")

        # ensure that no new, unexpected properties are added
        for preference, model in (
            ("keyboardShortcuts", models.KeyboardShortcuts),
            ("uiPreferences", models.UIPreferences),
        ):
            if preference not in preferences:
                continue

            for key, value in preferences[preference].items():
                if key in model.model_fields.keys():
                    old[preference][key] = value

            # error will be thrown if validation fails
            model(**old[preference])

        result = self.db.userPreferences.update_one({"userId": user_id}, {"$set": old})
        return result.modified_count > 0
