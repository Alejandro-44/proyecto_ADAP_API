# standard packages
from typing import Annotated, List
# third-party packages
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
# local packages
from app.models import CalculationResult, Category, Company, Employee, Evaluation, Question, Response
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
        from_atributes = True


class CategorySchema(BaseModel):
    id: int
    name: str
    group: str
    questions: List[QuestionSchema]

    class Config:
        from_atributes = True


class EvaluationRequestSchema(BaseModel):
    evaluation_id: int
    categories: List[CategorySchema]

    class Config:
        from_atributes = True


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


# Funciones auxiliares de cálculo

def get_response_score_by_code(evaluation_id: int, code: str, db: Session) -> int:
    # Buscar la respuesta que coincide con el código de la pregunta en la evaluación especificada
    response = (
        db.query(Response)
        .join(Question)
        .filter(Response.evaluation_id == evaluation_id)
        .filter(Question.code == code)
        .first()
    )
    
    # Retornar el puntaje si se encuentra la respuesta, o 0 si no existe
    return response.score if response else 0

def calculate_autoliderazgo(evaluation_id: int, db: Session):
    # Obtener los puntajes de las respuestas de Autoliderazgo para cada subfactor
    F1 = sum(get_response_score_by_code(evaluation_id, code, db) * weight for code, weight in [
        ("Auto_10", .2003),
        ("Auto_6", .1918),
        ("Auto_5", .1306),
        ("Auto_3", .124)
    ])
    F2 = get_response_score_by_code(evaluation_id, "Auto_14", db) * .0137
    F3 = get_response_score_by_code(evaluation_id, "Auto_4", db) * .0020
    F4 = get_response_score_by_code(evaluation_id, "Auto_7", db) * .1666
    F5 = sum(get_response_score_by_code(evaluation_id, code, db) * weight for code, weight in [
        ("Auto_8", 8.67),
        ("Auto_13", 10.36)
    ])
    
    E1 = F1 + F2 + F3 + F4 + F5

    F6 = sum(get_response_score_by_code(evaluation_id, code, db) * weight for code, weight in [
        ("Auto_16", .3726),
        ("Auto_17", .3551),
        ("Auto_15", .2721)
    ])

    E2 = F6

    F7 = sum(get_response_score_by_code(evaluation_id, code, db) * weight for code, weight in [
        ("Auto_1", .1846),
        ("Auto_11", .2267),
        ("Auto_12", .1903)
    ])
    F8 = get_response_score_by_code(evaluation_id, "Auto_2", db) * .0641

    F9 = sum(get_response_score_by_code(evaluation_id, code, db) * weight for code, weight in [
        ("Auto_9", .1846),
        ("Auto_18", .2267),
        ("Auto_19", .0892)
    ])
    E3 = F7 + F8 + F9

    overall_selfleadership = E1 * .3172 + E2 * .3155 + E3 * .3672

    return F1, F2, F3, F4, F5, E1, F6, E2, F7, F8, F9, E3, overall_selfleadership


def calculate_desempeno(evaluation_id: int, db: Session):
    # Calcular los subfactores de Desempeño

    D1 = sum(get_response_score_by_code(evaluation_id, code, db) * weight for code, weight in [
        ("Des_2", .327),
        ("Des_3", .271),
        ("Des_1", .238),
        ("Des_4", .162)
    ])

    D2 = sum(get_response_score_by_code(evaluation_id, code, db) * weight for code, weight in [
        ("Des_8", .1524),
        ("Des_9", .175),
        ("Des_7", .1301),
        ("Des_11", .1272),
        ("Des_10", .1223),
        ("Des_12", .1048),
        ("Des_6", .1045),
        ("Des_5", .834),
    ])

    D3 = sum(get_response_score_by_code(evaluation_id, code, db) * weight for code, weight in [
        ("Des_13", .1882),
        ("Des_14", .2051),
        ("Des_15", .2252),
        ("Des_16", .2029),
        ("Des_17", .1774),
    ])

    overall_performance_score = D1 * .4817 + D2 * .3936 + D3 * .1246

    return D1, D2, D3, overall_performance_score



def calculate_apoyo_organizacional(evaluation_id: int, db: Session):
    # Calcular Apoyo Organizacional Percibido
    organizational_support_score = sum(get_response_score_by_code(evaluation_id, code, db) * weight for code, weight in [
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
    Endpoint para subir las respuestas de una evaluación y calcular los resultados derivados.
    """
    # Verificar si la evaluación existe
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_data.evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada.")
    # Procesar y almacenar cada respuesta
    for answer in evaluation_data.answers:
        # Verificar si la pregunta existe
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail=f"Pregunta con ID {answer.question_id} no encontrada.")
        # Crear una instancia de Response para cada respuesta
        response = Response(
            evaluation_id=evaluation.id,
            question_id=answer.question_id,
            score=answer.score
        )
        # Agregar la respuesta a la sesión
        db.add(response)

    # Confirmar los cambios en la base de datos
    db.commit()
    # Calcular los resultados basados en las respuestas
    F1, F2, F3, F4, F5, E1, F6, E2, F7, F8, F9, E3, overall_selfleadership = calculate_autoliderazgo(evaluation.id, db)
    D1, D2, D3, overall_performance_score = calculate_desempeno(evaluation.id, db)
    organizational_support_score = calculate_apoyo_organizacional(evaluation.id, db)
    # Guardar los resultados en la tabla CalculationResult
    calculation_result = CalculationResult(
        evaluation_id=evaluation.id,
        F1=F1, F2=F2, F3=F3, F4=F4, F5=F5,
        E1=E1, F6=F6, E2=E2, F7=F7, F8=F8, F9=F9,
        E3=E3, overall_selfleadership=overall_selfleadership,
        D1=D1, D2=D2, D3=D3, overall_performance_score=overall_performance_score,
        organizational_support_score=organizational_support_score
    )
    # Agregar el resultado calculado a la sesión y confirmar los cambios
    db.add(calculation_result)
    db.commit()

    return {"message": "Respuestas de la evaluación guardadas exitosamente."}


@router.get("/{evaluation_id}", response_model=EvaluationRequestSchema)
def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db)
):
    """
    Endpoint para obtener una evaluación con todas sus categorías y preguntas.
    """
    # Verificar si la evaluación existe
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada.")

    # Obtener todas las categorías
    categories = db.query(Category).all()
    if not categories:
        raise HTTPException(status_code=404, detail="No se encontraron categorías para la evaluación.")
    
    # Serializar la evaluación y sus categorías
    evaluation_data = {
        "evaluation_id": evaluation.id,
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
                    for question in category.questions
                ]
            }
            for category in categories
        ]
    }

    return evaluation_data

@router.post("/assign", status_code=status.HTTP_201_CREATED)
async def assign_evaluation(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para asignar una evaluación a un empleado específico. Solo las compañías pueden realizar esta acción.
    """
    # Verificar que el usuario autenticado es una compañía
    if current_user["user_type"] != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only companies can assign evaluations"
        )

    # Verificar que el empleado existe y pertenece a la compañía de la compañía autenticada
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado.")
    
    # Verificar que el empleado pertenece a la misma compañía que el usuario autenticado
    if employee.company_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only assign evaluations to employees in your own company"
        )

    # Crear una nueva evaluación asignada al empleado y la compañía autenticada
    new_evaluation = Evaluation(
        employee_id=employee_id,
        company_id=current_user["user_id"]
    )
    
    db.add(new_evaluation)
    db.commit()
    db.refresh(new_evaluation)

    return {
        "message": "Evaluación asignada exitosamente.",
        "evaluation_id": new_evaluation.id,
        "employee_id": employee_id,
        "company_id": current_user["user_id"]
    }
