from app.database import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Float
from sqlalchemy.orm import relationship


class Company(Base):
    __tablename__ = 'companies'

    company_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    company_name = Column(String, unique=True, nullable=False)
    phone_number = Column(String)
    is_active = Column(Boolean, default=True)
    country_of_residence = Column(String, nullable=True)  # Nuevo campo para el país

    employees = relationship("Employee", back_populates="company")
    evaluations = relationship("Evaluation", back_populates="company")  # Relación con Evaluation


class Employee(Base):
    __tablename__ = 'employees'

    employee_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)  # Correo electrónico
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Información personal
    first_name = Column(String, nullable=False)  # Nombres
    last_name = Column(String, nullable=False)  # Apellidos
    nationality = Column(String, nullable=True)  # Nacionalidad
    document_id = Column(String, unique=False, nullable=True)  # Documento de identidad
    phone_number = Column(String, nullable=True)  # Número telefónico
    gender = Column(String, nullable=True)  # Género (Ej. "Masculino", "Femenino", "Otro")
    birth_date = Column(String, nullable=True)  # Fecha de nacimiento

    # Información de residencia
    city_of_residence = Column(String, nullable=True)  # Ciudad de residencia
    country_of_residence = Column(String, nullable=True)  # País de residencia

    # Información profesional
    profession = Column(String, nullable=True)  # Profesión
    position = Column(String, nullable=True)  # Cargo actual

    # Relación con la empresa
    company_id = Column(Integer, ForeignKey('companies.company_id'))
    company = relationship("Company", back_populates="employees")

    # Información de emprendimiento
    is_entrepreneur = Column(Boolean, default=False)  # Es emprendedor
    entrepreneurship_name = Column(String, nullable=True)  # Nombre del emprendimiento (si aplica)

    # Evaluaciones
    is_active = Column(Boolean, default=True)
    evaluations = relationship("Evaluation", back_populates="employee")  # Relación con Evaluaciones


class Category(Base):
    __tablename__ = 'categories'
    # ID único para la categoría
    id = Column(Integer, primary_key=True, index=True)
    # Nombre descriptivo de la categoría (Ej., "Estrategias de Comportamiento")
    name = Column(String, nullable=False)
    # Grupo de la categoría (Ej., E1, E2, E3 para diferenciar subgrupos)
    group = Column(String, nullable=False)
    # Relación con las preguntas
    questions = relationship("Question", back_populates="category")
    def __repr__(self):
        return f"<Category(name={self.name}, group={self.group})>"


class Question(Base):
    __tablename__ = 'questions'
    # ID único para cada pregunta
    id = Column(Integer, primary_key=True, index=True)
    # Texto de la pregunta
    text = Column(String, nullable=False)
    # Código único de la pregunta (Auto_X, Des_X, Apoyo_X)
    code = Column(String, unique=True, nullable=False)
    # ID de la categoría a la que pertenece la pregunta
    category_id = Column(Integer, ForeignKey('categories.id'))
    # Relación con la categoría
    category = relationship("Category", back_populates="questions")

    def __repr__(self):
        return f"<Question(code={self.code}, text={self.text})>"


class Evaluation(Base):
    __tablename__ = 'evaluations'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'))
    company_id = Column(Integer, ForeignKey('companies.company_id'))

    employee = relationship("Employee", back_populates="evaluations")
    company = relationship("Company", back_populates="evaluations")
    responses = relationship("Response", back_populates="evaluation")
    calculation_result = relationship("CalculationResult", back_populates="evaluation", uselist=False)


class Response(Base):
    __tablename__ = 'responses'
    id = Column(Integer, primary_key=True)
    evaluation_id = Column(Integer, ForeignKey('evaluations.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    score = Column(Integer)  # Score between 1 to 5
    evaluation = relationship("Evaluation", back_populates="responses")
    question = relationship("Question")


class CalculationResult(Base):
    __tablename__ = 'calculation_results'
    
    # ID de la tabla
    id = Column(Integer, primary_key=True)
    evaluation_id = Column(Integer, ForeignKey('evaluations.id'))
    
    # Subfactores para Autoliderazgo
    F1 = Column(Float)  # Auto_10, Auto_6, Auto_5, Auto_3
    F2 = Column(Float)  # Auto_14
    F3 = Column(Float)  # Auto_4
    F4 = Column(Float)  # Auto_7
    F5 = Column(Float)  # Auto_8, Auto_13

    # Factores de Autoliderazgo
    E1 = Column(Float)  # Estrategias de Comportamiento
    F6 = Column(Float)  # Auto_16, Auto_17, Auto_15
    E2 = Column(Float)  # Estrategias de Recompensa
    F7 = Column(Float)  # Auto_1, Auto_11, Auto_12
    F8 = Column(Float)  # Auto_2
    F9 = Column(Float)  # Auto_9, Auto_18, Auto_19
    E3 = Column(Float)  # Estrategias de Pensamiento Constructivo
    overall_selfleadership = Column(Float)  # Total Autoliderazgo

    # Subfactores para Desempeño
    D1 = Column(Float)  # Desempeño de Tarea
    D2 = Column(Float)  # Desempeño Contextual
    D3 = Column(Float)  # Desempeño de Conducta Contraproducente
    overall_performance_score = Column(Float)  # Total Desempeño Individual

    # Apoyo Organizacional Percibido
    organizational_support_score = Column(Float)  # Apoyo Organizacional Percibido
    
    # Relación con Evaluation
    evaluation = relationship("Evaluation", back_populates="calculation_result")

# Adding back_populates in Evaluation
Evaluation.calculation_result = relationship("CalculationResult", back_populates="evaluation", uselist=False)