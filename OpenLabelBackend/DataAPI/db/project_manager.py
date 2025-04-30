import datetime
from typing import Dict, List, Optional

from bson.objectid import ObjectId


class ProjectManager:
    """Project management for OpenLabel"""

    def __init__(self, db_manager):
        """Initialize with database manager"""
        self.db = db_manager.db
        self.initalize_default_projects()

    # Current supported annotation types
    # export interface AnnotatorLayout {
    #   type: "image" | "text" ;
    #   layout: "classification" | "object-detection"| string;
    #   labels: string[];
    # }
    def create_project(
        self,
        name: str,
        description: str,
        data_type: str,
        annotation_type: str,
        created_by: ObjectId,
        is_public: bool = False,
    ) -> ObjectId:
        """Create a new project"""
        # Check if project name already exists for this user
        existing = self.db.projects.find_one({"name": name, "createdBy": created_by})

        if existing:
            raise ValueError(f"Project '{name}' already exists for this user")


        project_doc = {
            "name": name,
            "description": description,
            "createdBy": created_by,
            "createdAt": datetime.datetime.utcnow(),
            "updatedAt": datetime.datetime.utcnow(),
            "members": [
                {
                    "userId": created_by,
                    # Admin role for creator
                    "roleId": self.db.roles.find_one({"name": "admin"})["_id"],
                    "joinedAt": datetime.datetime.utcnow(),
                }
            ],
            "settings": {
                "data_type": data_type,
                "annotation_type": annotation_type,
                "isPublic": is_public,
            },
        }

        result = self.db.projects.insert_one(project_doc)
        return result.inserted_id

    def get_project_by_id(self, project_id: ObjectId) -> Optional[Dict]:
        """Get project by ID"""
        return self.db.projects.find_one({"_id": project_id})

    def get_projects_by_user(self, user_id: ObjectId) -> List[Dict]:
        """Get projects where user is a member"""
        return list(self.db.projects.find({"members.userId": user_id}))

    def update_project(
        self, project_id: ObjectId, update_data: Dict, user_id: ObjectId
    ) -> bool:
        """Update project information if user has permission"""
        project = self.get_project_by_id(project_id)

        if not project:
            raise ValueError("Project not found")

        # Check if user is a member with admin or project_manager role
        has_permission = False
        for member in project["members"]:
            if member["userId"] == user_id:
                role = self.db.roles.find_one({"_id": member["roleId"]})
                if role and role["name"] in ["admin", "project_manager"]:
                    has_permission = True
                    break

        if not has_permission:
            raise ValueError("User does not have permission to update this project")

        # Don't allow updating name to an existing name
        if "name" in update_data:
            existing = self.db.projects.find_one(
                {
                    "name": update_data["name"],
                    "createdBy": project["createdBy"],
                    "_id": {"$ne": project_id},
                }
            )
            if existing:
                raise ValueError(f"Project name '{update_data['name']}' already exists")

        # Update settings if provided
        if "settings" in update_data:
            update_data["settings"] = {**project["settings"], **update_data["settings"]}

        # Always update the updatedAt field
        update_data["updatedAt"] = datetime.datetime.utcnow()

        result = self.db.projects.update_one({"_id": project_id}, {"$set": update_data})

        return result.modified_count > 0

    def add_project_member(
        self,
        project_id: ObjectId,
        user_id: ObjectId,
        role_name: str,
        added_by: ObjectId,
    ) -> bool:
        """Add a user to a project with specified role"""
        project = self.get_project_by_id(project_id)

        if not project:
            raise ValueError("Project not found")

        # Check if the adding user has permission
        has_permission = False
        for member in project["members"]:
            if member["userId"] == added_by:
                role = self.db.roles.find_one({"_id": member["roleId"]})
                if role and role["name"] in ["admin", "project_manager"]:
                    has_permission = True
                    break

        if not has_permission:
            raise ValueError("User does not have permission to add members")

        # Check if user already a member
        for member in project["members"]:
            if member["userId"] == user_id:
                raise ValueError("User is already a member of this project")

        # Get role ID
        role = self.db.roles.find_one({"name": role_name})
        if not role:
            raise ValueError(f"Role '{role_name}' does not exist")

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

    def get_project_members(self, project_id: ObjectId) -> List[Dict]:
        """Get all members of a project with their roles"""
        project = self.get_project_by_id(project_id)

        if not project:
            raise ValueError("Project not found")

        members = []
        for member in project["members"]:
            user = self.db.users.find_one({"_id": member["userId"]})
            role = self.db.roles.find_one({"_id": member["roleId"]})

            if user and role:
                members.append(
                    {
                        "userId": user["_id"],
                        "username": user["username"],
                        "roleName": role["name"],
                        "joinedAt": member["joinedAt"],
                    }
                )

        return members

    def get_all_projects(self) -> List[Dict]:
        """Get all projects"""
        return list(self.db.projects.find())
    
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

