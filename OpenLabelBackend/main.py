import fastapi
import pydantic
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from datetime import datetime, timedelta


app = fastapi.FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or "*" if you're testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}

# Expects This Interface As Output
# interface Project {
#   id: number;
#   name: string;
#   description: string;
# }
@app.get("/projects")
async def get_projects():
    return [
        {"id": 1, "name": "Project One", "description": "First project"},
    ]

# Expects This Interface As Output
# interface Project {
#   id: number;
#   name: string;
#   description: string;
# }
@app.get("/projects")
async def get_projects():
    return [
        {"id": 1, "name": "Project One", "description": "First project"},
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
    # Replace with your actual project retrieval logic
    if project_id == 1:
        return {"id": 1, "name": "Project One", "description": "First project", "type" : "image", "annotator_layout": "classification", "num_files" : 2, "num_annotated" : 0, "files": [
            {"id": 1, "name": "File One", "description": "First file", "size": 1234, "type": "image/png", "uploaded_at": "2023-01-01T00:00:00Z"},
            {"id": 2, "name": "File Two", "description": "Second file", "size": 5678, "type": "image/jpeg", "uploaded_at": "2023-01-02T00:00:00Z"},
        ]}
    else:
        raise HTTPException(status_code=404, detail="Project not found")

@app.get("/projects/{project_id}/annotator_layout")
async def get_project_annotator_layout(project_id: int):
    # Replace with your actual layout retrieval logic
    if project_id == 1:
        return {"type": "text", "layout": "classification", "labels": ["cat", "dog", "bird"]}
    else:
        raise HTTPException(status_code=404, detail="Project not found")
     
@app.get("/projects/{project_id}/files")
async def get_project_files(project_id: int):
    # Replace with your actual file retrieval logic
    if project_id == 1:
        return [
            {"id": 1, "name": "File One", "description": "First file", "size": 1234, "type": "image/png", "uploaded_at": "2023-01-01T00:00:00Z"},
            {"id": 2, "name": "File Two", "description": "Second file", "size": 5678, "type": "image/jpeg", "uploaded_at": "2023-01-02T00:00:00Z"},
        ]
    else:
        raise HTTPException(status_code=404, detail="Project not found")
    
@app.get("/projects/{project_id}/files/{file_id}")
async def get_project_file(project_id: int, file_id: int):
    # Replace with your actual file retrieval logic
    if project_id == 1 and file_id in [1, 2]:
        return {"id": file_id, "name": f"File {file_id}", "description": f"File {file_id} description", "size": 1234, "type": "image/png", "uploaded_at": "2023-01-01T00:00:00Z", "data": "This is the file content"}
    else:
        raise HTTPException(status_code=404, detail="File not found")
    

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
