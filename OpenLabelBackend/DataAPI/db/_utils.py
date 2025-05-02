from bson.objectid import ObjectId
from pymongo.database import Database

from .. import exceptions as exc


def project_exists(db: Database, project_id: ObjectId, error: bool = False) -> bool:
    project = db.projects.find_one({"_id": project_id})
    if not project:
        if error:
            raise exc.ResourceNotFound(f"Project with id '{str(project_id)}' not found")
        return False

    return True


def user_exists(db: Database, user_id: ObjectId, error: bool = False) -> bool:
    project = db.users.find_one({"_id": user_id})
    if not project:
        if error:
            raise exc.ResourceNotFound(f"User with id '{str(user_id)}' not found")
        return False

    return True
