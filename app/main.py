from fastapi import FastAPI, Request
# local packages
from app import models
from app.database import engine
from app.routers import auth, admin, users, evaluation
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="ADAP API",
    description="API para el sistema de evaluación ADAP",
    version="1.0"
)

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(evaluation.router)