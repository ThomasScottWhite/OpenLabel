from io import BytesIO
from pathlib import Path

from PIL import Image

from . import auth_utils, db, models


def init_test_data():
    token = db.user.create_user(
        "admin",
        "admin@email.com",
        "admin",
        "Admin",
        "User",
        "admin",
    )

    admin_id = auth_utils.decode_token(token).userId

    project1_id = db.project.create_project(
        name="Default Project 1",
        description="This is a default project for image object-detection.",
        created_by=admin_id,
        is_public=True,
        data_type=models.DataType.IMAGE,
        annotation_type=models.ProjectAnnotationType.OBJECT_DETECTION,
    )
    project2_id = db.project.create_project(
        name="Default Project 2",
        description="This is a default project for text classification.",
        created_by=admin_id,
        is_public=True,
        data_type=models.DataType.TEXT,
        annotation_type=models.ProjectAnnotationType.CLASSIFICATION,
    )
    project3_id = db.project.create_project(
        name="Default Project 3",
        description="This is a default project for image classification.",
        created_by=admin_id,
        is_public=True,
        data_type=models.DataType.IMAGE,
        annotation_type=models.ProjectAnnotationType.CLASSIFICATION,
    )

    image_folder = Path(__file__).resolve().parents[1] / "test_data"

    project1_imgs = []
    project3_imgs = []

    for filename in ("test_image1.png", "test_image2.png"):
        with open(image_folder / filename, "rb") as f:
            image = Image.open(BytesIO(f.read()))
            width, height = image.size
            meta = db.image.upload_image(
                f,
                project1_id,
                admin_id,
                filename,
                width,
                height,
                content_type="image/png",
            )
            project1_imgs.append(meta)

    for filename in ("test_image3.png", "test_image4.png"):
        with open(image_folder / filename, "rb") as f:
            image = Image.open(BytesIO(f.read()))
            width, height = image.size
            meta = db.image.upload_image(
                f,
                project3_id,
                admin_id,
                filename,
                width,
                height,
                content_type="image/png",
            )
            project3_imgs.append(meta)

    # db.annotation.create_bounding_box(project1_imgs[0])


if __name__ == "__main__":
    init_test_data()
