# standard packages
from typing import Annotated
# third-party packages
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
# local packages
from app.database import SessionLocal
from .auth import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
