from sqlalchemy.orm import Session
from app.models import Category, Question
from app.database import SessionLocal

def populate_autoliderazgo_data():
    db = SessionLocal()
    
    # Dimensiones y sus preguntas
    autoliderazgo_data = {
        "Estrategias de Comportamiento": {
            "group": "E1",
            "questions": [
                ("Escribo metas específicas para mi propio desempeño.", "Auto_10"),
                ("Establezco metas específicas para mi propio desempeño.", "Auto_6"),
                ("Pienso en las metas que pretendo alcanzar en el futuro.", "Auto_5"),
                ("Trabajo hacia metas específicas que me he fijado.", "Auto_3"),
                ("Cuando he completado con éxito una tarea, a menudo me recompenso con algo que me gusta.", "Auto_14"),
                ("Tiendo a ser duro conmigo mismo en mi forma de pensar cuando no he hecho bien una tarea.", "Auto_7"),
                ("Me aseguro de hacer un seguimiento de lo bien que me está yendo en el trabajo/estudio.", "Auto_4"),
                ("Utilizo notas escritas para recordarme a mí mismo lo que necesito lograr.", "Auto_8"),
                ("Utilizo recordatorios concretos (Ej., Notas y listas) para ayudarme a concentrarme en las cosas que quiero lograr.", "Auto_13"),
            ]
        },
        "Estrategias de Recompensa": {
            "group": "E2",
            "questions": [
                ("Intento rodearme de los objetos y las personas que resaltan mis comportamientos deseables.", "Auto_15"),
                ("Cuando tengo una opción, trato de hacer mi trabajo de la manera que disfruto, en lugar de tratar simplemente de superarlo.", "Auto_16"),
                ("Busco actividades en mi trabajo que disfruto hacer.", "Auto_17"),
            ]
        },
        "Estrategias de Pensamiento Constructivo": {
            "group": "E3",
            "questions": [
                ("Me visualizo realizando una tarea con éxito antes de realizarla.", "Auto_1"),
                ("Me visualizo a propósito, superando los desafíos que enfrento.", "Auto_2"),
                ("Pienso en mis propias creencias y suposiciones cada vez que encuentro una situación difícil.", "Auto_9"),
                ("Cuando me encuentro en situaciones difíciles, a veces hablo conmigo mismo (en voz alta o mentalmente) para ayudarme a superarlo.", "Auto_11"),
                ("Expreso y evalúo abiertamente mis propias suposiciones.", "Auto_12"),
                ("Pienso y evalúo las creencias y suposiciones que tengo.", "Auto_18"),
                ("Pienso en mis propias creencias y suposiciones cada vez que encuentro una situación difícil.", "Auto_19"),
            ]
        }
    }

    try:
        for category_name, category_data in autoliderazgo_data.items():
            # Crear o obtener la categoría
            category = Category(name=category_name, group=category_data["group"])
            db.add(category)
            db.commit()
            db.refresh(category)
            
            # Crear preguntas para la categoría
            for question_text, question_code in category_data["questions"]:
                question = Question(text=question_text, category_id=category.id, code=question_code)
                db.add(question)
            
            db.commit()
        
        print("Datos de Autoliderazgo insertados correctamente.")
    
    except Exception as e:
        print("Error al insertar datos de Autoliderazgo:", e)
        db.rollback()
    
    finally:
        db.close()


def populate_desempeno_data():
    db = SessionLocal()
    
    # Dimensiones y sus preguntas para Desempeño
    desempeno_data = {
        "Desempeño de Tarea": {
            "group": "D1",
            "questions": [
                ("Me las arreglé para planificar mi trabajo para que se hiciera a tiempo.", "Des_1"),
                ("Mi planeación fue óptima.", "Des_2"),
                ("Tuve la oportunidad de priorizar los problemas principales de los secundarios.", "Des_3"),
                ("Pude realizar bien mi trabajo con un mínimo tiempo y esfuerzo.", "Des_4"),
            ]
        },
        "Desempeño Contextual": {
            "group": "D2",
            "questions": [
                ("Asumí responsabilidades adicionales.", "Des_5"),
                ("Yo mismo comencé nuevas tareas cuando terminé las anteriores.", "Des_6"),
                ("Asumí una tarea de trabajo desafiante cuando estaba disponible.", "Des_7"),
                ("Trabajé para mantener actualizado mi conocimiento laboral.", "Des_8"),
                ("Trabajé para mantener mis actividades laborales actualizadas.", "Des_9"),
                ("Me ocurrieron soluciones creativas para nuevos problemas.", "Des_10"),
                ("Seguí buscando nuevos retos para mi trabajo.", "Des_11"),
                ("Participé activamente en reuniones de trabajo.", "Des_12"),
            ]
        },
        "Desempeño Contraproducente": {
            "group": "D3",
            "questions": [
                ("Me quejé de asuntos sin importancia en el trabajo.", "Des_13"),
                ("Hice los problemas más grandes de lo que estaban.", "Des_14"),
                ("Me concentré en los aspectos negativos de una situación laboral, en lugar de los aspectos positivos.", "Des_15"),
                ("Hablé con colegas sobre los aspectos negativos de mi trabajo.", "Des_16"),
                ("Hablé con personas ajenas a la organización sobre los aspectos negativos de mi trabajo.", "Des_17"),
            ]
        }
    }

    try:
        for category_name, category_data in desempeno_data.items():
            # Crear o obtener la categoría
            category = Category(name=category_name, group=category_data["group"])
            db.add(category)
            db.commit()
            db.refresh(category)
            
            # Crear preguntas para la categoría
            for question_text, question_code in category_data["questions"]:
                question = Question(text=question_text, code=question_code, category_id=category.id)
                db.add(question)
            
            db.commit()
        
        print("Datos de Desempeño insertados correctamente.")
    
    except Exception as e:
        print("Error al insertar datos de Desempeño:", e)
        db.rollback()
    
    finally:
        db.close()

def populate_apoyo_organizacional_data():
    db = SessionLocal()
    
    # Dimensiones y sus preguntas para Apoyo Organizacional
    apoyo_organizacional_data = {
        "Apoyo Organizacional": {
            "group": "A1",
            "questions": [
                ("La organización tiene en cuenta mis objetivos y valores.", "Apoyo_1"),
                ("Tengo ayuda completa de la organización cuando se presenta algún problema.", "Apoyo_2"),
                ("La organización está dispuesta a darme soporte para realizar mejor mi trabajo.", "Apoyo_3"),
                ("La organización intenta que mi trabajo sea lo más interesante posible.", "Apoyo_4"),
                ("La organización tiene en cuenta mis opiniones.", "Apoyo_5"),
                ("Si la organización obtuviera mayores ganancias consideraría aumentar mi salario.", "Apoyo_6"),
            ]
        }
    }

    try:
        for category_name, category_data in apoyo_organizacional_data.items():
            # Crear o obtener la categoría
            category = Category(name=category_name, group=category_data["group"])
            db.add(category)
            db.commit()
            db.refresh(category)
            
            # Crear preguntas para la categoría
            for question_text, question_code in category_data["questions"]:
                question = Question(text=question_text, code=question_code, category_id=category.id)
                db.add(question)
            
            db.commit()
        
        print("Datos de Apoyo Organizacional insertados correctamente.")
    
    except Exception as e:
        print("Error al insertar datos de Apoyo Organizacional:", e)
        db.rollback()
    
    finally:
        db.close()

# Ejecutar el script
if __name__ == "__main__":
    populate_desempeno_data()
    populate_apoyo_organizacional_data()
    populate_autoliderazgo_data()
