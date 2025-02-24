from fastapi import FastAPI, HTTPException, Depends, Request, Query
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
import re
from dotenv import load_dotenv
load_dotenv()
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
    allow_origins=['http://localhost:5174', 'http://localhost:5173','http://localhost:5175'],  # Permite todas las fuentes, puedes especificar dominios específicos
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
    USUARIO_CORRECTO = "MSOLANO"
    PASSWORD_CORRECTO = "123456"
    CIA_CORRECTO = "10"

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

#Api de Simulación para buscar la data de un documento
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import re

app = FastAPI()

# Datos simulados predefinidos en una estructura de diccionario
simulated_docs = {
    "BOLETA": {
        "B001-12345678": {
            "documento": "B001-12345678",
            "tipo_documento": "BOLETA",
            "fechaventa": "2025-01-01",
            "nrointerno": "B1234",
            "guiaremision": "G001-12345678",
            "condicionpago": "Contado",
            "vendedor": "Vendedor Boleta",
            "departamento": "Lima",
            "sucursal": "Sucursal Boleta",
            "almacen": "Almacén Boleta",
            "transportista": "Transportista Boleta"
        }
    },
    "FACTURA": {
        "F001-87654321": {
            "documento": "F001-87654321",
            "tipo_documento": "FACTURA",
            "fechaventa": "2025-01-02",
            "nrointerno": "F5678",
            "guiaremision": "G001-87654321",
            "condicionpago": "Crédito",
            "vendedor": "Vendedor Factura",
            "departamento": "Arequipa",
            "sucursal": "Sucursal Factura",
            "almacen": "Almacén Factura",
            "transportista": "Transportista Factura"
        }
    },
    "NOTA DE VENTA": {
        "1234567": {
            "documento": "1234567",
            "tipo_documento": "NOTA DE VENTA",
            "fechaventa": "2025-01-03",
            "nrointerno": "NV9012",
            "guiaremision": "G001-1234567",
            "condicionpago": "Efectivo",
            "vendedor": "Vendedor NV",
            "departamento": "Cusco",
            "sucursal": "Sucursal NV",
            "almacen": "Almacén NV",
            "transportista": "Transportista NV"
        }
    }
}

@app.get("/api/v1/buscar-documento")
async def buscar_documento(
    tipo_documento: int = Query(..., description="1 para BOLETA, 2 para FACTURA, 3 para NOTA DE VENTA"),
    serie: Optional[str] = Query("", description="Serie para BOLETA o FACTURA. No se utiliza para NOTA DE VENTA"),
    correlativo: str = Query(...)
):
    """
    Endpoint para buscar documento con datos simulados.

    Validaciones:
      - BOLETA (tipo_documento=1) y FACTURA (tipo_documento=2):
          * La serie es obligatoria y debe contener exactamente 4 caracteres alfanuméricos.
          * El correlativo debe contener exactamente 8 dígitos.
      - NOTA DE VENTA (tipo_documento=3):
          * No se debe enviar serie (debe estar vacío).
          * El correlativo debe contener exactamente 7 dígitos.
    """
    # Validación para BOLETA y FACTURA
    if tipo_documento in [1, 2]:
        if not serie or not re.fullmatch(r'[A-Za-z0-9]{4}', serie.strip()):
            return JSONResponse(
                status_code=422,
                content={
                    "errores": {
                        "serie": [
                            "Para BOLETA o FACTURA, la serie es obligatoria y debe contener exactamente 4 caracteres alfanuméricos."
                        ]
                    },
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )
        if not re.fullmatch(r'\d{8}', correlativo):
            return JSONResponse(
                status_code=422,
                content={
                    "errores": {
                        "correlativo": [
                            "Para BOLETA o FACTURA, el correlativo debe contener exactamente 8 dígitos."
                        ]
                    },
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )
        key = f"{serie}-{correlativo}"
        doc_type = "BOLETA" if tipo_documento == 1 else "FACTURA"
    # Validación para NOTA DE VENTA
    elif tipo_documento == 3:
        if serie and serie.strip() != "":
            return JSONResponse(
                status_code=422,
                content={
                    "errores": {
                        "serie": [
                            "Para NOTA DE VENTA, no se debe enviar serie."
                        ]
                    },
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )
        if not re.fullmatch(r'\d{7}', correlativo):
            return JSONResponse(
                status_code=422,
                content={
                    "errores": {
                        "correlativo": [
                            "Para NOTA DE VENTA, el correlativo debe contener exactamente 7 dígitos."
                        ]
                    },
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )
        key = correlativo
        doc_type = "NOTA DE VENTA"
    else:
        return JSONResponse(
            status_code=422,
            content={
                "errores": {
                    "tipo_documento": [
                        "Tipo de documento no reconocido. Use 1 para BOLETA, 2 para FACTURA o 3 para NOTA DE VENTA."
                    ]
                },
                "estado": 422,
                "mensaje": "No es posible procesar los datos enviados."
            }
        )

    # Buscar en la data simulada según el tipo de documento y la clave construida
    documento_info = simulated_docs.get(doc_type, {}).get(key)
    if not documento_info:
        return JSONResponse(
            status_code=422,
            content={
                "errores": {
                    "documento": [
                        f"No existe documento con { 'serie y correlativo' if tipo_documento in [1,2] else 'correlativo' } especificado."
                    ]
                },
                "estado": 422,
                "mensaje": "No es posible procesar los datos enviados."
            }
        )

    return JSONResponse(content={"data": documento_info})



