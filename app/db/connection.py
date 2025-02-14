import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging

load_dotenv()  # Carga variables de entorno desde .env

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_engine():
    try:
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        database = os.getenv("DB_NAME")

        if not all([user, password, host, port, database]):
            raise ValueError("Todas las variables de conexión son requeridas")

        user_encoded = urllib.parse.quote_plus(user)
        password_encoded = urllib.parse.quote_plus(password)
        connection_string = f"postgresql+psycopg2://{user_encoded}:{password_encoded}@{host}:{port}/{database}"
        
        logger.info(f"Intentando conectar a: {host}:{port}/{database}")
        
        engine = create_engine(connection_string)
        with engine.connect() as connection:
            logger.info("✅ Conexión a la base de datos establecida exitosamente")
        
        return engine

    except Exception as e:
        logger.error(f"❌ Error al conectar con la base de datos: {e}")
        raise

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
