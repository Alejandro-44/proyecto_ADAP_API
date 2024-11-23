from typing import Annotated, List
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


class EmployeeResponse(BaseModel):
    employee_id: int
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str

    class Config:
        from_attributes = True

class CompanyResponse(BaseModel):
    company_id: int
    username: str
    email: EmailStr
    company_name: str
    phone_number: str

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
    company = db.query(Company).filter(Company.company_id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Obtener empleados de la compañía del usuario autenticado
    employees = db.query(Employee).filter(Employee.company_id == company_id).all()
    
    if not employees:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No employees found for this company")

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