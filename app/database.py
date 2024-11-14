from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# URL (direccion) del archivo de base de datos SQLite
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/todoappdatabase"
SQLALCHEMY_DATABASE_URL = "sqlite:///adap.db"


# Crear la conexión a la base de datos
# check_same_thread: Si se establece en False, se asegura que la conexión se realice en un 
#                    mismo hilo de ejecución que el que ejecuta la consulta. Esto puede 
#                    mejorar el rendimiento en algunos casos, pero puede causar problemas 
#                    en otros. Por defecto, se establece en True.
# engine = create_engine(SQLALCHEMY_DATABASE_URL )(
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}) 

  
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()