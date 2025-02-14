from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import jwt
import requests
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.db_connection_simulacion import get_engine
from sqlalchemy import text
import logging
from typing import Optional
import random
import string
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware

# Configuración de FastAPI
app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5174', 'http://localhost:5173' 'http://localhost:5175'],  # Permite todas las fuentes, puedes especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos HTTP
    allow_headers=["*"],  # Permite todos los encabezados
)
# Configurar el contexto de encriptación (CORREGIDO bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cargar la clave secreta desde variables de entorno
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Definir sesión de la base de datos
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class UsuarioLogin(BaseModel):
    usuario: Optional[str] = None
    contrasena: Optional[str] = None

# Modelo de solicitud para registrar usuario
class RegistrarUsuarioRequest(BaseModel):
    tipo_usuarios_id: int
    tipo_documentos_id: int
    documento: str
    nombre_completo: str
    correo: EmailStr
    contrasena: str
    recontrasena: str


# Seguridad para obtener el token del header
security = HTTPBearer()

# Esquema de datos para cambiar contraseña
class CambiarContrasenaRequest(BaseModel):
    usuarios_id: Optional[int] = None
    contrasena: Optional[str] = None
    recontrasena: Optional[str] = None

# Modelo de solicitud para obtener el código
class ObtenerCodigoRequest(BaseModel):
    correo: str

from pydantic import BaseModel


# Modelo para recuperar la contraseña
class RecuperarContrasenaRequest(BaseModel):
    correo: str
    codigo: str
    contrasena: str
    recontrasena: str

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

#SIMULACIÓN DE LA API DE LOGIN DE LOS TRBAJADORES MYM
# Modelo de solicitud para la API simulada
class LoginSimuladoRequest(BaseModel):
    cia: str
    password: str
    username: str

# Endpoint para la API simulada
@app.post("/logindb2/loginv2")
def login_simulado(request: LoginSimuladoRequest):
    """
    API simulada para autenticación que responde con datos simulados sin conectarse a la base de datos.
    """

    # Simulación de credenciales correctas
    USUARIO_CORRECTO = "MAX123"
    PASSWORD_CORRECTO = "123456"
    CIA_CORRECTO = "14"

    if request.username == USUARIO_CORRECTO and request.password == PASSWORD_CORRECTO and request.cia == CIA_CORRECTO:
        # Simulación de respuesta correcta
        return {
            "usuario": request.username,
            "mensaje": "Usuario correcto",
            "status": 200,
            "data": {
                "coduser": request.username,
                "expiresDate": "1969-12-31 20:33:45",
                "accesos": "MMCBR001,MMFEWEBSVR,MM023,MM035,MM042,MM078,MM102,MM143,MM172,MM196,MM205,MM214,MM21401,MM215,MM221,MM256,MM2754,MM341,MM405,MM457,MM4571,MM548,MM549,MM638,MM891,MM892"
            }
        }
    
    # Simulación de acceso inválido
    return {
        "usuario": request.username,
        "mensaje": "Usuario o contraseña incorrecta",
        "status": 401,
        "data": None
    }


