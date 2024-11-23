from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

# Configurar la URL para SQLite (desarrollo)
# SQLALCHEMY_DATABASE_URL = "sqlite:///adap.db"

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener la URL de la base de datos desde la variable de entorno
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Verificar si la URL de la base de datos está configurada
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables")

# Crear la conexión a la base de datos
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()