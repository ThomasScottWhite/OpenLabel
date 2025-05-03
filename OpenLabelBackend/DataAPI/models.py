from __future__ import annotations

import datetime
from enum import Enum
from typing import Annotated, Any, Literal, Self

import gridfs
from bson.objectid import ObjectId
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    GetCoreSchemaHandler,
    PlainSerializer,
    computed_field,
)
from pydantic_core import core_schema


class CRUD(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class FileStatus(str, Enum):
    ANNOTATED = "annotated"
    UNANNOTATED = "unannotated"


class AnnotationType(str, Enum):
    BOUNDING_BOX = "boundingBox"
    POLYGON = "polygon"


class ProjectAnnotationType(str, Enum):
    CLASSIFICATION = "classification"
    OBJECT_DETECTION = "object-detection"
    SEGMENTATION = "segmentation"


class DataType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"

    @classmethod
    def from_mime(cls, mime_type: str) -> DataType:
        if mime_type.startswith("text"):
            return cls.TEXT
        elif mime_type.startswith("image"):
            return cls.IMAGE
        elif mime_type.startswith("video"):
            return cls.VIDEO
        raise ValueError(f"Cannot infer {cls.__name__} from MIME type '{mime_type}'")


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

    userId: ID = Field(validation_alias=AliasChoices("_id", "userId"))


class HasProjectID(BaseModel):
    projectId: ID


class HasFileID(BaseModel):
    fileId: ID


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


class BaseAnnotatation(
    HasCreatedBy, HasCreatedAt, HasUpdatedAt, HasProjectID, HasFileID
):
    annotationId: ID = Field(validation_alias=AliasChoices("_id", "annotationId"))
    type: AnnotationType
    label: str
    coordinates: Coordinates | Points
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]


class BoundingBoxAnnotation(BaseAnnotatation):
    type: Literal[AnnotationType.BOUNDING_BOX] = AnnotationType.BOUNDING_BOX
    coordinates: Coordinates


class PolygonAnnotation(BaseAnnotatation):
    type: Literal[AnnotationType.POLYGON] = AnnotationType.POLYGON
    coordinates: Points


Annotation = Annotated[
    BoundingBoxAnnotation | PolygonAnnotation, Field(discriminator="type")
]


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


# FILES


class _FileMetaBase(HasCreatedBy, HasCreatedAt, HasProjectID, HasFileID):
    filename: str
    # exif: dict
    size: int
    contentType: str  # use MIME types
    type: DataType
    status: FileStatus = FileStatus.UNANNOTATED

    @classmethod
    def from_grid_out(cls, grid_out: gridfs.GridOut) -> type[Self]:
        print(grid_out.metadata, grid_out.filename)
        return cls(
            **grid_out.metadata,
            fileId=grid_out._id,
            filename=grid_out.filename,
        )


class TextMeta(_FileMetaBase):
    type: Literal[DataType.TEXT] = DataType.TEXT


class ImageMeta(_FileMetaBase):
    type: Literal[DataType.IMAGE] = DataType.IMAGE
    width: int
    height: int


class VideoMeta(ImageMeta):
    type: Literal[DataType.VIDEO] = DataType.VIDEO
    framerate: float
    bitrate: float
    duration: float
    frameCount: int


FileMeta = Annotated[ImageMeta | VideoMeta | TextMeta, Field(discriminator="type")]


class File(BaseModel):
    data: str
    metadata: FileMeta


def get_filemeta_model(content_type: str) -> type[FileMeta]:
    """Returns a FileMeta type based on a MIME type

    Args:
        content_type: The type for which to get the associated FileMeta model.
            Must be a MIME type, or simply "image", "text", or "video".

    Returns:
        The FileMeta type that corresponds with `contentType`.
    """
    if content_type.startswith("image"):
        return ImageMeta
    elif content_type.startswith("video"):
        return VideoMeta
    elif content_type.startswith("text"):
        return TextMeta
    raise ValueError(f"Could not find metadata model for type '{content_type}'")


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
    labels: list[str] = Field([])


class Project(HasCreatedBy, HasCreatedAt, HasUpdatedAt, HasProjectID):
    projectId: ID = Field(validation_alias=AliasChoices("_id", "projectId"))
    name: str
    description: str
    settings: ProjectSettings
    members: list[ProjectMember]


class ProjectWithFiles(Project):
    files: list[FileMeta] = Field([])

    @computed_field
    @property
    def numAnnotated(self) -> int:
        return sum([1 for f in self.files if f.status == FileStatus.ANNOTATED])

    @computed_field
    @property
    def numFiles(self) -> int:
        return len(self.files)


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
