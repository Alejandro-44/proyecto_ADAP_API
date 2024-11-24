from datetime import datetime, timedelta, timezone
import os
from typing import Annotated, Optional
from fastapi import FastAPI, APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from starlette import status
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt
# local packages
from app.database import SessionLocal
from app.models import Company, Employee
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

# configuracion de JWT para autenticación de usuarios
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# configuracion de encriptación de contraseñas
bycrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

class CompanyCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    company_name: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(None, pattern="^\+?[0-9\s]*$")
    is_active: bool = Field(default=True)
    country_of_residence: str = Field(None, description="Country where the company is located")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "tech_corp",
                "email": "contact@techcorp.com",
                "password": "securepassword",
                "company_name": "Tech Corp",
                "phone_number": "+1234567890",
                "is_active": True,
                "country_of_residence": "United States"
            }
        }


from pydantic import BaseModel, Field, EmailStr

class EmployeeCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    nationality: str = Field(None, max_length=50)
    document_id: str = Field(..., description="Unique document ID")
    phone_number: str = Field(None, pattern="^\+?[0-9\s]*$")
    gender: str = Field(None, description="Gender of the employee")
    birth_date: str = Field(None, description="Date of birth (YYYY-MM-DD)")
    city_of_residence: str = Field(None, description="City of residence")
    country_of_residence: str = Field(None, description="Country of residence")
    profession: str = Field(None, description="Profession of the employee")
    position: str = Field(None, description="Job position")
    is_entrepreneur: bool = Field(default=False)
    entrepreneurship_name: str = Field(None, description="Name of the entrepreneurship")
    is_active: bool = Field(default=True)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "johndoe@example.com",
                "password": "securepassword",
                "first_name": "John",
                "last_name": "Doe",
                "nationality": "American",
                "document_id": "123456789",
                "phone_number": "+1234567890",
                "gender": "Male",
                "birth_date": "1990-01-01",
                "city_of_residence": "New York",
                "country_of_residence": "USA",
                "profession": "Software Engineer",
                "position": "Developer",
                "is_entrepreneur": False,
                "is_active": True
            }
        }



class Token(BaseModel):
    access_token: str
    token_type: str


def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


### Funciones auxiliares ###

def authenticate_user(db: Session, username: str, password: str):
    # Buscar en la tabla Company
    user = db.query(Company).filter(Company.username == username).first()
    user_type = "company"

    # Si no se encuentra en Company, buscar en Employee
    if not user:
        user = db.query(Employee).filter(Employee.username == username).first()
        user_type = "employee"

    # Si el usuario no existe o la contraseña es incorrecta, retornar False
    if not user or not bycrypt_context.verify(password, user.hashed_password):
        return None

    # Retornar el usuario y el tipo
    return {"user": user, "user_type": user_type}

def create_access_token(username: str, user_id: int, user_type: str, expires_delta: timedelta):
    to_encode = {
        'sub': username,
        'id': user_id,
        'user_type': user_type  # Nuevo campo para especificar el tipo de usuario
    }
    expires = datetime.now(timezone.utc) + expires_delta
    to_encode.update({'exp': expires})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_bearer), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_type: str = payload.get("user_type")
        
        if not username or not user_id or not user_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        if user_type == "company":
            user = db.query(Company).filter(Company.company_id == user_id).first()
        elif user_type == "employee":
            user = db.query(Employee).filter(Employee.employee_id == user_id).first()
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user type")

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return {
            "username": username,
            "user_id": user_id,
            "user_type": user_type
        }
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid or expired")

def is_username_email_taken(db: Session, username: str, email: str):
    company = db.query(Company).filter((Company.username == username) | (Company.email == email)).first()
    employee = db.query(Employee).filter((Employee.username == username) | (Employee.email == email)).first()
    return company or employee

## Endpoints ##

@router.post('/company', status_code=status.HTTP_201_CREATED)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    # Verificar si el username o email ya están registrados
    if db.query(Company).filter(
        (Company.username == company.username) | (Company.email == company.email)
    ).first():
        raise HTTPException(status_code=400, detail="Username or email already registered")

    hashed_password = bycrypt_context.hash(company.password)

    new_company = Company(
        username=company.username,
        email=company.email,
        hashed_password=hashed_password,
        company_name=company.company_name,
        phone_number=company.phone_number,
        is_active=company.is_active,
        country_of_residence=company.country_of_residence
    )

    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    return {"message": f"Company {new_company.username} created successfully", "company_id": new_company.company_id}

@router.post('/employee', status_code=status.HTTP_201_CREATED)
def create_employee(
    employee: EmployeeCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para crear un empleado. Solo las compañías pueden realizar esta acción.
    """
    # Verificar que el usuario autenticado es una compañía
    if current_user["user_type"] != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only companies can create employees"
        )

    # Verificar si el correo electrónico ya está registrado
    if db.query(Employee).filter(Employee.email == employee.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Verificar si el documento ya está registrado
    if db.query(Employee).filter(Employee.document_id == employee.document_id).first():
        raise HTTPException(status_code=400, detail="Document ID already registered")

    hashed_password = bycrypt_context.hash(employee.password)

    # Crear un nuevo empleado con todos los campos requeridos
    new_employee = Employee(
        username=employee.username,
        email=employee.email,
        hashed_password=hashed_password,
        first_name=employee.first_name,
        last_name=employee.last_name,
        nationality=employee.nationality,
        document_id=employee.document_id,
        phone_number=employee.phone_number,
        gender=employee.gender,
        birth_date=employee.birth_date,
        city_of_residence=employee.city_of_residence,
        country_of_residence=employee.country_of_residence,
        profession=employee.profession,
        position=employee.position,
        is_entrepreneur=employee.is_entrepreneur,
        entrepreneurship_name=employee.entrepreneurship_name if employee.is_entrepreneur else None,
        is_active=employee.is_active,
        company_id=current_user["user_id"]  # Usar el ID de la compañía autenticada
    )

    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    
    return {"message": f"Employee {new_employee.username} created successfully", "employee_id": new_employee.employee_id}

@router.post('/token')
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    auth_data = authenticate_user(db, form_data.username, form_data.password)
    if not auth_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    user = auth_data["user"]
    user_type = auth_data["user_type"]

    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        username=user.username,
        user_id=user.company_id if user_type == "company" else user.employee_id,
        user_type=user_type,  # Pasar el tipo de usuario
        expires_delta=token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/company_only_route")
async def company_only_route(current_user: dict = Depends(get_current_user)):
    if current_user["user_type"] != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to companies only"
        )
    # Lógica específica para compañías
    return {"message": "Welcome, company!"}

@router.get('/verify_token')
async def verify_token(current_user: dict = Depends(get_current_user)):
    """
    Endpoint para verificar la validez del token y devolver información del usuario.
    """
    return {
        "username": current_user["username"],
        "user_id": current_user["user_id"],
        "user_type": current_user["user_type"]
    }