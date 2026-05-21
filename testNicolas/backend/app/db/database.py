import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

# Obtener la URL de Neon.tech
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# Dependencia para que FastAPI obtenga y cierre la conexión limpiamente
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()