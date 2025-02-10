from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from pydantic_settings import BaseSettings
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import jwt
import requests
import os
from .db_connection import get_engine
from sqlalchemy import text
import logging
from typing import Optional
import random
import string
from datetime import datetime, timedelta

# Configuración de FastAPI
app = FastAPI()

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
    correo: Optional[str] = None
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

#Configuración para obtener codigo:
# Cargar configuración desde variables de entorno
class Settings(BaseSettings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool

    class Config:
        env_file = ".env"  # Archivo donde están las credenciales

settings = Settings()

# Configuración de FastMail con SendGrid
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS") == "True",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS") == "True",
    USE_CREDENTIALS=os.getenv("USE_CREDENTIALS") == "True"
)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"
class ObtenerCodigoRequest(BaseSettings):
    correo: str

async def enviar_correo(destinatario, codigo):
    message = MessageSchema(
        subject="Código de Recuperación",
        recipients=[destinatario],
        body=f"Tu código de recuperación es: {codigo}. Este código expira en 5 minutos.",
        subtype="plain"
    )
    try:
        fm = FastMail(settings)
        await fm.send_message(message)
        logging.info("Correo enviado correctamente.")
    except Exception as e:
        logging.error(f"Error enviando correo: {e}")

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def verificar_credenciales(correo: str, contrasena: str):
    try:
        session = SessionLocal()
        # Ejecutar la consulta SQL correctamente con text()
        query = text("SELECT * FROM USUARIOS WHERE correo = :correo AND estado = '1'")
        usuario = session.execute(query, {"correo": correo}).fetchone()
        
        if not usuario:
            logger.warning(f"No se encontró un usuario activo con el correo: {correo}")
            return None

        logger.info(f"Usuario encontrado en la base de datos con ID: {usuario[0]}")

        # Extraer datos del usuario en un diccionario
        usuario_dict = {
            "id": usuario[0],
            "tipo_usuarios_id": usuario[1],
            "nombre_completo": usuario[3],
            "tipo_documentos": usuario[2],
            "documento": usuario[4],
            "correo": usuario[5],
            "accesos": usuario[7],
            "permisos": usuario[8],
            "creado_el": usuario[10].strftime("%Y-%m-%d %H:%M:%S") if usuario[10] else None
        }
        logger.info(f"Datos del usuario extraídos correctamente: {usuario_dict}")

        # Verificar la contraseña con bcrypt (CORREGIDO)
        if not pwd_context.verify(contrasena, usuario[6]):  # usuario[6] es la columna 'contrasena'
            logger.warning(f"Contraseña incorrecta para el usuario con ID: {usuario[0]}")
            return None

        logger.info(f"Usuario autenticado correctamente: {correo}")
        return usuario_dict

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos: {e}")
        return "db_error"

    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return "db_error"

    finally:
        session.close()
        logger.info("Sesión de base de datos cerrada.")


# Función para generar token JWT (CORREGIDO)
def crear_token_jwt(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Endpoint para iniciar sesión
from fastapi import HTTPException

@app.post("/api/v1/auth/iniciar-sesion")
async def iniciar_sesion(request: Request):
    print("✅ Se recibió una solicitud en /api/v1/auth/iniciar-sesion")

    try:
        usuario_data = await request.json()
        errores = []

        # Validar que los campos estén presentes
        correo = usuario_data.get("correo")
        contrasena = usuario_data.get("contrasena")

        if not correo:
            errores.append({"correo": ["El campo es obligatorio."]})

        if not contrasena:
            errores.append({"contrasena": ["El campo es obligatorio."]})

        if errores:
            return JSONResponse(
                status_code=422,
                content={
                    "errores": errores,
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )

        usuario_validado = verificar_credenciales(correo, contrasena)

        if usuario_validado is None:
            return JSONResponse(
                status_code=422,
                content={
                    "errores": [
                        {"correo": ["El correo o la contraseña son incorrectos."]},
                        {"contrasena": ["El correo o la contraseña son incorrectos."]}
                    ],
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )

        if usuario_validado == "db_error":
            return JSONResponse(
                status_code=500,
                content={"estado": 500, "mensaje": "No es posible conectarse al servidor."}
            )

        # Generar token JWT
        token = crear_token_jwt({"sub": usuario_validado["correo"], "id": usuario_validado["id"]})

        return JSONResponse(
            status_code=200,
            content={
                "data": {
                    "usuario": usuario_validado,
                    "token": token
                },
                "estado": 200,
                "mensaje": "Respuesta procesada correctamente."
            }
        )

    except Exception as e:
        logging.error(f"Error inesperado en iniciar_sesion: {e}")
        return JSONResponse(
            status_code=500,
            content={"estado": 500, "mensaje": "No es posible conectarse al servidor."}
        )

@app.post("/api/v1/auth/registrar")
def registrar_usuario(request: RegistrarUsuarioRequest):
    session: Optional[Session] = None

    try:
        session = SessionLocal()
        
        errores = []

        # Verificar si el documento ya existe
        query = text("SELECT id FROM USUARIOS WHERE documento = :documento")
        usuario_existente = session.execute(query, {"documento": request.documento}).fetchone()

        if usuario_existente:
            errores.append({"documento": ["El documento ya está registrado."]})

        # Verificar si el correo ya existe
        query = text("SELECT id FROM USUARIOS WHERE correo = :correo")
        correo_existente = session.execute(query, {"correo": request.correo}).fetchone()

        if correo_existente:
            errores.append({"correo": ["El correo ya está registrado."]})

        # Verificar que las contraseñas coincidan
        if request.contrasena != request.recontrasena:
            errores.append({"contrasena": ["Las contraseñas no coinciden."]})

        if errores:
            return JSONResponse(
                status_code=422,
                content={
                    "errores": errores,
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )

        # Hashear la contraseña antes de guardarla
        contrasena_hash = pwd_context.hash(request.contrasena)

        # Insertar nuevo usuario en la base de datos
        insert_query = text("""
            INSERT INTO USUARIOS (tipo_usuarios_id, tipo_documentos_id, documento, nombre_completo, correo, contrasena, estado, creado_el)
            VALUES (:tipo_usuarios_id, :tipo_documentos_id, :documento, :nombre_completo, :correo, :contrasena, '1', :creado_el)
        """)
        session.execute(insert_query, {
            "tipo_usuarios_id": request.tipo_usuarios_id,
            "tipo_documentos_id": request.tipo_documentos_id,
            "documento": request.documento,
            "nombre_completo": request.nombre_completo,
            "correo": request.correo,
            "contrasena": contrasena_hash,
            "creado_el": datetime.utcnow()
        })
        session.commit()

        return {
            "estado": 200,
            "mensaje": "Cliente registrado"
        }

    except SQLAlchemyError as e:
        if session:
            session.rollback()
        return JSONResponse(
            status_code=500,
            content={"estado": 500, "mensaje": "No es posible conectarse al servidor."}
        )

    finally:
        if session:
            session.close()


@app.get("/api/v1/auth/cerrar-sesion")
def cerrar_sesion():
    logger.info("Sesión cerrada correctamente.")
    return {
        "estado": 200,
        "mensaje": "Sesión cerrada correctamente."
    }

@app.post("/api/v1/auth/cambiar-contrasena")
def cambiar_contrasena(
    request: CambiarContrasenaRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    session: Optional[Session] = None  # Inicializar sesión para evitar el UnboundLocalError

    try:
        logger.info(f"Solicitud de cambio de contraseña para usuario ID: {request.usuarios_id}")

        # Validar que todos los campos estén presentes
        if not request.usuarios_id or not request.contrasena or not request.recontrasena:
            logger.warning("Faltan datos en la solicitud de cambio de contraseña.")
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "No es posible procesar los datos enviados."})

        # Decodificar el token y verificar si es válido
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            usuario_id_token = payload.get("id")
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado.")
            raise HTTPException(status_code=401, detail={"message": "Token inválido"})
        except jwt.InvalidTokenError:
            logger.warning("Token inválido.")
            raise HTTPException(status_code=401, detail={"message": "Token inválido"})
        except Exception as e:
            logger.error(f"Error en la decodificación del token: {e}")
            raise HTTPException(status_code=401, detail={"message": "Token inválido"})

        # Validar que el token pertenece al usuario que intenta cambiar la contraseña
        if usuario_id_token != request.usuarios_id:
            logger.warning("Intento de cambiar contraseña con un token no autorizado.")
            raise HTTPException(status_code=401, detail={"message": "Token inválido"})

        session = SessionLocal()

        # Verificar si el usuario existe y obtener su contraseña actual
        query = text("SELECT id, contrasena FROM USUARIOS WHERE id = :id AND estado = '1'")
        usuario = session.execute(query, {"id": request.usuarios_id}).fetchone()

        if not usuario:
            logger.warning(f"Usuario con ID {request.usuarios_id} no encontrado o inactivo.")
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "No es posible procesar los datos enviados."})

        # Verificar que la contraseña ingresada es la actual
        if not pwd_context.verify(request.contrasena, usuario[1]):  # usuario[1] es la contraseña almacenada
            logger.warning("La contraseña actual no es válida.")
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "No es posible procesar los datos enviados."})

        # Verificar que la nueva contraseña es diferente a la actual
        if request.contrasena == request.recontrasena:
            logger.warning("La nueva contraseña no puede ser igual a la actual.")
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "La nueva contraseña no puede ser igual a la anterior."})

        # Hashear la nueva contraseña
        nueva_contrasena_hash = pwd_context.hash(request.recontrasena)

        # Actualizar la contraseña en la base de datos
        update_query = text("UPDATE USUARIOS SET contrasena = :nueva_contrasena WHERE id = :id")
        session.execute(update_query, {"nueva_contrasena": nueva_contrasena_hash, "id": request.usuarios_id})
        session.commit()

        logger.info(f"Contraseña cambiada exitosamente para usuario ID: {request.usuarios_id}")

        return {
            "data": {},
            "estado": 200,
            "mensaje": "Respuesta procesada correctamente."
        }

    except SQLAlchemyError as e:
        if session:
            session.rollback()
        logger.error(f"Error de base de datos: {e}")
        raise HTTPException(status_code=500, detail={"estado": 500, "mensaje": "No es posible conectarse al servidor."})

    except HTTPException as http_error:
        # Dejar pasar los errores HTTP sin capturarlos como 500
        raise http_error

    except Exception as e:
        logger.error(f"Error inesperado en cambiar_contrasena: {e}")
        raise HTTPException(status_code=500, detail={"estado": 500, "mensaje": "No es posible conectarse al servidor."})

    finally:
        if session:
            session.close()
            logger.info("Sesión de base de datos cerrada.")

@app.post("/api/v1/auth/obtener-codigo")
async def obtener_codigo(
    request: ObtenerCodigoRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    session: Optional[Session] = None

    try:
        logger.info(f"Solicitud de obtención de código para el correo: {request.correo}")

        # Validar el token antes de continuar
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            usuario_id_token = payload.get("id")
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise HTTPException(status_code=401, detail={"message": "Token inválido"})

        # Iniciar la sesión de base de datos
        session = SessionLocal()

        # Verificar si el usuario existe en la base de datos
        query = text("SELECT id FROM USUARIOS WHERE correo = :correo AND estado = '1'")
        usuario = session.execute(query, {"correo": request.correo}).fetchone()

        if not usuario:
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "No es posible procesar los datos enviados."})

        # Generar código aleatorio de 6 caracteres
        codigo = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

        # Hashear el código antes de guardarlo en la base de datos
        codigo_hash = pwd_context.hash(codigo)

        # Establecer tiempo de expiración (5 minutos desde ahora)
        expiracion = datetime.utcnow() + timedelta(minutes=5)

        # Guardar el código hasheado en la base de datos
        update_query = text("""
            UPDATE USUARIOS 
            SET codigo_recuperacion = :codigo_hash, codigo_expiracion = :expiracion 
            WHERE correo = :correo
        """)
        session.execute(update_query, {"codigo_hash": codigo_hash, "expiracion": expiracion, "correo": request.correo})
        session.commit()

        # Enviar el código por correo con SendGrid y FastMail
        message = MessageSchema(
            subject="Código de Recuperación",
            recipients=[request.correo],
            body=f"Tu código de recuperación es: {codigo}. Este código expira en 5 minutos.",
            subtype="plain"
        )

        try:
            fm = FastMail(conf)
            await fm.send_message(message)
            logger.info(f"✅ Código de recuperación enviado a {request.correo}")
        except Exception as e:
            logger.error(f"❌ Error al enviar correo con SendGrid: {e}")
            raise HTTPException(status_code=500, detail={"estado": 500, "mensaje": "No se pudo enviar el correo."})

        return {
            "data": {},
            "estado": 200,
            "mensaje": "Respuesta procesada correctamente."
        }

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos: {e}")
        raise HTTPException(status_code=500, detail={"estado": 500, "mensaje": "No es posible conectarse al servidor."})

    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail={"estado": 500, "mensaje": "Ocurrió un error inesperado."})

    finally:
        if session:
            session.close()
            logger.info("🔹 Sesión de base de datos cerrada.")



@app.post("/api/v1/auth/recuperar-contrasena")
def recuperar_contrasena(
    request: RecuperarContrasenaRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    session: Optional[Session] = None  

    try:
        logger.info(f"Solicitud de recuperación de contraseña para el correo: {request.correo}")

        # Validación del token
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            usuario_id_token = payload.get("id")
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise HTTPException(status_code=401, detail={"message": "Token inválido"})

        session = SessionLocal()

        # Buscar usuario y verificar código de recuperación
        query = text("""
            SELECT id, codigo_recuperacion, codigo_expiracion 
            FROM USUARIOS 
            WHERE correo = :correo AND estado = '1'
        """)
        usuario = session.execute(query, {"correo": request.correo}).fetchone()

        if not usuario:
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "No es posible procesar los datos enviados."})

        # Verificar si el código ha expirado
        if usuario.codigo_expiracion and datetime.utcnow() > usuario.codigo_expiracion:
            logger.warning(f"Código expirado para {request.correo}")
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "Código de recuperación expirado."})

        # Verificar que el código ingresado es correcto con el hash
        if not pwd_context.verify(request.codigo, usuario.codigo_recuperacion):
            logger.warning(f"Código incorrecto para {request.correo}")
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "Código de recuperación incorrecto."})

        # Verificar que las contraseñas coincidan
        if request.contrasena != request.recontrasena:
            logger.warning("Las contraseñas no coinciden.")
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "Las contraseñas no coinciden."})

        # Hashear la nueva contraseña
        nueva_contrasena_hash = pwd_context.hash(request.recontrasena)

        # Actualizar la contraseña y eliminar el código de recuperación
        update_query = text("""
            UPDATE USUARIOS 
            SET contrasena = :nueva_contrasena, codigo_recuperacion = NULL, codigo_expiracion = NULL 
            WHERE correo = :correo
        """)
        session.execute(update_query, {"nueva_contrasena": nueva_contrasena_hash, "correo": request.correo})
        session.commit()

        logger.info(f"Contraseña cambiada exitosamente para {request.correo}")

        return {
            "data": {},
            "estado": 200,
            "mensaje": "Contraseña cambiada correctamente."
        }

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos: {e}")
        raise HTTPException(status_code=500, detail={"estado": 500, "mensaje": "No es posible conectarse al servidor."})

    finally:
        if session:
            session.close()


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
    USUARIO_CORRECTO = "TUUSUARIO"
    PASSWORD_CORRECTO = "TUPASSWORD"
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






