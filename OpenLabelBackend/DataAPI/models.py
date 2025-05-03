from __future__ import annotations

import datetime
from enum import Enum
from typing import Annotated, Any, Literal

import gridfs
from bson.objectid import ObjectId
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    GetCoreSchemaHandler,
    PlainSerializer,
)
from pydantic_core import core_schema


class CRUD(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class ImageStatus(str, Enum):
    ANNOTATED = "annotated"
    UNPROCESSED = "unprocessed"


class AnnotationType(str, Enum):
    BOUNDING_BOX = "boundingBox"
    POLYGON = "polygon"


class ProjectAnnotationType(str, Enum):
    CLASSIFICATION = "classification"
    OBJECT_DETECTION = "object-detection"


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
    createdBy: ID


class HasUserID(BaseModel):
    userId: ID


class HasUserIDAuto(HasUserID):
    """Same as HasUserID, but automatically populates the field from '_id'"""

    userId: ID = Field(validation_alias="_id")


class HasProjectID(BaseModel):
    projectId: ID


class HasImageID(BaseModel):
    imageId: ID


class HasRoleID(BaseModel):
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
    points: Annotated[list[Point], Field(min_length=3)]


class Annotatation(HasCreatedBy, HasCreatedAt, HasUpdatedAt, HasProjectID, HasImageID):
    annotationId: ID = Field(validation_alias="_id")
    type: AnnotationType
    label: str
    coordinates: Coordinates | Points
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]


class BoundingBoxAnnotation(Annotatation):
    type: Literal[AnnotationType.BOUNDING_BOX] = AnnotationType.BOUNDING_BOX
    coordinates: Coordinates


class PolygonAnnotation(Annotatation):
    type: Literal[AnnotationType.POLYGON] = AnnotationType.POLYGON
    coordinates: Points


class UpdateAnnotation(BaseModel):
    """Intended use: update.model_dump(exclude_unset=True)

    All default values are dummy values and are not intended to actually be used, hence
    the excluding of unset parameters.
    """

    label: str = ""
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    coordinates: Coordinates | Points = Points(
        points=[Point(x=0, y=0), Point(x=0, y=0), Point(x=0, y=0)]
    )


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
    annotatationType: ProjectAnnotationType
    isPublic: bool = False


class Project(HasCreatedBy, HasCreatedAt, HasUpdatedAt):
    name: str
    description: str
    members: list[ProjectMember]
    settings: ProjectSettings
    numFiles: int = 0
    numAnnotated: int = 0


# USERS


class UserNoPassword(HasCreatedAt, HasRoleID):

    username: str
    email: EmailStr
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


class ImageMeta(HasCreatedBy, HasCreatedAt, HasProjectID, HasImageID):
    filename: str
    width: int
    height: int
    # exif: dict
    contentType: str  # use MIME types
    status: ImageStatus = ImageStatus.UNPROCESSED

    @classmethod
    def from_grid_out(cls, grid_out: gridfs.GridOut) -> ImageMeta:
        print(grid_out.metadata, grid_out.filename)
        return cls(
            **grid_out.metadata, imageId=grid_out._id, filename=grid_out.filename
        )
