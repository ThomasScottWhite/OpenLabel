import random
import string
from io import BytesIO
from pathlib import Path

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
    project1_labels = ["bird", "cat", "dog", "lynx", "fish"]
    project2_labels = ["happy", "sad", "glad", "disappointed", "mad"]

    project1_id = db.project.create_project(
        name="Default Project 1",
        description="This is a default project for image object-detection.",
        created_by=admin_id,
        is_public=True,
        data_type=models.DataType.IMAGE,
        annotation_type=models.AnnotationType.OBJECT_DETECTION,
        labels=project1_labels,
    )
    project2_id = db.project.create_project(
        name="Default Project 2",
        description="This is a default project for text classification.",
        created_by=admin_id,
        is_public=True,
        data_type=models.DataType.TEXT,
        annotation_type=models.AnnotationType.CLASSIFICATION,
        labels=project2_labels,
    )
    project3_id = db.project.create_project(
        name="Default Project 3",
        description="This is a default project for image classification.",
        created_by=admin_id,
        is_public=True,
        data_type=models.DataType.IMAGE,
        annotation_type=models.AnnotationType.CLASSIFICATION,
        labels=["car", "bike", "shirt"],
    )

    image_folder = Path(__file__).resolve().parents[1] / "test_data"

    project1_files: list[models.FileMeta] = []
    project2_files: list[models.FileMeta] = []
    project3_files: list[models.FileMeta] = []

    text = string.ascii_letters + string.digits + " "

    for filename in ("test_image1.png", "test_image2.png"):
        with open(image_folder / filename, "rb") as f:
            meta = db.file.upload_file(
                f,
                project1_id,
                admin_id,
                filename,
                content_type="image/png",
            )
            project1_files.append(meta)

    for filename in ("test_text1.txt", "test_text2.txt"):
        with open(image_folder / filename, "rb") as f:
            meta = db.file.upload_file(
                f,
                project2_id,
                admin_id,
                filename,
                content_type="text/plain",
            )
            project2_files.append(meta)

    for i in range(100):
        contents = "".join(random.choices(text, k=random.randint(100, 2000)))

        with BytesIO(contents.encode()) as file:
            meta = db.file.upload_file(
                file,
                project2_id,
                admin_id,
                f"random_text{i}.txt",
                content_type="text/plain",
            )
            project2_files.append(meta)

    for filename in ("test_image3.png", "test_image4.png"):
        with open(image_folder / filename, "rb") as f:
            meta = db.file.upload_file(
                f,
                project3_id,
                admin_id,
                filename,
                content_type="image/png",
            )
            project3_files.append(meta)

    print(project1_files)
    print(project2_files)
    print(project3_files)

    for file in project1_files:
        for _ in range(random.randint(0, 10)):

            bbox = models.BBox(
                x=random.random(),
                y=random.random(),
                width=random.random(),
                height=random.random(),
            )

            db.annotation.create_object_detection_annotation(
                file_id=file.fileId,
                project_id=file.projectId,
                label=random.choice(project1_labels),
                bbox=bbox,
                created_by=admin_id,
            )

    for file in project2_files:
        db.annotation.create_classification_annotation(
            file_id=file.fileId,
            project_id=file.projectId,
            label=random.choice(project2_labels),
            created_by=admin_id,
        )

    db.export.export_project(project1_id, models.ExportFormat.COCO)
    db.export.export_project(project2_id, models.ExportFormat.CLASSIFICATION)


if __name__ == "__main__":
    init_test_data()
