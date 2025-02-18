import os
import urllib.parse
from sqlalchemy import create_engine
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
import os

dotenv_path = r"C:\Users\ING ANGEL\Desktop\Proyecto_MyM_2025\PLATAFORMA_POST_VENTA_BACKEND\.env"
load_dotenv(dotenv_path, override=True)

print("DB_USER:", os.getenv("DB_USER"))
print("DB_PASSWORD:", os.getenv("DB_PASSWORD"))
print("DB_HOST:", os.getenv("DB_HOST"))
print("DB_PORT:", os.getenv("DB_PORT"))
print("DB_NAME:", os.getenv("DB_NAME"))

def get_engine():
    try:
        # Obtener variables de entorno
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        database = os.getenv("DB_NAME")

        # Validar que todas las variables estén presentes
        if not all([user, password, host, port, database]):
            raise ValueError("Todas las variables de conexión son requeridas")

        # Codificar credenciales
        user_encoded = urllib.parse.quote_plus(user)
        password_encoded = urllib.parse.quote_plus(password)

        # Construir cadena de conexión
        connection_string = f"postgresql+psycopg2://{user_encoded}:{password_encoded}@{host}:{port}/{database}"
        
        logger.info(f"Intentando conectar a: {host}:{port}/{database}")
        
        # Crear motor de base de datos
        engine = create_engine(connection_string)
        
        # Probar conexión
        with engine.connect() as connection:
            logger.info("✅ Conexión a la base de datos establecida exitosamente")
        
        return engine

    except Exception as e:
        logger.error(f"❌ Error al conectar con la base de datos: {e}")
        raise