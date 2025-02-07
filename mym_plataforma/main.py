from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import jwt
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

# Modificar el modelo para permitir campos opcionales
class UsuarioLogin(BaseModel):
    correo: Optional[str] = None
    contrasena: Optional[str] = None

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
def iniciar_sesion(usuario: UsuarioLogin):
    print("✅ Se recibió una solicitud en /api/v1/auth/iniciar-sesion")  # Mensaje de prueba

    try:
        logger.info(f"Solicitud recibida en /api/v1/auth/iniciar-sesion para el correo: {usuario.correo}")

        # Validar que ambos campos estén presentes
        if not usuario.correo or not usuario.contrasena:
            logger.warning("Faltan datos en la solicitud.")
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "No es posible procesar los datos enviados."})

        usuario_data = verificar_credenciales(usuario.correo, usuario.contrasena)

        if usuario_data is None:
            logger.warning(f"Credenciales incorrectas para el usuario: {usuario.correo}")
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "No es posible procesar los datos enviados."})
        
        if usuario_data == "db_error":
            logger.error("Error en la base de datos durante la autenticación")
            raise HTTPException(status_code=500, detail={"estado": 500, "mensaje": "No es posible conectarse al servidor."})

        token = crear_token_jwt({"sub": usuario_data["correo"], "id": usuario_data["id"]})

        logger.info(f"Autenticación exitosa para el usuario: {usuario.correo}")

        return {
            "data": {
                "usuario": usuario_data,
                "token": token
            },
            "estado": 200,
            "mensaje": "Respuesta procesada correctamente."
        }

    except HTTPException as http_error:
        # Si ya es una excepción HTTP, la dejamos pasar sin modificar
        raise http_error

    except Exception as e:
        logger.error(f"Error inesperado en iniciar_sesion: {e}")
        raise HTTPException(status_code=500, detail={"estado": 500, "mensaje": "No es posible conectarse al servidor."})




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
def obtener_codigo(
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
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado.")
            raise HTTPException(status_code=401, detail={"message": "Token inválido"})
        except jwt.InvalidTokenError:
            logger.warning("Token inválido.")
            raise HTTPException(status_code=401, detail={"message": "Token inválido"})

        session = SessionLocal()

        # Verificar si el usuario existe en la base de datos
        query = text("SELECT id FROM USUARIOS WHERE correo = :correo AND estado = '1'")
        usuario = session.execute(query, {"correo": request.correo}).fetchone()

        if not usuario:
            logger.warning(f"No se encontró un usuario activo con el correo: {request.correo}")
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "No es posible procesar los datos enviados."})

        # Generar código aleatorio de 6 caracteres
        codigo = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

        # Establecer tiempo de expiración (2 minutos desde ahora)
        expiracion = datetime.utcnow() + timedelta(minutes=2)

        # Guardar el código en texto plano (sin hash)
        update_query = text("""
            UPDATE USUARIOS 
            SET codigo_recuperacion = :codigo, codigo_expiracion = :expiracion 
            WHERE correo = :correo
        """)
        session.execute(update_query, {"codigo": codigo, "expiracion": expiracion, "correo": request.correo})
        session.commit()

        logger.info(f"Código de recuperación generado para {request.correo}: {codigo}")

        return {
            "data": {"codigo_para_pruebas": codigo},  # 🔹 SOLO PARA PRUEBAS
            "estado": 200,
            "mensaje": "Código de recuperación enviado correctamente."
        }

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos: {e}")
        raise HTTPException(status_code=500, detail={"estado": 500, "mensaje": "No es posible conectarse al servidor."})

    finally:
        if session:
            session.close()
            logger.info("Sesión de base de datos cerrada.")

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
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado.")
            raise HTTPException(status_code=401, detail={"message": "Token inválido"})
        except jwt.InvalidTokenError:
            logger.warning("Token inválido.")
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
            logger.warning(f"Usuario con correo {request.correo} no encontrado o inactivo.")
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "No es posible procesar los datos enviados."})

        # Verificar si el código ha expirado
        if usuario.codigo_expiracion and datetime.utcnow() > usuario.codigo_expiracion:
            logger.warning(f"Código expirado para {request.correo}")
            raise HTTPException(status_code=422, detail={"estado": 422, "mensaje": "Código de recuperación expirado."})

        # Verificar que el código ingresado es correcto (SIN HASH)
        if usuario.codigo_recuperacion != request.codigo:
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
            logger.info("Sesión de base de datos cerrada.")





