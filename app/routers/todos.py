# standard packages
from typing import Annotated
# third-party packages
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
# local packages
from app.models import Todo
from app.database import SessionLocal
from .auth import get_current_user

router = APIRouter(
    prefix="/todos",
    tags=['todos']
)


def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    done: bool = Field(default=False)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "A new todo",
                "description": "A new description of a todo",
                "priority": 5,
                "done": False
            }
        }
    }

@router.get("/")
async def read_all_todos(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return db.query(Todo).filter(Todo.owner_id == user.get('user_id')).all()

@router.get("/todos/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Query para obtener el todo
    todo_model = db.query(Todo)\
        .filter(Todo.todo_id == todo_id)\
        .filter(Todo.owner_id == user.get('user_id'))\
        .first()
                  
    if todo_model:
        return todo_model
    else:
        raise HTTPException(status_code=404, detail="Todo not found")
    

@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, 
                      db: db_dependency, 
                      todo: TodoRequest):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    new_todo = Todo(**todo.model_dump(), owner_id=user.get('user_id'))
    db.add(new_todo)
    db.commit()
    return {"message": "Todo created"}

@router.put("/todos/{todo_id}", status_code=status.HTTP_200_OK)
async def update_todo(user: user_dependency,
                      db: db_dependency,
                      todo: TodoRequest, 
                      todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Query para obtener el todo
    todo_model = db.query(Todo)\
        .filter(Todo.todo_id == todo_id)\
        .filter(Todo.owner_id == user.get('user_id'))\
        .first()
    if todo_model:
        todo_model.title = todo.title
        todo_model.description = todo.description
        todo_model.priority = todo.priority
        todo_model.done = todo.done
        db.commit()
        return todo_model
    else:
        raise HTTPException(status_code=404, detail="Todo not found")

@router.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency,
                      db: db_dependency, 
                      todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    todo_model = db.query(Todo)\
        .filter(Todo.todo_id == todo_id)\
        .filter(Todo.owner_id == user.get('user_id'))\
        .first()
    if todo_model:
        db.delete(todo_model)
        db.commit()
    else:
        raise HTTPException(status_code=404, detail="Todo not found")

