# standard packages
from typing import Annotated, List, Optional
from datetime import datetime, timedelta, timezone
# third-party packages
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
# local packages
from app.models import CalculationResult, Category, Company, Employee, EmployeeEvaluation,EvaluationTemplate, Question, Response
from app.database import SessionLocal
from .auth import get_current_user


router = APIRouter(
    prefix="/evaluation",
    tags=['evaluation']
)

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class QuestionSchema(BaseModel):
    id: int
    text: str
    code: str

    class Config:
        from_attributes = True


class CategorySchema(BaseModel):
    id: int
    name: str
    group: str
    questions: List[QuestionSchema]

    class Config:
        from_attributes = True


class EvaluationRequestSchema(BaseModel):
    evaluation_id: int
    title: str
    assigned_date: str
    due_date: Optional[str]
    is_completed: bool
    categories: List[CategorySchema]

    class Config:
        from_attributes = True


class AnswerSchema(BaseModel):
    question_id: int  # ID de la pregunta respondida
    score: int  # Calificación de 1 a 5


class EvaluationResponseSchema(BaseModel):
    evaluation_id: int  # ID de la evaluación
    answers: List[AnswerSchema]  # Lista de respuestas

    class Config:
        json_schema_extra = {
            "example": {
                "evaluation_id": 1,
                "answers": [
                    {"question_id": 1, "score": 5},
                    {"question_id": 2, "score": 4},
                    {"question_id": 3, "score": 3},
                    {"question_id": 4, "score": 2},
                    {"question_id": 5, "score": 0},
                    {"question_id": 6, "score": 4},
                    {"question_id": 7, "score": 2},
                    {"question_id": 8, "score": 1},
                    {"question_id": 9, "score": 0},
                    {"question_id": 10, "score": 3},
                    {"question_id": 11, "score": 3},
                    {"question_id": 12, "score": 3},
                    {"question_id": 13, "score": 1},
                    {"question_id": 14, "score": 5},
                    {"question_id": 15, "score": 5},
                    {"question_id": 16, "score": 2},
                    {"question_id": 17, "score": 0},
                    {"question_id": 18, "score": 0},
                    {"question_id": 19, "score": 4},
                    {"question_id": 20, "score": 4},
                    {"question_id": 21, "score": 0},
                    {"question_id": 22, "score": 4},
                    {"question_id": 23, "score": 3},
                    {"question_id": 24, "score": 2},
                    {"question_id": 25, "score": 0},
                    {"question_id": 26, "score": 5},
                    {"question_id": 27, "score": 3},
                    {"question_id": 28, "score": 3},
                    {"question_id": 29, "score": 0},
                    {"question_id": 30, "score": 3},
                    {"question_id": 31, "score": 1},
                    {"question_id": 32, "score": 3},
                    {"question_id": 33, "score": 3},
                    {"question_id": 34, "score": 1},
                    {"question_id": 35, "score": 5},
                    {"question_id": 36, "score": 4},
                    {"question_id": 37, "score": 5},
                    {"question_id": 38, "score": 5},
                    {"question_id": 39, "score": 4},
                    {"question_id": 40, "score": 5},
                    {"question_id": 41, "score": 5},
                    {"question_id": 42, "score": 3},
                ]
            }
        }

class TemplateResponse(BaseModel):
    id: int
    title: str
    description: str
    created_date: datetime

    class Config:
        from_attributes = True  # Permite usar objetos SQLAlchemy directamente

class CreateEvaluationTemplateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Employee Evaluation 2024",
                "description": "This is the evaluation template for all employees in 2024."
            }
        }

class AssignEvaluationRequest(BaseModel):
    template_id: int
    employee_ids: List[int]
    due_date: datetime
    class Config:
        json_schema_extra = {
            "example": {
                "template_id": 1,
                "employee_ids": [101, 102, 103],
                "due_date": "2024-12-31T23:59:59"
            }
        }

class AssignedEvaluationResponse(BaseModel):
    evaluation_id: int
    title: str
    template_id: int
    assigned_date: Optional[str]
    due_date: Optional[str]
    completion_date: Optional[str]
    is_completed: bool

    class Config:
        from_attributes = True


# Funciones auxiliares de cálculo

def get_response_score_by_code(employee_evaluation_id: int, code: str, db: Session) -> int:
    # Buscar la respuesta que coincide con el código de la pregunta en la evaluación especificada
    response = (
        db.query(Response)
        .join(Question)
        .filter(Response.employee_evaluation_id == employee_evaluation_id)
        .filter(Question.code == code)
        .first()
    )
    
    # Retornar el puntaje si se encuentra la respuesta, o 0 si no existe
    return response.score if response else 0

def calculate_autoliderazgo(employee_evaluation_id: int, db: Session):
    # Obtener los puntajes de las respuestas de Autoliderazgo para cada subfactor
    F1 = sum(get_response_score_by_code(employee_evaluation_id, code, db) * weight for code, weight in [
        ("Auto_10", .2003),
        ("Auto_6", .1918),
        ("Auto_5", .1306),
        ("Auto_3", .124)
    ])
    F2 = get_response_score_by_code(employee_evaluation_id, "Auto_14", db) * .0137
    F3 = get_response_score_by_code(employee_evaluation_id, "Auto_4", db) * .0020
    F4 = get_response_score_by_code(employee_evaluation_id, "Auto_7", db) * .1666
    F5 = sum(get_response_score_by_code(employee_evaluation_id, code, db) * weight for code, weight in [
        ("Auto_8", .0867),
        ("Auto_13", .1036)
    ])
    
    E1 = F1 + F2 + F3 + F4 + F5

    F6 = sum(get_response_score_by_code(employee_evaluation_id, code, db) * weight for code, weight in [
        ("Auto_16", .3726),
        ("Auto_17", .3551),
        ("Auto_15", .2721)
    ])

    E2 = F6

    F7 = sum(get_response_score_by_code(employee_evaluation_id, code, db) * weight for code, weight in [
        ("Auto_1", .1846),
        ("Auto_11", .2267),
        ("Auto_12", .1903)
    ])
    F8 = get_response_score_by_code(employee_evaluation_id, "Auto_2", db) * .0641

    F9 = sum(get_response_score_by_code(employee_evaluation_id, code, db) * weight for code, weight in [
        ("Auto_9", .1846),
        ("Auto_18", .2267),
        ("Auto_19", .0892)
    ])
    E3 = F7 + F8 + F9

    overall_selfleadership = E1 * .3172 + E2 * .3155 + E3 * .3672

    return F1, F2, F3, F4, F5, E1, F6, E2, F7, F8, F9, E3, overall_selfleadership


def calculate_desempeno(employee_evaluation_id: int, db: Session):
    # Calcular los subfactores de Desempeño

    D1 = sum(get_response_score_by_code(employee_evaluation_id, code, db) * weight for code, weight in [
        ("Des_2", .327),
        ("Des_3", .271),
        ("Des_1", .238),
        ("Des_4", .162)
    ])

    D2 = sum(get_response_score_by_code(employee_evaluation_id, code, db) * weight for code, weight in [
        ("Des_8", .1524),
        ("Des_9", .175),
        ("Des_7", .1301),
        ("Des_11", .1272),
        ("Des_10", .1223),
        ("Des_12", .1048),
        ("Des_6", .1045),
        ("Des_5", .834),
    ])

    D3 = sum(get_response_score_by_code(employee_evaluation_id, code, db) * weight for code, weight in [
        ("Des_13", .1882),
        ("Des_14", .2051),
        ("Des_15", .2252),
        ("Des_16", .2029),
        ("Des_17", .1774),
    ])

    overall_performance_score = D1 * .4817 + D2 * .3936 + D3 * .1246

    return D1, D2, D3, overall_performance_score



def calculate_apoyo_organizacional(employee_evaluation_id: int, db: Session):
    # Calcular Apoyo Organizacional Percibido
    organizational_support_score = sum(get_response_score_by_code(employee_evaluation_id, code, db) * weight for code, weight in [
        ("Apoyo_1", .1731),
        ("Apoyo_2", .1963),
        ("Apoyo_3", .1983),
        ("Apoyo_4", .1743),
        ("Apoyo_5", .167),
        ("Apoyo_6",.0908),
    ])

    return organizational_support_score

# Endpoint para enviar respuestas y calcular los resultados

@router.post("/submit", status_code=status.HTTP_201_CREATED)
def submit_evaluation_responses(
    evaluation_data: EvaluationResponseSchema, 
    db: Session = Depends(get_db)
):
    """
    Endpoint para subir las respuestas de una evaluación asignada y calcular los resultados derivados.
    """
    # Verificar si la evaluación asignada existe
    employee_evaluation = db.query(EmployeeEvaluation).filter(
        EmployeeEvaluation.id == evaluation_data.evaluation_id
    ).first()

    if not employee_evaluation:
        raise HTTPException(status_code=404, detail="Evaluación asignada no encontrada.")
    
    # Verificar si la evaluación ya está completada
    if employee_evaluation.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta evaluación ya ha sido completada."
        )

    # Procesar y almacenar cada respuesta
    for answer in evaluation_data.answers:
        # Verificar si la pregunta existe
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail=f"Pregunta con ID {answer.question_id} no encontrada.")
        
        # Verificar si la respuesta ya existe para evitar duplicados
        existing_response = db.query(Response).filter(
            Response.employee_evaluation_id == employee_evaluation.id,
            Response.question_id == answer.question_id
        ).first()

        if existing_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una respuesta para la pregunta con ID {answer.question_id}."
            )

        # Crear una instancia de Response para cada respuesta
        response = Response(
            employee_evaluation_id=employee_evaluation.id,  # Relacionar con EmployeeEvaluation
            question_id=answer.question_id,
            score=answer.score
        )
        # Agregar la respuesta a la sesión
        db.add(response)

    # Confirmar los cambios en la base de datos
    db.commit()

    # Calcular los resultados basados en las respuestas
    F1, F2, F3, F4, F5, E1, F6, E2, F7, F8, F9, E3, overall_selfleadership = calculate_autoliderazgo(employee_evaluation.id, db)
    D1, D2, D3, overall_performance_score = calculate_desempeno(employee_evaluation.id, db)
    organizational_support_score = calculate_apoyo_organizacional(employee_evaluation.id, db)

    # Guardar los resultados en la tabla CalculationResult
    calculation_result = CalculationResult(
        employee_evaluation_id=employee_evaluation.id,  # Relacionar con EmployeeEvaluation
        F1=F1, F2=F2, F3=F3, F4=F4, F5=F5,
        E1=E1, F6=F6, E2=E2, F7=F7, F8=F8, F9=F9,
        E3=E3, overall_selfleadership=overall_selfleadership,
        D1=D1, D2=D2, D3=D3, overall_performance_score=overall_performance_score,
        organizational_support_score=organizational_support_score
    )
    # Agregar el resultado calculado a la sesión y confirmar los cambios
    db.add(calculation_result)

    # Marcar la evaluación como completada y registrar la fecha de realización
    employee_evaluation.is_completed = True
    employee_evaluation.completion_date = datetime.now(timezone.utc)
    db.commit()

    return {
        "message": "Respuestas de la evaluación guardadas exitosamente.",
        "evaluation_id": employee_evaluation.id,
        "results": {
            "overall_selfleadership": overall_selfleadership,
            "overall_performance_score": overall_performance_score,
            "organizational_support_score": organizational_support_score
        }
    }

@router.post("/template", status_code=status.HTTP_201_CREATED)
def create_evaluation_template(
    request: CreateEvaluationTemplateRequest,  # Usar el modelo de validación
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Crear una evaluación general para una compañía.
    """
    # Verificar que el usuario autenticado sea de tipo 'company'
    if current_user["user_type"] != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only companies can create evaluation templates."
        )

    # Obtener el ID de la compañía actual
    company_id = current_user["user_id"]

    # Verificar si ya existe un template con el mismo título para esta compañía
    existing_template = db.query(EvaluationTemplate).filter(
        EvaluationTemplate.title == request.title,
        EvaluationTemplate.company_id == company_id
    ).first()

    if existing_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An evaluation template with this title already exists for your company."
        )

    # Crear la plantilla de evaluación
    evaluation_template = EvaluationTemplate(
        title=request.title,
        description=request.description,
        company_id=company_id
    )

    # Guardar la plantilla en la base de datos
    db.add(evaluation_template)
    db.commit()
    db.refresh(evaluation_template)

    return {
        "message": "Evaluation template created successfully",
        "template_id": evaluation_template.id
    }

@router.get("/templates", response_model=List[TemplateResponse], status_code=status.HTTP_200_OK)
def get_templates_of_current_company(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para obtener la lista de templates de evaluación creados por la compañía actual.
    """
    # Verificar que el usuario autenticado sea de tipo 'company'
    if current_user["user_type"] != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to company users."
        )

    # Obtener el ID de la compañía actual
    company_id = current_user["user_id"]

    # Consultar los templates creados por la compañía
    templates = db.query(EvaluationTemplate).filter(
        EvaluationTemplate.company_id == company_id
    ).all()

    # Validar si no hay templates
    if not templates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No templates found for your company."
        )

    # Retornar la lista de templates en el formato requerido
    return [
        {
            "id": template.id,
            "title": template.title,
            "description": template.description,
            "created_date": template.created_date.isoformat(),
        }
        for template in templates
    ]


@router.post("/assign", status_code=status.HTTP_201_CREATED)
def assign_evaluation_to_employees(
    request: AssignEvaluationRequest,  # Usar el modelo de validación
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Asignar una evaluación a empleados específicos.
    Solo puede ser realizado por usuarios de tipo 'company'.
    """
    # Verificar que el usuario autenticado sea de tipo 'company'
    if current_user["user_type"] != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only companies can assign evaluations."
        )

    # Verificar que la plantilla de evaluación existe y pertenece a la compañía actual
    template = db.query(EvaluationTemplate).filter(
        EvaluationTemplate.id == request.template_id,
        EvaluationTemplate.company_id == current_user["user_id"]
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation template not found or does not belong to your company."
        )

    # Validar y asignar la evaluación a cada empleado
    for employee_id in request.employee_ids:
        # Verificar que el empleado existe y pertenece a la compañía actual
        employee = db.query(Employee).filter(
            Employee.employee_id == employee_id,
            Employee.company_id == current_user["user_id"]
        ).first()

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {employee_id} not found or does not belong to your company."
            )

        # Crear y asignar la evaluación al empleado
        employee_evaluation = EmployeeEvaluation(
            employee_id=employee_id,
            template_id=request.template_id,
            due_date=request.due_date
        )
        db.add(employee_evaluation)

    # Confirmar cambios en la base de datos
    db.commit()

    return {"message": "Evaluations assigned successfully."}


@router.get("/assigned", response_model=List[AssignedEvaluationResponse])
def get_assigned_evaluations(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para obtener la lista de evaluaciones asignadas al empleado autenticado.
    """
    # Verificar que el usuario autenticado es un empleado
    if current_user["user_type"] != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can access their assigned evaluations."
        )

    # Obtener las evaluaciones asignadas al empleado actual desde EmployeeEvaluation
    assigned_evaluations = db.query(EmployeeEvaluation).filter(
        EmployeeEvaluation.employee_id == current_user["user_id"]
    ).all()

    # Construir la respuesta con los campos relevantes
    evaluations = [
        {
            "evaluation_id": assigned_evaluation.id,
            "template_id": assigned_evaluation.template_id, 
            "title": assigned_evaluation.evaluation_template.title,  # Título desde EvaluationTemplate
            "assigned_date": assigned_evaluation.assigned_date.isoformat() if assigned_evaluation.assigned_date else None,
            "due_date": assigned_evaluation.due_date.isoformat() if assigned_evaluation.due_date else None,
            "completion_date": assigned_evaluation.completion_date.isoformat() if assigned_evaluation.completion_date else None,
            "is_completed": assigned_evaluation.is_completed
        }
        for assigned_evaluation in assigned_evaluations
    ]

    if not evaluations:
        return []  # Devuelve una lista vacía si no hay evaluaciones asignadas

    return evaluations

@router.get("/get_evaluation/{employee_evaluation_id}", response_model=EvaluationRequestSchema)
def get_evaluation(
    employee_evaluation_id: int,
    db: Session = Depends(get_db)
):
    """
    Endpoint para obtener una evaluación asignada con sus categorías y preguntas.
    """
    # Verificar si la evaluación asignada existe
    employee_evaluation = db.query(EmployeeEvaluation).join(EvaluationTemplate).filter(
        EmployeeEvaluation.id == employee_evaluation_id
    ).first()

    if not employee_evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluación asignada no encontrada."
        )

    # Obtener todas las categorías con sus preguntas
    categories = db.query(Category).all()
    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron categorías para la evaluación."
        )

    # Serializar la evaluación asignada y sus categorías/preguntas
    evaluation_data = {
        "evaluation_id": employee_evaluation.id,
        "title": employee_evaluation.evaluation_template.title,  # Obtener título desde EvaluationTemplate
        "assigned_date": employee_evaluation.assigned_date.isoformat(),
        "due_date": employee_evaluation.due_date.isoformat() if employee_evaluation.due_date else None,
        "is_completed": employee_evaluation.is_completed,
        "categories": [
            {
                "id": category.id,
                "name": category.name,
                "group": category.group,
                "questions": [
                    {
                        "id": question.id,
                        "text": question.text,
                        "code": question.code
                    }
                    for question in category.questions  # Obtener preguntas relacionadas
                ]
            }
            for category in categories
        ]
    }

    return evaluation_data


@router.get("/incomplete", status_code=status.HTTP_200_OK)
def get_incomplete_evaluations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para obtener todas las evaluaciones asignadas que no han sido completadas.
    Incluye ID, título del template, empleado asignado, fecha de asignación y fecha límite.
    """
    # Verificar que el usuario actual sea de tipo 'company'
    if current_user["user_type"] != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only companies can access this endpoint."
        )

    # Consultar las evaluaciones no completadas para la compañía actual
    incomplete_evaluations = db.query(EmployeeEvaluation).join(EvaluationTemplate).filter(
        EvaluationTemplate.company_id == current_user["user_id"],
        EmployeeEvaluation.is_completed == False  # Filtrar las evaluaciones no completadas
    ).all()

    if not incomplete_evaluations:
        return []  # Devolver una lista vacía si no hay evaluaciones no completadas

    # Construir la respuesta con los campos solicitados
    evaluations = [
        {
            "evaluation_id": evaluation.id,
            "template_title": evaluation.evaluation_template.title,
            "employee": {
                "id": evaluation.employee.employee_id,
                "name": f"{evaluation.employee.first_name} {evaluation.employee.last_name}"
            },
            "assigned_date": evaluation.assigned_date.isoformat() if evaluation.assigned_date else None,
            "due_date": evaluation.due_date.isoformat() if evaluation.due_date else None
        }
        for evaluation in incomplete_evaluations
    ]

    return evaluations