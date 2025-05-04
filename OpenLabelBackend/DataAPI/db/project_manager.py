import datetime
from typing import Any

from bson.objectid import ObjectId

from .. import exceptions as exc
from .. import models
from .db_manager import MongoDBManager


class ProjectManager:
    """Project management for OpenLabel"""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize with database manager"""
        self.db = db_manager.db

    def create_project(
        self,
        name: str,
        description: str,
        data_type: models.DataType,
        annotation_type: models.AnnotationType,
        created_by: ObjectId,
        labels: list[str],
        is_public: bool = False,
    ) -> ObjectId:
        """Create a new project"""
        # Check if project name already exists for this user
        existing = self.db.projects.find_one({"name": name, "createdBy": created_by})

        if existing:
            raise exc.ProjectNameExists(
                f"Project '{name}' already exists for this user"
            )

        project_doc = models.Project(
            projectId=ObjectId(),
            name=name,
            description=description,
            createdBy=created_by,
            members=[
                models.ProjectMember(
                    userId=created_by,
                    roleId=self.db.roles.find_one({"name": "admin"})["_id"],
                ),
            ],
            settings=models.ProjectSettings(
                dataType=data_type,
                annotatationType=annotation_type,
                isPublic=is_public,
                labels=labels,
            ),
        )

        result = self.db.projects.insert_one(
            project_doc.model_dump(exclude=["projectId"])
        )
        return result.inserted_id

    def get_project_by_id(self, project_id: ObjectId) -> models.Project | None:
        """Get project by ID"""
        project = self.db.projects.find_one({"_id": project_id})
        if project is None:
            return None

        return models.Project.model_validate(project)

    def get_projects_by_user(self, user_id: ObjectId) -> list[models.Project]:
        """Get projects where user is a member"""
        projects = self.db.projects.find({"members.userId": user_id})
        return [models.Project.model_validate(project) for project in projects]

    def update_project(
        self, project_id: ObjectId, update_data: dict, user_id: ObjectId
    ) -> bool:
        """Update project information if user has permission

        Args:
            project_id: _description_
            update_data: _description_
            user_id: _description_

        Raises:
            ResourceNotFound: If the project was not found.
            InvalidPatchMap: If `update_data` was invalid.
            PermissionError: If the user provided does not have permission to update the project.
            ProjectNameExists: If the user attempts to update the project name to an existing project name.

        Returns:
            True if something was modified, False otherwise.
        """
        project = self.get_project_by_id(project_id)

        if not project:
            raise exc.ResourceNotFound("Project not found")

        valid_keys = {"name", "description", "settings"}
        invalid_keys = set(update_data.keys()) - valid_keys
        if invalid_keys:
            raise exc.InvalidPatchMap(
                f"Keys {''.join(invalid_keys)} are not valid keys for updating projects!"
            )

        # Check if user is a member with admin or project_manager role
        has_permission = False
        for member in project.members:
            if member.userId == user_id:
                role = self.db.roles.find_one({"_id": member.roleId})
                if role and role["name"] in ["admin", "project_manager"]:
                    has_permission = True
                    break

        if not has_permission:
            raise exc.PermissionError(
                "User does not have permission to update this project"
            )

        # Update settings if provided
        if "settings" in update_data:
            update_data["settings"] = {
                **project.settings.model_dump(),
                **update_data["settings"],
            }

            # ensure validity of changes
            models.ProjectSettings.model_validate(update_data["settings"])

        # Don't allow updating name to an existing name
        if "name" in update_data:
            existing = self.db.projects.find_one(
                {
                    "name": update_data["name"],
                    "createdBy": project.createdBy,
                    "_id": {"$ne": project_id},
                }
            )
            if existing:
                raise exc.ProjectNameExists(
                    f"Project name '{update_data['name']}' already exists"
                )

        # Always update the updatedAt field
        update_data["updatedAt"] = datetime.datetime.now(datetime.timezone.utc)

        result = self.db.projects.update_one({"_id": project_id}, {"$set": update_data})

        return result.modified_count > 0

    def add_project_member(
        self,
        project_id: ObjectId,
        user_id: ObjectId,
        role_name: str,
        added_by: ObjectId,
    ) -> bool:
        """Add a user to a project with specified role

        Args:
            project_id: The project to add the user to.
            user_id: The ID of the user to add to the project.
            role_name: The role to assign to the new member.
            added_by: The user adding the member to the project.

        Raises:
            ResourceNotFound: If the project does not exist.
            PermissionError: If the `added_by` user does not have permission to add members.
            UserAlreadyExists: If the provided user was already added to the project.
            RoleNotFound: If the specified role does not exist.

        Returns:
            _description_
        """
        project = self.get_project_by_id(project_id)

        if not project:
            raise exc.ResourceNotFound("Project not found")

        # Check if the adding user has permission
        has_permission = False
        for member in project["members"]:
            if member["userId"] == added_by:
                role = self.db.roles.find_one({"_id": member["roleId"]})
                if role and role["name"] in ["admin", "project_manager"]:
                    has_permission = (
                        role_name == models.RoleName.ADMIN
                        and role["name"] == models.RoleName.ADMIN
                    ) or role_name != models.RoleName.ADMIN
                    break

        if not has_permission:
            raise exc.PermissionError("User does not have permission to add members")

        # Check if user already a member
        for member in project["members"]:
            if member["userId"] == user_id:
                raise exc.UserAlreadyExists("User is already a member of this project")

        # Get role ID
        role = self.db.roles.find_one({"name": role_name})
        if not role:
            raise exc.RoleNotFound(f"Role '{role_name}' does not exist")

        # Add user to project
        result = self.db.projects.update_one(
            {"_id": project_id},
            {
                "$push": {
                    "members": {
                        "userId": user_id,
                        "roleId": role["_id"],
                        "joinedAt": datetime.datetime.now(datetime.timezone.utc),
                    }
                }
            },
        )

        return result.modified_count > 0

    def get_project_members(self, project_id: ObjectId) -> list[dict]:
        """Get all members of a project with their roles"""
        project = self.get_project_by_id(project_id)

        if not project:
            raise exc.ResourceNotFound("Project not found")

        members = []
        for member in project["members"]:
            user = self.db.users.find_one({"_id": member["userId"]})
            role = self.db.roles.find_one({"_id": member["roleId"]})

            if user and role:
                members.append(
                    {
                        "user": user,
                        "role": role,
                        "joinedAt": member["joinedAt"],
                    }
                )

        return members

    def get_all_projects(self) -> list[models.Project]:
        """Get all projects"""
        projects = self.db.projects.find()
        return [models.Project.model_validate(project) for project in projects]

    def initalize_default_projects(self):
        """Initialize default projects"""

        default_admin = self.db.users.find_one({"username": "admin"})
        if not default_admin:
            raise ValueError("Admin user not found")

        admin_id = default_admin["_id"]
        try:
            self.create_project(
                name="Default Project 1",
                description="This is a default project for image object-detection.",
                created_by=admin_id,
                is_public=True,
                data_type="image",
                annotation_type="object-detection",
            )
        except:
            pass
        try:
            self.create_project(
                name="Default Project 2",
                description="This is a default project for text classification.",
                created_by=admin_id,
                is_public=True,
                data_type="text",
                annotation_type="classification",
            )
        except:
            pass
        try:
            self.create_project(
                name="Default Project 3",
                description="This is a default project for image classification.",
                created_by=admin_id,
                is_public=True,
                data_type="image",
                annotation_type="classification",
            )
        except:
            pass
