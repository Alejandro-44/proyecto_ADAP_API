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

# Modelos de validación para las solicitudes
class UpdateCompanyRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    company_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, pattern="^\+?[0-9\s]*$")
    country_of_residence: Optional[str] = None
    is_active: Optional[bool] = None
    class Config:
        json_schema_extra = {
            "example": {
                "email": "new_email@example.com",
                "username": "updated_company",
                "company_name": "Updated Tech Corp",
                "phone_number": "+1234567890",
                "country_of_residence": "Canada",
                "is_active": True
            }
        }

class UpdateEmployeeRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    nationality: Optional[str] = None
    document_id: Optional[str] = None
    phone_number: Optional[str] = Field(None, pattern="^\+?[0-9\s]*$")
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    city_of_residence: Optional[str] = None
    country_of_residence: Optional[str] = None
    profession: Optional[str] = None
    position: Optional[str] = None
    is_entrepreneur: Optional[bool] = None
    entrepreneurship_name: Optional[str] = None
    is_active: Optional[bool] = None

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
    employees = db.query(Employee).filter((Employee.company_id == company_id) & (Employee.is_active == True)).all()

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
    Si el usuario es un empleado, se incluye la información de la compañía a la que pertenece.
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
            "data": CompanyResponse.model_validate(user)
        }

    elif user_type == "employee":
        user = db.query(Employee).filter(Employee.employee_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empleado no encontrado"
            )

        # Obtener información de la compañía del empleado
        company = db.query(Company).filter(Company.company_id == user.company_id).first()

        return {
            "user_type": "employee",
            "data": {
                "employee_info": EmployeeResponse.model_validate(user),
                "company_info": CompanyResponse.model_validate(company) if company else None
            }
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tipo de usuario desconocido"
    )

@router.put("/employee/{employee_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para desactivar un empleado.
    Solo los usuarios de tipo 'company' pueden realizar esta acción.
    """
    # Verificar que el usuario autenticado sea de tipo 'company'
    if current_user["user_type"] != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only companies can deactivate employees."
        )

    # Verificar que el empleado existe y pertenece a la compañía autenticada
    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id,
        Employee.company_id == current_user["user_id"]
    ).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found or does not belong to your company."
        )

    # Marcar al empleado como inactivo
    employee.is_active = False
    db.commit()

    return {"message": "Employee deactivated successfully."}

@router.put("/update_user", status_code=status.HTTP_200_OK)
def update_user(
    company_update: Optional[UpdateCompanyRequest] = None,
    employee_update: Optional[UpdateEmployeeRequest] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para actualizar los datos del usuario actual (compañía o empleado).
    """
    user_id = current_user["user_id"]
    user_type = current_user["user_type"]

    if user_type == "company":
        if not company_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body for company update is required."
            )

        company = db.query(Company).filter(Company.company_id == user_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )

        # Actualizar los campos proporcionados en el request
        for key, value in company_update.dict(exclude_unset=True).items():
            setattr(company, key, value)

        db.commit()
        db.refresh(company)

        return {
            "message": "Company updated successfully",
            "data": {
                "username": company.username,
                "email": company.email,
                "company_name": company.company_name,
                "phone_number": company.phone_number,
                "country_of_residence": company.country_of_residence,
                "is_active": company.is_active
            }
        }

    elif user_type == "employee":
        if not employee_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body for employee update is required."
            )

        employee = db.query(Employee).filter(Employee.employee_id == user_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )

        # Actualizar los campos proporcionados en el request
        for key, value in employee_update.dict(exclude_unset=True).items():
            setattr(employee, key, value)

        db.commit()
        db.refresh(employee)

        return {
            "message": "Employee updated successfully",
            "data": {
                "username": employee.username,
                "email": employee.email,
                "first_name": employee.first_name,
                "last_name": employee.last_name,
                "nationality": employee.nationality,
                "document_id": employee.document_id,
                "phone_number": employee.phone_number,
                "gender": employee.gender,
                "birth_date": employee.birth_date,
                "city_of_residence": employee.city_of_residence,
                "country_of_residence": employee.country_of_residence,
                "profession": employee.profession,
                "position": employee.position,
                "is_entrepreneur": employee.is_entrepreneur,
                "entrepreneurship_name": employee.entrepreneurship_name,
                "is_active": employee.is_active
            }
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unknown user type"
    )