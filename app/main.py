from fastapi import FastAPI, Request
# local packages
from app import models
from app.database import engine
from app.routers import auth, admin, users, evaluation, dashboard
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ADAP API",
    description="API para el sistema de evaluación ADAP",
    version="1.0"
)

# Configuración de CORS
origins = [
    "http://localhost:5173",  # Permitir tu cliente React
    "http://127.0.0.1:5173"   # Alternativa si usas localhost de otra forma
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,             # Permitir estos orígenes
    allow_credentials=True,            # Permitir cookies/credenciales
    allow_methods=["*"],               # Permitir todos los métodos HTTP (GET, POST, etc.)
    allow_headers=["*"],               # Permitir todos los encabezados
)

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(evaluation.router)
app.include_router(dashboard.router)