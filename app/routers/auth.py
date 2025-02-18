from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError
from sqlalchemy import text
from datetime import datetime, timedelta
import random, string, jwt
import requests

from app.models.usuario import (
    UsuarioLogin,
    RegistrarUsuarioRequest,
    CambiarContrasenaRequest,
    ObtenerCodigoRequest,
    RecuperarContrasenaRequest
)
from app.db.connection import SessionLocal
from app.services import auth_service, email_service
from app.utils.security import create_access_token, verify_password, hash_password
from app.config import JWT_SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_HOURS
from app.utils.logger import logger

router = APIRouter(prefix="/api/v1/auth")
security = HTTPBearer()

@router.post("/iniciar-sesion")
async def iniciar_sesion(request: Request):
    try:
        data = await request.json()
        errores = {}

        empresa_id = data.get("empresa_id")
        usuario_input = data.get("usuario")
        contrasena = data.get("contrasena")

        if not usuario_input:
            errores["usuario"] = ["El campo es obligatorio."]
        if not contrasena:
            errores["contrasena"] = ["El campo es obligatorio."]
        if errores:
            return JSONResponse(
                status_code=422,
                content={
                    "errores": errores,
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )

        if not empresa_id:
            usuario_validado = auth_service.verificar_credenciales(usuario_input, contrasena)
            if usuario_validado is None:
                return JSONResponse(
                    status_code=422,
                    content={
                        "errores": {
                            "usuario": ["El usuario o la contraseña son incorrectos."],
                            "contrasena": ["El usuario o la contraseña son incorrectos."]
                        },
                        "estado": 422,
                        "mensaje": "No es posible procesar los datos enviados."
                    }
                )
            if usuario_validado == "db_error":
                return JSONResponse(
                    status_code=500,
                    content={"estado": 500, "mensaje": "No es posible conectarse al servidor."}
                )

            token = create_access_token({"sub": usuario_validado["usuario"], "id": usuario_validado["id"]})
            creado_el = datetime.utcnow()
            expira_el = creado_el + timedelta(hours=TOKEN_EXPIRE_HOURS)

            session = SessionLocal()
            insert_token_query = text("""
                INSERT INTO POSTVENTA.USUARIOS_TOKENS (usuarios_id, token, creado_el, expira_el)
                VALUES (:usuarios_id, :token, :creado_el, :expira_el)
            """)
            session.execute(insert_token_query, {
                "usuarios_id": usuario_validado["id"],
                "token": token,
                "creado_el": creado_el,
                "expira_el": expira_el
            })
            session.commit()
            session.close()

            return JSONResponse(
                status_code=200,
                content={
                    "data": {"usuario": usuario_validado, "token": token},
                    "estado": 200,
                    "mensaje": "Respuesta procesada correctamente."
                }
            )

        else:
            # Autenticación remota
            payload_remote = {
                "cia": empresa_id,
                "username": usuario_input,
                "password": contrasena
            }
            remote_api_url = "http://127.0.0.1:8002/logindb2/loginv2"
            remote_response = requests.post(remote_api_url, json=payload_remote)
            remote_data = remote_response.json()
            
            if remote_data.get("status") == 200 and remote_data.get("mensaje") == "Usuario correcto":
                usuario_validado = auth_service.verificar_credenciales_empresa(usuario_input, empresa_id)
                if usuario_validado is None:
                    usuario_validado = auth_service.insertar_usuario(usuario_input, contrasena, empresa_id)
                    if usuario_validado == "db_error":
                        return JSONResponse(
                            status_code=500,
                            content={"estado": 500, "mensaje": "Error al insertar el usuario en la BD."}
                        )
                token = create_access_token({"sub": usuario_validado["usuario"], "id": usuario_validado["id"]})
                creado_el = datetime.utcnow()
                expira_el = creado_el + timedelta(hours=TOKEN_EXPIRE_HOURS)

                session = SessionLocal()
                insert_token_query = text("""
                    INSERT INTO POSTVENTA.USUARIOS_TOKENS (usuarios_id, token, creado_el, expira_el)
                    VALUES (:usuarios_id, :token, :creado_el, :expira_el)
                """)
                session.execute(insert_token_query, {
                    "usuarios_id": usuario_validado["id"],
                    "token": token,
                    "creado_el": creado_el,
                    "expira_el": expira_el
                })
                session.commit()
                session.close()

                return JSONResponse(
                    status_code=200,
                    content={
                        "data": {"usuario": usuario_validado, "token": token},
                        "estado": 200,
                        "mensaje": "Respuesta procesada correctamente."
                    }
                )
            else:
                return JSONResponse(
                    status_code=401,
                    content={
                        "estado": 401,
                        "mensaje": "Usuario o contraseña incorrecta",
                        "data": None
                    }
                )

    except Exception as e:
        logger.error(f"Error inesperado en iniciar_sesion: {e}")
        return JSONResponse(
            status_code=500,
            content={"estado": 500, "mensaje": "No es posible conectarse al servidor."}
        )

@router.post("/registrar")
def registrar_usuario(request: RegistrarUsuarioRequest):
    session = SessionLocal()
    try:
        errores = {}

        # Validación de campos obligatorios
        if not request.documento.strip():
            errores["documento"] = ["El documento es obligatorio."]
        if not request.nombre_completo.strip():
            errores["nombre_completo"] = ["El nombre completo es obligatorio."]
        if not request.correo.strip():
            errores["correo"] = ["El correo es obligatorio."]
        if not request.contrasena.strip():
            errores["contrasena"] = ["La contraseña es obligatoria."]
        if not request.recontrasena.strip():
            errores["recontrasena"] = ["Debe repetir la contraseña."]

        if errores:
            return JSONResponse(
                status_code=422,
                content={
                    "errores": errores,
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )

        query = text("SELECT id FROM POSTVENTA.USUARIOS WHERE documento = :documento")
        usuario_existente = session.execute(query, {"documento": request.documento}).fetchone()

        if usuario_existente:
            errores["documento"] = ["El documento ya está registrado."]

        correo_normalizado = request.correo.lower()
        query = text("SELECT id FROM POSTVENTA.USUARIOS WHERE correo = :correo")
        correo_existente = session.execute(query, {"correo": correo_normalizado}).fetchone()

        if correo_existente:
            errores["correo"] = ["El correo ya está registrado."]

        if request.contrasena != request.recontrasena:
            errores["contrasena"] = ["Las contraseñas no coinciden."]

        if errores:
            return JSONResponse(
                status_code=422,
                content={
                    "errores": errores,
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )

        contrasena_hash = hash_password(request.contrasena)

        insert_query = text("""
            INSERT INTO POSTVENTA.USUARIOS (tipo_usuarios_id, tipo_documentos_id, documento, usuario, nombre_completo, correo, contrasena, estado, creado_el)
            VALUES (:tipo_usuarios_id, :tipo_documentos_id, :documento, :documento, :nombre_completo, :correo, :contrasena, '1', :creado_el)
        """)
        session.execute(insert_query, {
            "tipo_usuarios_id": request.tipo_usuarios_id,
            "tipo_documentos_id": request.tipo_documentos_id,
            "documento": request.documento,
            "nombre_completo": request.nombre_completo,
            "correo": correo_normalizado,
            "contrasena": contrasena_hash,
            "creado_el": datetime.utcnow()
        })
        session.commit()

        return {
            "estado": 200,
            "mensaje": "Cliente registrado"
        }

    except Exception as e:
        session.rollback()
        return JSONResponse(
            status_code=500,
            content={"estado": 500, "mensaje": "No es posible conectarse al servidor."}
        )
    finally:
        session.close()


@router.get("/cerrar-sesion")
def cerrar_sesion(credenciales: HTTPAuthorizationCredentials = Depends(security)):
    token = credenciales.credentials
    logger.info("Intención de cerrar sesión con token recibido.")

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id = payload.get("id")
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado.")
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido"})
    except jwt.InvalidTokenError:
        logger.warning("Token inválido.")
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido"})

    if not auth_service.eliminar_token_de_bd(token, usuario_id):
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido"})

    return JSONResponse(status_code=200, content={"estado": 200, "mensaje": "Sesión cerrada exitosamente"})


@router.post("/cambiar-contrasena")
def cambiar_contrasena(
    request: CambiarContrasenaRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    session = SessionLocal()
    try:
        token = credentials.credentials
       
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            usuario_id_token = payload.get("id")
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado.")
            return JSONResponse(status_code=401, content={"message": "Token inválido"})
        except jwt.InvalidTokenError:
            logger.warning("Token inválido.")
            return JSONResponse(status_code=401, content={"message": "Token inválido"})
        logger.info(f"Solicitud de cambio de contraseña para usuario ID: {usuario_id_token}")
        query = text("SELECT id FROM POSTVENTA.USUARIOS_TOKENS WHERE usuarios_id = :usuarios_id AND token = :token")
        token_registrado = session.execute(query, {"usuarios_id": usuario_id_token, "token": token}).fetchone()
        if not token_registrado:
            logger.warning("Token inválido o ya eliminado.")
            return JSONResponse(status_code=401, content={"message": "Token inválido"})
        query = text("SELECT id, contrasena FROM POSTVENTA.USUARIOS WHERE id = :id AND estado = '1'")
        usuario = session.execute(query, {"id": usuario_id_token}).fetchone()
        if not usuario:
            logger.warning(f"Usuario con ID {usuario_id_token} no encontrado o inactivo.")
            return JSONResponse(status_code=422, content={"estado": 422, "mensaje": "No es posible procesar los datos enviados."})
        if not verify_password(request.contrasena, usuario[1]):
            logger.warning("La contraseña actual no es válida.")
            return JSONResponse(status_code=422, content={
                "errores": {
                    "contrasena": ["Contraseña incorrecta"]
                },
                "estado": 422,
                "mensaje": "No es posible procesar los datos enviados."
            })
        if request.contrasena == request.recontrasena:
            logger.warning("La nueva contraseña no puede ser igual a la actual.")
            return JSONResponse(status_code=422, content={
                "errores": {
                    "message": ["Las contraseñas no pueden ser iguales"]
                },
                "estado": 422,
                "mensaje": "No es posible procesar los datos enviados."
            })
        nueva_contrasena_hash = hash_password(request.recontrasena)
        update_query = text("UPDATE POSTVENTA.USUARIOS SET contrasena = :nueva_contrasena WHERE id = :id")
        session.execute(update_query, {"nueva_contrasena": nueva_contrasena_hash, "id": usuario_id_token})
        session.commit()
        if not auth_service.eliminar_token_de_bd(token, usuario_id_token):
            return JSONResponse(status_code=500, content={"estado": 500, "mensaje": "No es posible conectarse al servidor."})
        return {
            "data": {},
            "estado": 200,
            "mensaje": "Contraseña cambiada correctamente y sesión cerrada."
        }
    except ValidationError as e:
        errores = {}
        for error in e.errors():
            campo = error["loc"][0]
            # Siempre establecer "Campo obligatorio." para cualquier error de campo faltante
            errores.setdefault(campo, []).append("Campo obligatorio.")
        return JSONResponse(status_code=422, content={
            "errores": errores,
            "estado": 422,
            "mensaje": "No es posible procesar los datos enviados."
        })
    except Exception as e:
        session.rollback()
        logger.error(f"Error inesperado en cambiar_contrasena: {e}")
        return JSONResponse(status_code=500, content={"estado": 500, "mensaje": "No es posible conectarse al servidor."})
    finally:
        session.close()

@router.post("/obtener-codigo")
async def obtener_codigo(request: ObtenerCodigoRequest):
    session = SessionLocal()
    try:
        logger.info(f"Solicitud de obtención de código para el correo: {request.correo}")
        
        query = text("SELECT id FROM POSTVENTA.USUARIOS WHERE correo = :correo AND estado = '1'")
        usuario = session.execute(query, {"correo": request.correo}).fetchone()
        
        if not usuario:
            return JSONResponse(
                status_code=422,
                content={
                    "errores": {
                        "correo": ["Correo inválido."]
                    },
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )

        codigo = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        codigo_hash = hash_password(codigo)
        expiracion = datetime.utcnow() + timedelta(minutes=5)
        
        update_query = text("""
            UPDATE POSTVENTA.USUARIOS 
            SET codigo_recuperacion = :codigo_hash, codigo_expiracion = :expiracion 
            WHERE correo = :correo
        """)
        result = session.execute(update_query, {"codigo_hash": codigo_hash, "expiracion": expiracion, "correo": request.correo})
        session.commit()
        
        if result.rowcount == 0:
            logger.error(f"❌ No se pudo actualizar el código de recuperación en la BD para {request.correo}")
            return JSONResponse(
                status_code=500,
                content={
                    "estado": 500,
                    "mensaje": "Error al guardar el código en la BD."
                }
            )
        
        # Verificar si el envío del correo fue exitoso
        if not await email_service.enviar_correo(request.correo, codigo):
            return JSONResponse(
                status_code=500,
                content={
                    "estado": 500,
                    "mensaje": "Error al enviar el correo electrónico."
                }
            )
            
        logger.info(f"✅ Código de recuperación enviado a {request.correo}")
        
        return JSONResponse(
            status_code=200,
            content={
                "data": {},
                "estado": 200,
                "mensaje": "Código de recuperación enviado correctamente."
            }
        )
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error inesperado: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "estado": 500,
                "mensaje": "No es posible conectarse al servidor."
            }
        )
    finally:
        session.close()

@router.post("/recuperar-contrasena")
def recuperar_contrasena(request: RecuperarContrasenaRequest):
    session = SessionLocal()
    errores = {}

    try:
        logger.info(f"Solicitud de recuperación de contraseña para el correo: {request.correo}")

        # Validaciones iniciales
        if not request.codigo.strip():
            errores["codigo"] = ["Campo obligatorio"]

        query = text("""
            SELECT id, codigo_recuperacion, codigo_expiracion 
            FROM POSTVENTA.USUARIOS 
            WHERE correo = :correo AND estado = '1'
        """)
        usuario = session.execute(query, {"correo": request.correo}).fetchone()

        if usuario is None:
            errores["correo"] = ["Correo inválido."]

        if errores:  # Si ya hay errores, retornarlos sin continuar
            return JSONResponse(
                status_code=422,
                content={
                    "errores": errores,
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )

        usuario_dict = dict(zip(["id", "codigo_recuperacion", "codigo_expiracion"], usuario))

        # Validar código de recuperación
        if not usuario_dict.get("codigo_recuperacion"):
            errores["codigo"] = ["Código de recuperación incorrecto."]

        if usuario_dict.get("codigo_expiracion") and datetime.utcnow() > usuario_dict["codigo_expiracion"]:
            errores["codigo"] = ["Código de recuperación incorrecto."]

        if not verify_password(request.codigo, usuario_dict["codigo_recuperacion"]):
            errores["codigo"] = ["Código de recuperación incorrecto."]

        # Verificar si las contraseñas coinciden
        if request.contrasena != request.recontrasena:
            errores["recontrasena"] = ["Las contraseñas no coinciden"]

        if errores:  # Si hay errores, los retornamos todos juntos
            return JSONResponse(
                status_code=422,
                content={
                    "errores": errores,
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )

        # Actualizar la contraseña
        nueva_contrasena_hash = hash_password(request.recontrasena)
        update_query = text("""
            UPDATE POSTVENTA.USUARIOS 
            SET contrasena = :nueva_contrasena, codigo_recuperacion = NULL, codigo_expiracion = NULL 
            WHERE correo = :correo
        """)
        session.execute(update_query, {"nueva_contrasena": nueva_contrasena_hash, "correo": request.correo})
        session.commit()

        logger.info(f"Contraseña cambiada exitosamente para {request.correo}")
        return JSONResponse(
            status_code=200,
            content={
                "data": {},
                "estado": 200,
                "mensaje": "Contraseña cambiada correctamente."
            }
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Error de BD: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "estado": 500,
                "mensaje": "No es posible conectarse al servidor."
            }
        )
    finally:
        session.close()


