import datetime

from bson.objectid import ObjectId

from .. import exceptions as exc
from .. import models
from .db_manager import MongoDBManager


class ProjectManager:
    """Project management for OpenLabel"""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize with database manager"""
        self.db = db_manager.db
        self.man = db_manager

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
        """Creates a new annotation project.

        Args:
            name: The name of the project. Must be unique to projects created by `created_by`.
            description: The description of the project.
            data_type: The data type used by the project.
            annotation_type: The type of annotations used by the project.
            created_by: The ID of the user creating the project.
            labels: A list of categories/labels.
            is_public: Whether the project will be publically visible. Defaults to False.

        Raises:
            exc.ProjectNameExists: If the provided `name` is already being used by the creating user.

        Returns:
            The ID of the created project.
        """
        # Check if project name already exists for this user
        existing = self.db.projects.find_one({"name": name, "createdBy": created_by})

        if existing:
            raise exc.ProjectNameExists(
                f"Project '{name}' already exists for this user"
            )

        project_doc = models.BaseProject(
            name=name,
            description=description,
            createdBy=created_by,
            members=[
                models.ProjectMember(
                    userId=created_by,
                    roleId=self.man.get_role_by_name(models.RoleName.ADMIN).roleId,
                ),
            ],
            settings=models.ProjectSettings(
                dataType=data_type,
                annotatationType=annotation_type,
                isPublic=is_public,
                labels=labels,
            ),
        )

        result = self.db.projects.insert_one(project_doc.model_dump())
        return result.inserted_id

    def get_project_by_id(self, project_id: ObjectId) -> models.Project | None:
        """Returns the specified project, or None if the project doesn't exist.

        Args:
            project_id: The ID of the project to fetch.
        """
        project = self.db.projects.find_one({"_id": project_id})
        if project is None:
            return None

        return models.Project.model_validate(project)

    def get_projects_by_user(self, user_id: ObjectId) -> list[models.Project]:
        """Fetches all project in which the specified user is a member.

        Args:
            user_id: The ID of the user in question.
        """
        projects = self.db.projects.find({"members.userId": user_id})
        return [models.Project.model_validate(project) for project in projects]

    def update_project(
        self, project_id: ObjectId, update_data: dict, user_id: ObjectId
    ) -> bool:
        """Update project information if user has permission

        Args:
            project_id: The ID of the project to update.
            update_data: A Mapping containing the fields to update.
            user_id: The ID of the user attemping to update the project.

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
        # TODO: revamp permissions
        # has_permission = False
        # for member in project.members:
        #     if member.userId == user_id:
        #         role = self.man.get_role_by_id(member.roleId)
        #         if role and role.name in [
        #             models.RoleName.ADMIN,
        #             models.RoleName.PROJECT_MANAGER,
        #         ]:
        #             has_permission = True
        #             break

        # if not has_permission:
        #     raise exc.PermissionError(
        #         "User does not have permission to update this project"
        #     )

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
        # TODO: revamp permissions
        # has_permission = False
        # for member in project["members"]:
        #     if member["userId"] == added_by:
        #         role = self.db.roles.find_one({"_id": member["roleId"]})
        #         if role and role["name"] in ["admin", "project_manager"]:
        #             has_permission = (
        #                 role_name == models.RoleName.ADMIN
        #                 and role["name"] == models.RoleName.ADMIN
        #             ) or role_name != models.RoleName.ADMIN
        #             break

        # if not has_permission:
        #     raise exc.PermissionError("User does not have permission to add members")

        # Check if user already a member
        for member in project["members"]:
            if member["userId"] == user_id:
                raise exc.UserAlreadyExists("User is already a member of this project")

        # Get role ID
        role = self.man.get_role_by_name(role_name)
        if not role:
            raise exc.RoleNotFound(f"Role '{role_name}' does not exist")

        # Add user to project
        result = self.db.projects.update_one(
            {"_id": project_id},
            {
                "$push": {
                    "members": {
                        "userId": user_id,
                        "roleId": role.roleId,
                        "joinedAt": datetime.datetime.now(datetime.timezone.utc),
                    }
                }
            },
        )

        return result.modified_count > 0

    def get_project_members(
        self, project_id: ObjectId
    ) -> list[models.ProjectMemberDetails]:
        """Returns the members of a project with additional details about the user and their role.

        Args:
            project_id: The ID of the project for which to fetch members.

        Raises:
            exc.ResourceNotFound: If the specified project does not exist.
        """
        project = self.get_project_by_id(project_id)

        if not project:
            raise exc.ResourceNotFound("Project not found")

        members: list[models.ProjectMemberDetails] = []
        for member in project.members:
            user = self.db.users.find_one({"_id": member.userId})
            role = self.db.roles.find_one({"_id": member.roleId})

            if user and role:
                members.append(
                    models.ProjectMemberDetails(
                        joinedAt=member.joinedAt,
                        user=models.UserNoPasswordWithID.model_validate(user),
                        role=models.Role.model_validate(role),
                    )
                )

        return members

    def get_all_projects(self) -> list[models.Project]:
        """Returns all projects."""
        projects = self.db.projects.find()
        return [models.Project.model_validate(project) for project in projects]
