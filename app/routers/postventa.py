from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.connection import SessionLocal
from app.models.postventa import EnTiendaUpdate, ComentarioCreate, CierreFormulario
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

@router.post("/reclamo-queja/{codigo}/en-tienda")
def actualizar_en_tienda(
    codigo: str,
    body: EnTiendaUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    # Validar token y obtener usuarios_id
    query_token = text("SELECT usuarios_id FROM postventa.usuarios_tokens WHERE token = :token")
    result_token = db.execute(query_token, {"token": token}).fetchone()

    if not result_token:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido", "data": []})

    usuarios_id = result_token[0]

    # Obtener tipo_usuarios_id del usuario
    query_usuario = text("SELECT tipo_usuarios_id FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()

    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado", "data": []})

    # Actualizar en_tienda en la tabla postventa.trazabilidad
    try:
        update_query = text("""
            UPDATE postventa.formularios
            SET en_tienda = :en_tienda
            WHERE codigo = :codigo
        """)
        db.execute(update_query, {"en_tienda": body.en_tienda, "codigo": codigo})
        db.commit()
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"estado": 500, "mensaje": "Error al actualizar", "data": []})

    return JSONResponse(
        status_code=200,
        content={
            "data": [],
            "estado": 200,
            "mensaje": "Se ha actualizado correctamente"
        }
    )

UPLOADS_GUIA = "uploads/guia"
os.makedirs(UPLOADS_GUIA, exist_ok=True)

@router.post("/reclamo-queja/{codigo}/guiado")
async def registrar_guia(
    codigo: str,
    fecha_llegada: str = Form(...),
    archivo: UploadFile = File(...),
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

    query_usuario = text("SELECT tipo_usuarios_id FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()
    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado", "data": []})

    # Obtener ID del formulario
    query_form = text("""
        SELECT id, (nombres || ' ' || apellidos) AS nombres_apellidos
        FROM postventa.formularios
        WHERE codigo = :codigo
    """)
    formulario = db.execute(query_form, {"codigo": codigo}).fetchone()
    if not formulario:
        return JSONResponse(status_code=404, content={"estado": 404, "mensaje": "Código no encontrado", "data": []})

    formularios_id = formulario[0]
    nombres_apellidos = formulario[1]

    # Guardar el archivo
    extension = archivo.filename.split(".")[-1]
    filename = f"{codigo}_guia_{datetime.now().strftime('%Y%m%d')}.{extension}"
    file_path = os.path.join(UPLOADS_GUIA, filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await archivo.read())

    url_archivo = f"http://localhost:8001/uploads/guia/{filename}"

    try:
        insert_query = text("""
            INSERT INTO postventa.guia (formularios_id, fecha_llegada, url_archivo, tipo_archivo)
            VALUES (:formularios_id, :fecha_llegada, :url_archivo, :tipo_archivo)
            RETURNING creado_el
        """)
        created = db.execute(insert_query, {
            "formularios_id": formularios_id,
            "fecha_llegada": fecha_llegada,
            "url_archivo": url_archivo,
            "tipo_archivo": extension.upper()
        }).fetchone()
        db.commit()

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"estado": 500, "mensaje": "Error al registrar la guía", "data": []})

    return JSONResponse(
        status_code=200,
        content={
            "estado": 200,
            "mensaje": "Guía registrada correctamente",
            "data": [{
                "rq_id": codigo,
                "fecha_llegada": fecha_llegada,
                "archivo": url_archivo,
                "creado_el": created[0].strftime("%Y-%m-%d %H:%M:%S"),
                "creado_por": nombres_apellidos
            }]
        }
    )

@router.post("/reclamo-queja/{codigo}/comentario")
def registrar_comentario(
    codigo: str,
    body: ComentarioCreate,
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

    query_usuario = text("SELECT tipo_usuarios_id FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()
    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado", "data": []})

    # Buscar el formulario por el código
    query_formulario = text("SELECT id, nombres, apellidos FROM postventa.formularios WHERE codigo = :codigo")
    formulario = db.execute(query_formulario, {"codigo": codigo}).fetchone()
    if not formulario:
        return JSONResponse(status_code=404, content={"estado": 404, "mensaje": "Formulario no encontrado", "data": []})

    formulario_id, nombres, apellidos = formulario

    # Validar que el comentario no esté vacío
    if not body.comentario or not body.comentario.strip():
        return JSONResponse(
            status_code=422,
            content={
                "errores": {
                    "comentario": ["Este campo es requerido"]
                },
                "estado": 422,
                "mensaje": "No es posible procesar los datos enviados."
            }
        )

    # Registrar el comentario
    insertar = text("""
        INSERT INTO postventa.comentarios (formulario_id, fecha, comentario)
        VALUES (:formulario_id, :fecha, :comentario)
    """)
    db.execute(insertar, {
        "formulario_id": formulario_id,
        "fecha": datetime.now(),
        "comentario": body.comentario
    })
    db.commit()

    # Obtener todos los comentarios de ese formulario
    query_comentarios = text("""
        SELECT c.id, f.codigo AS rq_id, c.comentario, f.nombres, f.apellidos, c.fecha
        FROM postventa.comentarios c
        INNER JOIN postventa.formularios f ON f.id = c.formulario_id
        WHERE c.formulario_id = :formulario_id
        ORDER BY c.fecha ASC
    """)
    comentarios = db.execute(query_comentarios, {"formulario_id": formulario_id}).fetchall()

    data = []
    for c in comentarios:
        data.append({
            "id": c.id,
            "rq_id": c.rq_id,
            "comentario": c.comentario,
            "creado_por": f"{c.nombres} {c.apellidos}",
            "creado_el": c.fecha.strftime("%d/%m/%Y %I:%M %p")
        })

    return JSONResponse(status_code=200, content={
        "estado": 200,
        "mensaje": "Se ha guardado correctamente",
        "data": data
    })

@router.post("/reclamo-queja/{codigo}/cierre")
def registrar_cierre(
    codigo: str,
    body: CierreFormulario,
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

    # 🔎 Verificar tipo de usuario
    query_usuario = text("SELECT tipo_usuarios_id FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()
    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado", "data": []})

    # 🔎 Buscar el formulario por código
    query_form = text("SELECT id FROM postventa.formularios WHERE codigo = :codigo")
    result_form = db.execute(query_form, {"codigo": codigo}).fetchone()
    if not result_form:
        return JSONResponse(status_code=404, content={"estado": 404, "mensaje": "Formulario no encontrado", "data": []})
    formulario_id = result_form[0]

    # ✅ Actualizar estado del formulario a 10 y guardar el origen
    update_form = text("""
        UPDATE postventa.formularios 
        SET estado_id = 10, origen_id = :origen
        WHERE id = :formulario_id
    """)
    db.execute(update_form, {"origen": body.origen, "formulario_id": formulario_id})

    # ✅ Insertar trazabilidad
    insert_trazabilidad = text("""
        INSERT INTO postventa.trazabilidad (formulario_id, estado_id, mensaje)
        VALUES (:formulario_id, 10, :mensaje)
    """)
    db.execute(insert_trazabilidad, {"formulario_id": formulario_id, "mensaje": body.detalle})

    db.commit()

    return JSONResponse(status_code=200, content={
        "estado": 200,
        "mensaje": "Se ha guardado correctamente",
        "data": []
    })