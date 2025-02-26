from sqlalchemy import text
from app.db.connection import SessionLocal
from app.utils.security import verify_password, hash_password
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from app.utils.logger import logger
from passlib.context import CryptContext
from jose import jwt, JWTError
from starlette.responses import JSONResponse
from fastapi import FastAPI, Depends
from app.config import JWT_SECRET_KEY, ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verificar_credenciales(usuario_input: str, contrasena: str):
    session = SessionLocal()
    try:
        query = text("SELECT * FROM POSTVENTA.USUARIOS WHERE usuario = :usuario AND estado = '1'")
        result = session.execute(query, {"usuario": usuario_input})
        usuario = result.mappings().fetchone()
        
        if not usuario:
            logger.warning(f"No se encontró un usuario activo con el usuario: {usuario_input}")
            return None

        usuario_dict = dict(usuario)
        if usuario_dict.get("creado_el"):
            usuario_dict["creado_el"] = usuario_dict["creado_el"].strftime("%Y-%m-%d %H:%M:%S")
        
        if not verify_password(contrasena, usuario_dict["contrasena"]):
            logger.warning(f"Contraseña incorrecta para el usuario con ID: {usuario_dict['id']}")
            return None

        allowed_fields = [
            "id", "tipo_usuarios_id", "nombre_completo", "tipo_documentos_id",
            "documento", "correo", "accesos", "permisos", "creado_el", "usuario"
        ]
        filtered_usuario = {field: usuario_dict.get(field) for field in allowed_fields}
        return filtered_usuario

    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return "db_error"
    finally:
        session.close()
        logger.info("Sesión de base de datos cerrada.")

def verificar_credenciales_empresa(usuario_input: str, empresa_id: str):
    session = SessionLocal()
    try:
        query = text("""
            SELECT * FROM POSTVENTA.USUARIOS 
            WHERE usuario = :usuario 
              AND empresa_id = :empresa_id 
              AND estado = '1'
        """)
        result = session.execute(query, {"usuario": usuario_input, "empresa_id": empresa_id})
        usuario = result.mappings().fetchone()
        
        if not usuario:
            logger.info(f"Usuario {usuario_input} no encontrado para empresa_id {empresa_id}")
            return None

        usuario_dict = dict(usuario)
        if usuario_dict.get("creado_el"):
            usuario_dict["creado_el"] = usuario_dict["creado_el"].strftime("%Y-%m-%d %H:%M:%S")
        
        allowed_fields = [
            "id", "tipo_usuarios_id", "nombre_completo", "tipo_documentos_id",
            "documento", "correo", "accesos", "permisos", "creado_el", "usuario"
        ]
        filtered_usuario = {field: usuario_dict.get(field) for field in allowed_fields}
        return filtered_usuario

    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return "db_error"
    finally:
        session.close()

def insertar_usuario(usuario_input: str, contrasena: str, empresa_id: str):
    session = SessionLocal()
    try:
        hashed_pass = hash_password(contrasena)
        unique_email = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "@" + usuario_input + ".com"
        query = text("""
            INSERT INTO POSTVENTA.USUARIOS 
            (tipo_usuarios_id, tipo_documentos_id, nombre_completo, documento, correo, usuario, contrasena, estado, empresa_id)
            VALUES ('1','1','Usuario MYM','1', :correo, :usuario, :contrasena, '1', :empresa_id)
            RETURNING id
        """)
        result = session.execute(query, {"correo": unique_email, "usuario": usuario_input, "contrasena": hashed_pass, "empresa_id": empresa_id})
        new_id = result.mappings().fetchone()["id"]
        session.commit()

        query_user = text("SELECT * FROM POSTVENTA.USUARIOS WHERE id = :id")
        result = session.execute(query_user, {"id": new_id})
        new_user = result.mappings().fetchone()
        usuario_dict = dict(new_user)
        if usuario_dict.get("creado_el"):
            usuario_dict["creado_el"] = usuario_dict["creado_el"].strftime("%Y-%m-%d %H:%M:%S")
        allowed_fields = [
            "id", "tipo_usuarios_id", "nombre_completo", "tipo_documentos_id",
            "documento", "correo", "accesos", "permisos", "creado_el", "usuario"
        ]
        filtered_usuario = {field: usuario_dict.get(field) for field in allowed_fields}
        return filtered_usuario

    except Exception as e:
        logger.error(f"Error inesperado al insertar usuario: {e}")
        session.rollback()
        return "db_error"
    finally:
        session.close()

def eliminar_token_de_bd(token: str, usuario_id: int):
    session = SessionLocal()
    try:
        query = text("SELECT id FROM POSTVENTA.USUARIOS_TOKENS WHERE usuarios_id = :usuarios_id AND token = :token")
        token_registrado = session.execute(query, {"usuarios_id": usuario_id, "token": token}).fetchone()

        if not token_registrado:
            logger.warning("Token no encontrado en la base de datos.")
            return False

        delete_query = text("DELETE FROM POSTVENTA.USUARIOS_TOKENS WHERE id = :token_id")
        session.execute(delete_query, {"token_id": token_registrado[0]})
        session.commit()
        logger.info("Token eliminado correctamente de la base de datos.")
        return True
    except Exception as e:
        logger.error(f"Error al eliminar token: {e}")
        return False
    finally:
        session.close()

def eliminar_tokens_expirados():
    """Elimina los tokens que han caducado en la base de datos."""
    session = SessionLocal()
    try:
        ahora = datetime.utcnow()
        delete_query = text("""
            DELETE FROM POSTVENTA.USUARIOS_TOKENS 
            WHERE expira_el <= :ahora
        """)
        session.execute(delete_query, {"ahora": ahora})
        session.commit()
        logger.info("Tokens expirados eliminados correctamente.")
    except Exception as e:
        logger.error(f"Error al eliminar tokens expirados: {e}")
    finally:
        session.close()

def verificar_token(token: str) -> int:
    """
    Verifica si el token es válido y devuelve el ID del usuario si es correcto.
    Si el token es inválido o expirado, devuelve None.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id = payload.get("id")
        
        # Verificar si el token aún está almacenado en la base de datos
        session = SessionLocal()
        query = text("SELECT id FROM POSTVENTA.USUARIOS_TOKENS WHERE usuarios_id = :usuarios_id AND token = :token")
        token_registrado = session.execute(query, {"usuarios_id": usuario_id, "token": token}).fetchone()
        session.close()

        if not token_registrado:
            return None  # Token no encontrado en la BD, inválido
        
        return usuario_id  # Token válido

    except jwt.ExpiredSignatureError:
        return None  # Token expirado
    except jwt.InvalidTokenError:
        return None  # Token inválido

# Función para validar token
def validar_token(credenciales: HTTPAuthorizationCredentials = Depends(security)):
    token = credenciales.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # Si el token es válido, se devuelve el payload
    except jwt.ExpiredSignatureError:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido"})
    except jwt.JWTError:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido"})
