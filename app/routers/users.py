from typing import Annotated, List, Optional
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status
from app.models import Company, Employee
from app.database import SessionLocal
from .auth import get_current_user
from passlib.context import CryptContext

router = APIRouter(
    prefix='/user',
    tags=['user']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


# Esquema para devolver información de la compañía
class CompanyResponse(BaseModel):
    company_id: int
    username: str
    email: str
    company_name: str
    phone_number: str
    is_active: bool
    country_of_residence: str

    class Config:
        from_attributes = True


# Esquema para devolver información del empleado
class EmployeeResponse(BaseModel):
    employee_id: int
    username: str
    email: str
    first_name: str
    last_name: str
    nationality: str
    document_id: str
    phone_number: str
    gender: str
    birth_date: str
    city_of_residence: str
    country_of_residence: str
    profession: str
    position: str
    is_entrepreneur: bool
    entrepreneurship_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# Modelo de entrada para cambiar la contraseña
class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)

@router.get("/companies", response_model=List[CompanyResponse], status_code=status.HTTP_200_OK)
async def get_companies(db: Session = Depends(get_db)):
    """
    Endpoint para obtener la lista de todas las compañías.
    """
    companies = db.query(Company).all()
    if not companies:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No companies found")

    return companies


@router.get("/employees", response_model=List[EmployeeResponse], status_code=status.HTTP_200_OK)
async def get_employees_of_current_company(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para obtener la lista de empleados de la compañía del usuario autenticado.
    """
    # Verificar que el usuario autenticado es de tipo 'company'
    if current_user["user_type"] != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to company users"
        )

    # Obtener la compañía actual del usuario autenticado
    company_id = current_user["user_id"]

    # Verificar que la compañía exista (esto es redundante, pero asegura consistencia)
    company = db.query(Company).filter(Company.company_id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Company not found"
        )

    # Obtener empleados de la compañía
    employees = db.query(Employee).filter(Employee.company_id == company_id).all()

    # Retornar una lista vacía si no hay empleados en la compañía
    return employees


@router.put("/companies/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_company_password(
    password_data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para que una compañía cambie su contraseña.
    """
    # Verificar que el usuario es una compañía
    if current_user["user_type"] != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to companies"
        )

    # Buscar la compañía autenticada en la base de datos
    company = db.query(Company).filter(Company.company_id == current_user["user_id"]).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Verificar la contraseña actual
    if not bcrypt_context.verify(password_data.current_password, company.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    # Hashear la nueva contraseña y actualizarla en la base de datos
    company.hashed_password = bcrypt_context.hash(password_data.new_password)
    db.add(company)
    db.commit()

@router.put("/employees/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_employee_password(
    password_data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para que un empleado cambie su contraseña.
    """
    # Verificar que el usuario es un empleado
    if current_user["user_type"] != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to employees"
        )

    # Buscar el empleado autenticado en la base de datos
    employee = db.query(Employee).filter(Employee.employee_id == current_user["user_id"]).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Verificar la contraseña actual
    if not bcrypt_context.verify(password_data.current_password, employee.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    # Hashear la nueva contraseña y actualizarla en la base de datos
    employee.hashed_password = bcrypt_context.hash(password_data.new_password)
    db.add(employee)
    db.commit()

@router.get("/me", response_model=dict, status_code=status.HTTP_200_OK)
def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para obtener la información del usuario actual (compañía o empleado).
    """
    user_id = current_user["user_id"]
    user_type = current_user["user_type"]

    if user_type == "company":
        user = db.query(Company).filter(Company.company_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compañía no encontrada"
            )
        return {
            "user_type": "company",
            "data": CompanyResponse.from_orm(user)
        }

    elif user_type == "employee":
        user = db.query(Employee).filter(Employee.employee_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empleado no encontrado"
            )
        return {
            "user_type": "employee",
            "data": EmployeeResponse.from_orm(user)
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tipo de usuario desconocido"
    )