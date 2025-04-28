import datetime
from enum import Enum
from typing import Annotated, Literal

from bson.objectid import ObjectId
from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

# put pydantic models here


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


class ExportFormat(str, Enum):
    COCO = "COCO"
    YOLO = "YOLO"
    ONNX = "ONNX"


ID = Annotated[ObjectId, PlainSerializer(lambda x: str(x), return_type=str)]


# SHARED PROPERTIES


class HasCreateAt(BaseModel):
    createdAt: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class HasUpdatedAt(BaseModel):
    updatedAt: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class HasCreatedBy(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    createdBy: ID


# ROLES
class Permission(BaseModel):
    resource: str
    actions: list[CRUD]


class Role(BaseModel):
    name: str
    permissions: list[Permission]
    description: str


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


class Annotatation(HasCreatedBy, HasCreateAt, HasUpdatedAt):
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


# PROJECTS


class ProjectMember(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    userID: ID
    roleID: ID
    joinedAt: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class ProjectSettings(BaseModel):
    exportFormat: ExportFormat = ExportFormat.COCO
    annotatationTypes: list[AnnotationType]
    isPublic: bool = False


class Project(HasCreatedBy, HasCreateAt, HasUpdatedAt):
    name: str
    description: str
    members: list[ProjectMember]
    settings: ProjectSettings


# USERS


class UserNoPassword(HasCreateAt):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    username: str
    email: str
    firstName: str
    lastName: str
    roleId: ID
    lastLogin: datetime.datetime | None = None
    isActive: bool


class User(UserNoPassword):
    password: bytes


# IMAGES


class ImageMeta(HasCreatedBy, HasCreateAt):

    projectID: ID
    width: int
    height: int
    exif: dict
    contentType: str  # use MIME types
    status: ImageStatus = ImageStatus.UNPROCESSED
