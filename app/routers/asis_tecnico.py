from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.connection import SessionLocal
import logging
from datetime import datetime
import os


router = APIRouter(prefix="/api/v1")
security = HTTPBearer()

# Configurar el logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import json

def json_serial(obj):
    """Función para convertir `date` y `datetime` a string en JSON"""
    if isinstance(obj, (datetime.date, datetime.datetime)):  # Soporta `date` y `datetime`
        return obj.isoformat()  # Convierte a `YYYY-MM-DD` o `YYYY-MM-DDTHH:MM:SS`
    raise TypeError(f"Type {type(obj)} not serializable")

@router.post("/reclamo-queja/{codigo}/solicitud-conformidad")
def registrar_conformidad(
    codigo: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    
    # Validar token y obtener usuario
    query_token = text("SELECT usuarios_id FROM postventa.usuarios_tokens WHERE token = :token")
    result_token = db.execute(query_token, {"token": token}).fetchone()
    if not result_token:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido", "data": []})
    
    usuarios_id = result_token[0]
    query_usuario = text("SELECT tipo_usuarios_id, nombre_completo FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()
    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado", "data": []})
    
    nombre_completo = result_usuario[1]  # Obtener el nombre del usuario
    
    # Obtener el id del formulario a partir del código
    query_formulario = text("SELECT id FROM postventa.formularios WHERE codigo = :codigo")
    result_formulario = db.execute(query_formulario, {"codigo": codigo}).fetchone()
    if not result_formulario:
        return JSONResponse(status_code=404, content={"estado": 404, "mensaje": "Formulario no encontrado", "data": []})
    
    formulario_id = result_formulario[0]
    creado_el = datetime.now()
    
    # Insertar en la tabla conformidad
    query_insert = text("""
        INSERT INTO postventa.conformidad (formulario_id, usuarios_id, creado_el)
        VALUES (:formulario_id, :usuarios_id, :creado_el)
    """)
    db.execute(query_insert, {"formulario_id": formulario_id, "usuarios_id": usuarios_id, "creado_el": creado_el})
    db.commit()
    
    creado_el_formateado = creado_el.strftime("%d/%m/%Y %I:%M %p")
    
    return JSONResponse(status_code=200, content={
        "estado": 200,
        "mensaje": "Se ha guardado correctamente",
        "data": {
            "creado_el": creado_el_formateado,
            "creado_por": nombre_completo
        }
    })

@router.post("/reclamo-queja/{codigo}/evaluacion-en-proceso")
def crear_evaluacion(
    codigo: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    # 🔐 Validar token y obtener usuario
    query_token = text("SELECT usuarios_id FROM postventa.usuarios_tokens WHERE token = :token")
    result_token = db.execute(query_token, {"token": token}).fetchone()
    if not result_token:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido", "data": []})

    usuarios_id = result_token[0]
    query_usuario = text("SELECT tipo_usuarios_id, nombre_completo FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()
    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado", "data": []})

    nombre_completo = result_usuario[1]  # Obtener el nombre del usuario

    # Obtener el ID del formulario usando el código
    query_formulario = text("SELECT id FROM postventa.formularios WHERE codigo = :codigo")
    result_formulario = db.execute(query_formulario, {"codigo": codigo}).fetchone()
    if not result_formulario:
        return JSONResponse(status_code=404, content={"estado": 404, "mensaje": "Formulario no encontrado", "data": []})

    formularios_id = result_formulario[0]

    # Insertar la evaluación sin laudo (para obtener el ID generado)
    query_insert = text("""
        INSERT INTO postventa.evaluaciones (formularios_id, creado_el, creado_por, modificado_el, modificado_por)
        VALUES (:formularios_id, :creado_el, :creado_por, :modificado_el, :modificado_por)
        RETURNING id, creado_el
    """)
    result_insert = db.execute(query_insert, {
        "formularios_id": formularios_id,
        "creado_el": datetime.now(),
        "creado_por": nombre_completo,
        "modificado_el": datetime.now(),
        "modificado_por": nombre_completo
    })
    evaluacion = result_insert.fetchone()
    db.commit()

    evaluacion_id = evaluacion[0]  # ID de la evaluación recién creada
    creado_el = evaluacion[1]

    # Formatear el laudo correctamente
    laudo = f"M&M2025-{str(evaluacion_id).zfill(4)}"

    # Actualizar la evaluación con el laudo generado
    query_update_laudo = text("UPDATE postventa.evaluaciones SET laudo = :laudo WHERE id = :id")
    db.execute(query_update_laudo, {"laudo": laudo, "id": evaluacion_id})
    db.commit()

    # Respuesta
    return JSONResponse(
        status_code=200,
        content={
            "estado": 200,
            "mensaje": "Se ha guardado correctamente",
            "data": {
                "laudo_codigo": laudo,
                "laudo_fecha": creado_el.strftime("%d/%m/%Y"),
                "producto_recibido": [],
                "producto_evaluacion": [],
                "causa": "",
                "resultado_id": None,
                "conclusion": "",
                "recomendacion": "",
                "creado_el": creado_el.strftime("%d/%m/%Y %I:%M %p"),
                "creado_por": nombre_completo,
                "modificado_el": creado_el.strftime("%d/%m/%Y %I:%M %p"),
                "modificado_por": nombre_completo
            }
        }
    )