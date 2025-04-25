import fastapi
import pydantic
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from datetime import datetime, timedelta
import base64
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path

app = fastapi.FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or "*" if you're testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Expects This Interface As Output
# interface Project {
#   id: number;
#   name: string;
#   description: string;
# }
@app.get("/projects")
async def get_projects():
    return [
        {"id": 1, "name": "Project One", "description": "image classification"},
        {"id": 2, "name": "Project Two", "description": "text classification"},
        {"id": 3, "name": "Project Three", "description": "object detection"},
    ]


# Expects This Interface As Output


# export interface Project {
#   id: number;
#   name: string;
#   description: string;
#   type: string; // e.g., "image"
#   annotator_layout: string; // e.g., "classification"
#   num_files: number;
#   num_annotated: number;
#   files: ProjectFile[];
# }

# export interface ProjectFile {
#   id: number;
#   name: string;
#   description: string;
#   size: number; // in bytes
#   type: string; // MIME type like "image/png"
#   uploaded_at: string; // ISO string
# }

@app.get("/projects/{project_id}")
async def get_project(project_id: int):
    if project_id == 1:
        return {"id": 1, "name": "Project One", "description": "First project", "type" : "image", "annotator_layout": "classification", "num_files" : 2, "num_annotated" : 0, "files": [
            {"id": 1, "name": "File One", "description": "First file", "size": 1234, "type": "image/png", "uploaded_at": "2023-01-01T00:00:00Z"},
            {"id": 2, "name": "File Two", "description": "Second file", "size": 5678, "type": "image/jpeg", "uploaded_at": "2023-01-02T00:00:00Z"},
        ]}
    elif project_id == 2:
        return {"id": 2, "name": "Project Two", "description": "Second project", "type" : "text", "annotator_layout": "classification", "num_files" : 3, "num_annotated" : 1, "files": [
            {"id": 3, "name": "File Three", "description": "Third file", "size": 91011, "type": "text/plain", "uploaded_at": "2023-01-03T00:00:00Z"},
            {"id": 4, "name": "File Four", "description": "Fourth file", "size": 121314, "type": "text/html", "uploaded_at": "2023-01-04T00:00:00Z"},
        ]}
    elif project_id == 3:
        return {"id": 3, "name": "Project Three", "description": "Third project", "type" : "video", "annotator_layout": "object-detection", "num_files" : 1, "num_annotated" : 0, "files": [
            {"id": 5, "name": "File Five", "description": "Fifth file", "size": 151617, "type": "video/mp4", "uploaded_at": "2023-01-05T00:00:00Z"},
        ]}
    else:
        raise HTTPException(status_code=404, detail="Project not found")

# Expects This Interface As Output
# export interface AnnotatorLayout {
#   type: "image" | "text" | "video";
#   layout: "classification" | "object-detection" | "segmentation" | string;
#   labels: string[];
# }



# Expects This Interface As Output
# export interface ProjectFile {
#   id: number;
#   name: string;
#   description: string;
#   size: number;
#   type: string;
#   uploaded_at: string;
# }
@app.get("/projects/{project_id}/annotator_layout")
async def get_project_annotator_layout(project_id: int):
    # Replace with your actual layout retrieval logic
    if project_id == 1:
        return {"type": "image", "layout": "classification", "labels": ["Label1", "Label2"]}
    elif project_id == 2:
        return {"type": "text", "layout": "classification", "labels": ["Label3", "Label4"]}
    elif project_id == 3:
        return {"type": "image", "layout": "object-detection", "labels": ["Label5", "Label6"]}
    else:
        raise HTTPException(status_code=404, detail="Project not found")

# export interface ProjectFileWithData extends ProjectFile {
#   data: string;
# }
@app.get("/projects/{project_id}/files")
async def get_project_files(project_id: int):
    # Replace with your actual file retrieval logic
    if project_id == 1:
        return [
            {"id": 1, "name": "File One", "description": "First file", "size": 1234, "type": "image/png", "uploaded_at": "2023-01-01T00:00:00Z"},
            {"id": 2, "name": "File Two", "description": "Second file", "size": 5678, "type": "image/png", "uploaded_at": "2023-01-02T00:00:00Z"},
        ]
    elif project_id == 2:
        return [
            {"id": 3, "name": "File Three", "description": "Third file", "size": 91011, "type": "text/plain", "uploaded_at": "2023-01-03T00:00:00Z"},
            {"id": 4, "name": "File Four", "description": "Fourth file", "size": 121314, "type": "text/html", "uploaded_at": "2023-01-04T00:00:00Z"},
        ]
    elif project_id == 3:
        return [
            {"id": 5, "name": "File Five", "description": "Fifth file", "size": 151617, "type": "image/png", "uploaded_at": "2023-01-05T00:00:00Z"},
            {"id": 6, "name": "File Six", "description": "Sixth file", "size": 181920, "type": "image/png", "uploaded_at": "2023-01-06T00:00:00Z"},
        ]
    else:
        raise HTTPException(status_code=404, detail="Project not found")

# Expects This Interface As Output
# export interface ProjectFile {
#   id: number;
#   name: string;
#   description: string;
#   size: number;
#   type: string;
#   uploaded_at: string;
# }

# export interface ProjectFileWithData extends ProjectFile {
#   data: string;
# }

@app.get("/projects/{project_id}/files/{file_id}")
async def get_project_file(project_id: int, file_id: int):
    file_mapping = {
        (1, 1): "./test_data/test_image1.png",
        (1, 2): "./test_data/test_image2.png",
        (2, 3): "./test_data/test_text1.txt",
        (2, 4): "./test_data/test_text2.txt",
        (3, 5): "./test_data/test_image3.png",
        (3, 6): "./test_data/test_image4.png",
    }

    file_path = file_mapping.get((project_id, file_id))
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    file_bytes = Path(file_path).read_bytes()
    encoded_data = base64.b64encode(file_bytes).decode('utf-8')

    file_type = "image/png" if file_path.endswith(".png") else "text/plain" if file_path.endswith(".txt") else "video/mp4"

    # Generate different fake annotations based on the project type
    if project_id == 1:
        # Text Classification
        annotations = [
            {"annotator": "user1@example.com", "label": "Positive"},
            {"annotator": "user2@example.com", "label": "Negative"},
        ]
    elif project_id == 2:
        # Image Classification
        annotations = [
            {"annotator": "user3@example.com", "label": "Cat"},
            {"annotator": "user4@example.com", "label": "Dog"},
        ]
    elif project_id == 3:
        # Object Detection
        annotations = [
            {"annotator": "user5@example.com", "label": "Car", "bbox": [.25, .25, .5, .5]},
            {"annotator": "user6@example.com", "label": "Person", "bbox": [.25, .25, .5, .5]},
        ]
    else:
        annotations = []

    return {
        "id": file_id,
        "name": f"File {file_id}",
        "description": f"File {file_id} description",
        "size": len(file_bytes),
        "type": file_type,
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
        "data": encoded_data,
        "annotations": annotations,
    }
    

SECRET_KEY = "your-secret"
ALGORITHM = "HS256"


@app.post("/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Replace with your actual user validation
    # if form_data.username != "admin@admin.admin" or form_data.password != "12345":
    #     raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {
        "sub": form_data.username,
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    print("Success")
    print(token)
    return {"access_token": token, "token_type": "bearer"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
