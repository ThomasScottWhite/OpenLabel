from __future__ import annotations

import datetime
from enum import Enum
from typing import Annotated, Any, Literal

from bson.objectid import ObjectId
from pydantic import BaseModel, ConfigDict, Field, GetCoreSchemaHandler, PlainSerializer
from pydantic_core import core_schema


class CRUD(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class ImageStatus(str, Enum):
    PROCESSED = "processed"
    UNPROCESSED = "unprocessed"


class AnnotationType(str, Enum):
    BOUNDING_BOX = "boundingBox"
    POLYGON = "polygon"


class DataType(str, Enum):
    TEXT = "text"
    IMAGE = "image"


class ExportFormat(str, Enum):
    COCO = "COCO"
    YOLO = "YOLO"
    ONNX = "ONNX"


class RoleName(str, Enum):
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    ANNOTATOR = "annotator"
    REVIEWER = "reviewer"


class _ObjectID(ObjectId):

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate, core_schema.any_schema()
        )

    @classmethod
    def validate(cls, value: Any):
        return cls(value)


ID = Annotated[
    _ObjectID,
    PlainSerializer(lambda x: str(x), return_type=str, when_used="json"),
]


# SHARED PROPERTIES

_now_field = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


class HasCreatedAt(BaseModel):
    createdAt: datetime.datetime = _now_field


class HasUpdatedAt(BaseModel):
    updatedAt: datetime.datetime = _now_field


class HasJoinedAt(BaseModel):
    joinedAt: datetime.datetime = _now_field


class HasCreatedBy(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    createdBy: ID


class HasUserID(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    userId: ID


class HasUserIDAuto(HasUserID):
    """Same as HasUserID, but automatically populates the field from '_id'"""

    userId: ID = Field(validation_alias="_id")


class HasRoleID(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    roleId: ID


class ForbidExtra(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ROLES
class Permission(BaseModel):
    resource: str
    actions: list[CRUD]


class Role(BaseModel):
    name: str
    permissions: list[Permission]
    description: str


class RoleWithID(Role, HasRoleID):
    pass


# ANNOTATIONS


class Coordinates(BaseModel):
    x: float
    y: float
    width: float
    height: float


class Point(BaseModel):
    x: float
    y: float


class Points(BaseModel):
    points: list[Point]


class Annotatation(HasCreatedBy, HasCreatedAt, HasUpdatedAt):
    type: AnnotationType
    imageId: ID
    projectID: ID
    label: str
    coordinates: Coordinates | Points
    attributes: dict
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]


class BoundingBoxAnnotation(Annotatation):
    type: Literal[AnnotationType.BOUNDING_BOX] = AnnotationType.BOUNDING_BOX
    coordinates: Coordinates


class PolygonAnnotation(Annotatation):
    type: Literal[AnnotationType.POLYGON] = AnnotationType.POLYGON
    coordinates: Points


# AUTH


class TokenOnlyResponse(BaseModel):
    token: str


class TokenPayload(HasUserID):
    exp: datetime.datetime
    iat: datetime.datetime


# PROJECTS


class ProjectMember(HasUserID, HasRoleID, HasJoinedAt):
    pass


class ProjectMemberDetails(HasJoinedAt):
    user: UserNoPasswordWithID
    role: RoleWithID


class ProjectSettings(BaseModel):
    dataType: DataType
    annotatationType: str
    isPublic: bool = False


class Project(HasCreatedBy, HasCreatedAt, HasUpdatedAt):
    name: str
    description: str
    members: list[ProjectMember]
    settings: ProjectSettings


# USERS


class UserNoPassword(HasCreatedAt, HasRoleID):

    username: str
    email: str
    firstName: str
    lastName: str
    lastLogin: datetime.datetime | None = None
    isActive: bool


class UserNoPasswordWithID(UserNoPassword, HasUserIDAuto):
    pass


class User(UserNoPassword):
    password: bytes


class UserWithID(User, HasUserIDAuto):
    pass


# PREFERENCES


class KeyboardShortcuts(BaseModel):
    # TODO: validate keyboard shortcuts??
    createBox: str = "b"
    createPolygon: str = "p"
    deleteAnnotation: str = "d"
    saveAnnotation: str = "ctrl+s"
    nextImage: str = "right"
    prevImage: str = "left"


class UIPreferences(BaseModel):
    theme: str = "light"
    language: str = "en"
    annotationDefaultColor: str = "#FF0000"


class UserPreferences(HasUserID):
    keyboardShortcuts: KeyboardShortcuts
    uiPreferences: UIPreferences


# IMAGES


class ImageMeta(HasCreatedBy, HasCreatedAt):

    projectId: ID
    width: int
    height: int
    exif: dict
    contentType: str  # use MIME types
    status: ImageStatus = ImageStatus.UNPROCESSED
