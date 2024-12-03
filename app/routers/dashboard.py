import os
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path
from pydantic import BaseModel

from app.models import Company, Employee
from .auth import get_current_user, get_db
from jose import jwt
from sqlalchemy.orm import Session
from starlette import status
from app.database import SessionLocal
import time

router = APIRouter(
    prefix="/dashboard",
    tags=['dashboard']
)

METABASE_SITE_URL = os.getenv("METABASE_SITE_URL")
METABASE_SECRET_KEY = os.getenv("METABASE_SECRET_KEY")

# Pydantic Model para el request
class MetabaseDashboardRequest(BaseModel):
    template_id: int  # ID del template asociado al dashboard 

# Función auxiliar para generar la URL
def generate_employee_dashboard_url(empleado: str, empresa: str, template_id: int) -> str:
    """
    Genera la URL embebida de un dashboard de Metabase.

    Parámetros:
        dashboard_id (int): ID del dashboard en Metabase.
        empleado (str): Nombre de usuario del empleado.
        empresa (str): Nombre de usuario de la empresa.
        evaluacion (int): Id de la evaluación.

    Retorna:
        str: URL del dashboard embebido.
    """
    # Definir la carga útil del token
    payload = {
        "resource": {"dashboard": 7},
        "params": {
            "empleado": empleado,
            "empresa": empresa,
            "evaluacion": template_id
        },
        "exp": round(time.time()) + (60 * 30)  # Expiración de 30 minutos
    }

    # Crear el token JWT
    try:
        token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating JWT: {str(e)}")

    # Generar la URL del iframe
    iframe_url = f"{METABASE_SITE_URL}/embed/dashboard/{token}#bordered=true&titled=true"

    return iframe_url

@router.post("/generate_dashboard_url", status_code=status.HTTP_200_OK)
def get_dashboard_url(
    request: MetabaseDashboardRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para generar la URL embebida de un dashboard de Metabase.
    """
    if not METABASE_SECRET_KEY or not METABASE_SITE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metabase configuration is missing"
        )

    # Obtener el username del usuario actual y validar el tipo de usuario
    username = current_user["username"]

    if current_user["user_type"] == "employee":
        user = db.query(Employee).filter(Employee.username == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        # Obtener la empresa a la que pertenece el empleado
        company = db.query(Company).filter(Company.company_id == user.company_id).first()
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        company_username = company.username

    elif current_user["user_type"] == "company":
        user = db.query(Company).filter(Company.username == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        company_username = username  # El username de la compañía es el de la empresa

    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User type not supported")

    try:
        # Crear el payload para generar el token
        iframe_url = generate_employee_dashboard_url(
            empleado=username,
            empresa=company_username,
            template_id=request.template_id
        )

        return {"iframe_url": iframe_url}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating dashboard URL: {str(e)}"
        )

@router.get("/generate_company_dashboard_url", status_code=status.HTTP_200_OK)
def generate_company_dashboard_url(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para generar la URL embebida del dashboard para empresas en Metabase.
    """
    if not METABASE_SECRET_KEY or not METABASE_SITE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metabase configuration is missing"
        )

    # Verificar que el usuario sea una compañía
    if current_user["user_type"] != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to companies only."
        )

    # Obtener el nombre de la empresa
    company_name = current_user.get("username")
    if not company_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company information is missing."
        )

    try:
        # Crear el payload para el token
        payload = {
            "resource": {"dashboard": 6},  # ID del dashboard para empresas
            "params": {
                "empresa": [company_name]
            },
            "exp": round(time.time()) + (60 * 10)  # Expiración en 10 minutos
        }

        # Generar el token JWT
        token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

        # Construir la URL del iframe
        iframe_url = f"{METABASE_SITE_URL}/embed/dashboard/{token}#bordered=true&titled=true"

        return {"iframe_url": iframe_url}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating dashboard URL: {str(e)}"
        )