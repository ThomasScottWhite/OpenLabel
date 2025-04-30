from __future__ import annotations

import logging
from typing import Final

from fastapi import APIRouter

from DataAPI import db
from pydantic import BaseModel
from .. import models
from fastapi import APIRouter, Depends
from DataAPI.auth_utils import auth_user
logger = logging.getLogger(__name__)

_section_name: Final[str] = "projects"

# Do not change the name of "router"!
router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


@router.post("/hello")
def hello() -> str:
    return "hello, world!"

class Project(BaseModel):
    token: str

@router.get("/projects")
def view_projects(current_user: dict = Depends(auth_user)) -> dict:
    """View all projects"""
    try:
        projects = db.project.get_all_projects()
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        return {"error": "Failed to fetch projects"}
    
    logger.info(f"Fetched {len(projects)} projects")

    # Convert ObjectId to string for JSON serialization
    for project in projects:
        project["_id"] = str(project["_id"])
        project["createdBy"] = str(project["createdBy"])
        project["updatedAt"] = str(project["updatedAt"])
        project["createdAt"] = str(project["createdAt"])
        project["members"] = [{"userId": str(member["userId"]), "joinedAt": str(member["joinedAt"])} for member in project["members"]]

    return {"projects": projects}