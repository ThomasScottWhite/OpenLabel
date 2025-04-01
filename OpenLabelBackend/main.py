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


@app.get("/projects/")
def read_project():
    return {}


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
