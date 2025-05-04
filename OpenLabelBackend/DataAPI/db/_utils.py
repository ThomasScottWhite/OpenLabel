from typing import Callable

from bson.objectid import ObjectId
from pymongo.client_session import ClientSession
from pymongo.collection import Collection
from pymongo.database import Database

from .. import exceptions as exc


def item_exists(
    collection: Collection, item_id: ObjectId, session: ClientSession | None = None
):
    return collection.find_one({"_id": item_id}, session=session) is not None


class _ExistsChecker:

    def __init__(self, collection: str, item_name: str = "Item"):
        self.collection = collection
        self.item_name = item_name

    def __call__(
        self,
        db: Database,
        item_id: ObjectId,
        error: bool = False,
        session: ClientSession | None = None,
    ):
        """
        Returns `True` if the item exists, `False` otherwise. If `error` is `True`,
        raises a ResourceException if the item does not exist instead of returning.

        Args:
            db: The pymongo Database object to use.
            item_id: The ID of the item for which to check existence.
            error: Whether to raise an error upon the item not existing. Defaults to False.
            session: The pymongo ClientSession to use. Defaults to None.

        Raises:
            ResourceError: if `error` is `True` and the specified item does not exist.

        """
        if not item_exists(db[self.collection], item_id, session=session):
            if error:
                raise exc.ResourceNotFound(
                    f"{self.item_name} with ID '{str(item_id)}' not found"
                )
            return False

        return True


project_exists = _ExistsChecker("projects", "Project")
user_exists = _ExistsChecker("users", "User")
annotation_exists = _ExistsChecker("annotations", "Annotation")
