from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Query, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.models.formularios import ConsultarEstadoRequest, simulated_docs, clientes
from app.models.formularios import ReclamoForm,QuejaServicioForm, ArchivoServicioForm, ReclamoProductoForm,ArchivoReclamoForm, AnularRequest, LeidoNotificacionRequest
from app.db.connection import SessionLocal
from app.services.auth_service import verificar_token
from app.utils.security import JWT_SECRET_KEY, ALGORITHM
from fastapi.responses import JSONResponse
from typing import Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import blue, black
import re, os
import requests
from fastapi import BackgroundTasks
from app.services.background_tasks import generar_pdf_background
from app.services.auth_service import obtener_motivo


router = APIRouter(prefix="/api/v1")
security = HTTPBearer()

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


@router.get("/consultar-reclamo-queja")
def consultar_estado_reclamo_queja(
    page: int = Query(1, ge=1, description="Número de página"),
    items_per_page: int = Query(10, ge=1, le=100, description="Elementos por página"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    # Obtener usuarios_id desde USUARIOS_TOKENS
    query_token = text("SELECT usuarios_id FROM postventa.usuarios_tokens WHERE token = :token")
    result_token = db.execute(query_token, {"token": token}).fetchone()

    if not result_token:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido"})

    usuarios_id = result_token[0]

    # Obtener tipo_usuarios_id y empresa_id para verificar si es trabajador
    query_usuario = text("SELECT tipo_usuarios_id, empresa_id FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()

    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado"})

    tipo_usuarios_id, empresa_id = result_usuario

    # Si el usuario NO es trabajador, obtener todos sus reclamos y quejas desde formularios
    if empresa_id is None:
        # Primero, obtén el conteo total para la metadata de paginación
        query_count = text("""
            SELECT COUNT(id)
            FROM postventa.formularios
            WHERE usuarios_id = :usuarios_id
        """)
        
        total_items = db.execute(query_count, {"usuarios_id": usuarios_id}).scalar()
        
        # Calcula el offset para la paginación
        skip = (page - 1) * items_per_page
        
        # Modifica la consulta para incluir LIMIT y OFFSET para paginación
        query_formularios = text("""
            SELECT 
                id, reclamo, queja_servicio, queja_producto, 
                detalle_reclamo, detalle_queja, fecha_creacion, fecha_modificacion,
                estado_id, motivos_servicio_id, motivos_producto_id
            FROM postventa.formularios
            WHERE usuarios_id = :usuarios_id
            ORDER BY fecha_creacion DESC
            LIMIT :limit OFFSET :offset
        """)

        result_formularios = db.execute(query_formularios, {
            "usuarios_id": usuarios_id,
            "limit": items_per_page,
            "offset": skip
        }).fetchall()

        data_completa = []
        for row in result_formularios:
            (
                id_formulario, reclamo, queja_servicio, queja_producto, 
                detalle_reclamo, detalle_queja, fecha_creacion, fecha_modificacion, estado,
                motivos_servicio_id, motivos_producto_id
            ) = row

            # Determinar el prefijo del ID y el tipo
            if reclamo == 1:
                prefijo = "R"
                tipo = "Falla de producto"
            elif queja_servicio == 1:
                prefijo = "Q"
                query_motivo = text("SELECT nombre FROM postventa.motivos_servicio WHERE id = :id")
                result_motivo = db.execute(query_motivo, {"id": motivos_servicio_id}).fetchone()
                tipo = result_motivo[0] if result_motivo else "Motivo no encontrado"
            elif queja_producto == 1:
                prefijo = "R"
                query_motivo = text("SELECT nombre FROM postventa.motivos_producto WHERE id = :id")
                result_motivo = db.execute(query_motivo, {"id": motivos_producto_id}).fetchone()
                tipo = result_motivo[0] if result_motivo else "Motivo no encontrado"
            else:
                continue  # Si no es reclamo ni queja, lo ignoramos

            # 🔹 Buscar la URL del archivo en la tabla archivos
            query_archivo = text("""
                SELECT archivo_url 
                FROM postventa.archivos 
                WHERE formulario_id = :id_formulario AND tipo_archivo = 'pdf'
                ORDER BY id_archivo DESC LIMIT 1
            """)
            result_archivo = db.execute(query_archivo, {"id_formulario": id_formulario}).fetchone()
            archivo_url = result_archivo[0] if result_archivo else None

             # Si no encuentra la URL en la base de datos, deja la ruta genérica
            enlace_pdf = archivo_url if archivo_url else f"http://localhost:8001/uploads/pdfs/{prefijo}_{id_formulario:05d}.pdf"

            # Obtener la trazabilidad del formulario
            query_trazabilidad = text("""
                SELECT t.estado_id, e.nombre, t.fecha_cambio
                FROM postventa.trazabilidad t
                JOIN postventa.estados e ON t.estado_id = e.id_estado
                WHERE t.formulario_id = :id_formulario
                ORDER BY t.fecha_cambio DESC
            """)
            result_trazabilidad = db.execute(query_trazabilidad, {"id_formulario": id_formulario}).fetchall()

            # Construir la trazabilidad con el estado y la fecha correcta
            trazabilidad = [
                {
                    "estado": estado_nombre,
                    "fecha": fecha_cambio.strftime("%d/%m/%Y %H:%M"),
                    "titulo": "Reclamo generado de manera exitosa" if reclamo == 1 else "Queja registrada de manera exitosa",
                    "archivo": {
                        "enlace": enlace_pdf,
                        "nombre": f"{prefijo}_{id_formulario:05d}",
                        "extensión": ".pdf"
                    }
                }
                for estado_id, estado_nombre, fecha_cambio in result_trazabilidad
            ]

            data_completa.append({
                "id": f"{prefijo}{id_formulario:05d}",
                "tipo": tipo,
                "fecha": fecha_creacion.strftime("%d/%m/%Y %H:%M"),
                "trazabilidad": trazabilidad
            })

        # Calcular información de paginación
        total_pages = (total_items + items_per_page - 1) // items_per_page  # Redondeo hacia arriba
        
        # Información de paginación
        paginacion = {
            "page": page,
            "items_per_page": items_per_page,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }

        return JSONResponse(
            status_code=200,
            content={
                "estado": 200, 
                "mensaje": "Consulta exitosa.", 
                "data": data_completa,
                "paginacion": paginacion
            }
        )

    # Si el usuario es trabajador, aquí manejaríamos la lógica específica (veremos después)
    return JSONResponse(
        status_code=400, content={"estado": 400, "mensaje": "Acción no permitida para trabajadores en esta etapa."}
    )

# Definir rutas de almacenamiento
UPLOADS_IMAGENES = "uploads/imagenes"
UPLOADS_VIDEOS = "uploads/videos"
UPLOADS_DOCUMENTOS = "uploads/documentos"
UPLOADS_PDFS = "uploads/pdfs"

@router.post("/registrar-reclamo")
async def registrar_reclamo(
    background_tasks: BackgroundTasks,
    form_data: ReclamoForm = Depends(),
    archivo_data: ArchivoReclamoForm = Depends(),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):

    token = credentials.credentials

    # 🔹 Obtener usuarios_id y tipo_usuarios_id desde USUARIOS
    query_usuario = text("""
        SELECT u.id AS usuarios_id, u.tipo_usuarios_id 
        FROM postventa.usuarios_tokens ut 
        JOIN postventa.usuarios u ON ut.usuarios_id = u.id 
        WHERE ut.token = :token
    """)

    result_usuario = db.execute(query_usuario, {"token": token}).fetchone()

    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido o usuario no encontrado"})

    usuarios_id, tipo_usuarios_id = result_usuario 


        # 🔹 Verificar si es cliente o trabajador
    es_cliente = tipo_usuarios_id == 1
    es_trabajador = tipo_usuarios_id != 1

    # Validaciones
    errores = {}

    # Validaciones adicionales para trabajadores
    if es_trabajador:
        if not hasattr(form_data, "clasificacion_venta") or not form_data.clasificacion_venta:
            errores["clasificacion_venta"] = ["Este campo es obligatorio para trabajadores."]
        if not hasattr(form_data, "potencial_venta") or not form_data.potencial_venta:
            errores["potencial_venta"] = ["Este campo es obligatorio para trabajadores."]
        
        # 🔹 Validar que `form_3_en_tienda` haya sido proporcionado
        if form_data.en_tienda is None:
            errores["en_tienda"] = ["Este campo es obligatorio para trabajadores y debe ser True o False."]
    else:
        # 🔹 Si es cliente, forzamos `en_tienda = False`
        form_data.en_tienda = False

    # 🔹 Si hay errores, retornar una respuesta de validación
    if errores:
        return JSONResponse(status_code=422, content={"errores": errores, "estado": 422, "mensaje": "No es posible procesar los datos enviados."})

    # 🔹 Usamos el valor proporcionado por el trabajador o False si es cliente
    en_tienda_value = form_data.en_tienda

    # Validar `tipo_correlativos_id`
    tipo_correlativos_id = form_data.tipo_correlativos_id
    serie = form_data.serie
    correlativo = form_data.correlativo

    if tipo_correlativos_id in [1, 2]:
        if not serie or len(serie) != 4:
            errores.setdefault("serie", []).append("La serie debe tener exactamente 4 caracteres.")
        if not correlativo or len(correlativo) != 8:
            errores.setdefault("correlativo", []).append("El correlativo debe tener exactamente 8 dígitos.")
    elif tipo_correlativos_id == 3:
        if serie:
            errores.setdefault("serie", []).append("No debe incluir una serie.")
        if not correlativo or len(correlativo) != 7:
            errores.setdefault("correlativo", []).append("El correlativo debe tener exactamente 7 dígitos.")

    # Validar `DNI`
    if len(form_data.dni) != 8 or not form_data.dni.isdigit():
        errores.setdefault("dni", []).append("El DNI debe tener exactamente 8 dígitos numéricos.")

    # Validar archivos
    if not archivo_data.form_5_images and not archivo_data.form_5_videos:
        errores.setdefault("archivos", []).append("Debe adjuntar al menos un archivo")

    if errores:
        return JSONResponse(status_code=422, content={"errores": errores, "estado": 422, "mensaje": "Datos incorrectos"})

    try:
        # Insertar en `formularios`
        insert_reclamo = text("""
            INSERT INTO postventa.formularios (
                usuarios_id, tipo_usuarios_id, tipo_correlativos_id, reclamo, queja_servicio, queja_producto,
                cliente, dni, nombres, apellidos, email, telefono,
                estado_id, fecha, fecha_creacion, serie, correlativo, 
                producto_id, producto_cantidad, detalle_reclamo, 
                placa_vehiculo, marca, modelo_vehiculo, anio, modelo_motor, tipo_operacion_id,
                fecha_instalacion, horas_uso_reclamo, km_instalacion, km_actual, en_tienda
            ) VALUES (
                :usuarios_id, :tipo_usuarios_id, :tipo_correlativos_id, 1, 0, 0,
                :cliente, :dni, :nombres, :apellidos, :correo, :telefono,
                2, CAST(:fecha_venta AS DATE), DEFAULT, :serie, :correlativo,
                :producto_id, :producto_cantidad, :detalle_reclamo, 
                :placa_vehiculo, :marca, :modelo_vehiculo, :anio, :modelo_motor, :tipo_operacion_id,
                :fecha_instalacion, :horas_uso_reclamo, :km_instalacion, :km_actual, :en_tienda
            ) RETURNING id, fecha_creacion
        """)

        result = db.execute(insert_reclamo, form_data.__dict__ | {
            "usuarios_id": usuarios_id,
            "tipo_usuarios_id": tipo_usuarios_id,
            "en_tienda": en_tienda_value
        })
        reclamo_id, fecha_creacion = result.fetchone()

        # Insertar archivos
        insert_archivo = text("""
            INSERT INTO postventa.archivos (formulario_id, archivo_url, tipo_archivo)
            VALUES (:formulario_id, :archivo_url, :tipo_archivo)
        """)

        archivos_insertados = []
        for file in archivo_data.form_5_images + archivo_data.form_5_videos:
            # Detectar si el archivo es imagen o video
            tipo_archivo = file.filename.split('.')[-1].upper()

            if tipo_archivo in ["JPG", "PNG"]:
                folder_path = UPLOADS_IMAGENES
                base_url = "http://localhost:8001/uploads/imagenes"
            elif tipo_archivo in ["MP4"]:
                folder_path = UPLOADS_VIDEOS
                base_url = "http://localhost:8001/uploads/videos"
            else:
                continue  # Si el archivo no es compatible, lo ignoramos

            # Ruta completa para guardar el archivo
            file_path = os.path.join(folder_path, file.filename)

            # Guardar el archivo en la carpeta correspondiente
            with open(file_path, "wb") as f:
                f.write(await file.read())

            # Construir la URL accesible
            archivo_url = f"{base_url}/{file.filename}"

            # Insertar en la base de datos
            db.execute(insert_archivo, {
                "formulario_id": reclamo_id,  
                "archivo_url": archivo_url,  # Guardamos la URL completa
                "tipo_archivo": tipo_archivo
            })

            archivos_insertados.append({"archivo_url": archivo_url, "tipo_archivo": tipo_archivo})
        
        # Insertar en trazabilidad
        insert_trazabilidad = text("""
            INSERT INTO postventa.trazabilidad (formulario_id, estado_id)
            VALUES (:formulario_id, :estado_id)
        """)

         # Ejecutar la inserción
        db.execute(insert_trazabilidad, {
            "formulario_id": reclamo_id,
            "estado_id": 2  # Estado en el que se encuentra el formulario
        })

                # Insertar notificación cuando se registra un reclamo
        insert_notificacion = text("""
            INSERT INTO postventa.notificaciones (usuarios_id, formulario_id, tipo, icono, mensaje)
            VALUES (:usuarios_id, :formulario_id, 'Notificación por sistema', 'far fa-list', :mensaje)
        """)

        mensaje_notificacion = f"{reclamo_id} - {form_data.cliente}, generó un reclamo por 'Falla de producto'"

        db.execute(insert_notificacion, {
            "usuarios_id": usuarios_id,  
            "formulario_id": reclamo_id,  
            "mensaje": mensaje_notificacion
        })

        db.commit()

        if es_cliente:
            # 🔹 Llamar a la generación de PDF en segundo plano
            background_tasks.add_task(generar_pdf_background, reclamo_id, token, SessionLocal)

        response_data = {
            "estado": 200,
            "mensaje": "Reclamo registrado correctamente.",
            "id_reclamo": reclamo_id,
            "fecha_creacion": fecha_creacion.strftime("%Y-%m-%d"),
            "usuarios_id": usuarios_id,
            "tipo_usuarios_id": tipo_usuarios_id,
            "tipo_correlativos_id": form_data.tipo_correlativos_id,
            "serie": form_data.serie,
            "correlativo": form_data.correlativo,
            "fecha_venta": form_data.fecha_venta,
            "cliente": form_data.cliente,
            "dni": form_data.dni,
            "nombres": form_data.nombres,
            "apellidos": form_data.apellidos,
            "correo": form_data.correo,
            "telefono": form_data.telefono,
            "producto_id": form_data.producto_id,
            "producto_cantidad": form_data.producto_cantidad,
            "detalle_reclamo": form_data.detalle_reclamo,
            "placa_vehiculo": form_data.placa_vehiculo,
            "marca": form_data.marca,
            "modelo_vehiculo": form_data.modelo_vehiculo,
            "anio": form_data.anio,
            "modelo_motor": form_data.modelo_motor,
            "tipo_operacion_id": form_data.tipo_operacion_id,
            "fecha_instalacion": form_data.fecha_instalacion,
            "horas_uso_reclamo": form_data.horas_uso_reclamo,
            "km_instalacion": form_data.km_instalacion,
            "km_actual": form_data.km_actual,
            "archivos": archivos_insertados,
            "en_tienda": en_tienda_value,
        }

         # Solo agregar estos campos si es trabajador
        if es_trabajador:
            response_data["clasificacion_venta"] = form_data.clasificacion_venta
            response_data["potencial_venta"] = form_data.potencial_venta

        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"estado": 500, "mensaje": f"Error en el servidor: {str(e)}"})

@router.post("/registrar-queja-producto")
async def registrar_queja_producto(
    background_tasks: BackgroundTasks,
    form_data: ReclamoProductoForm = Depends(),
    archivo_data: ArchivoReclamoForm = Depends(),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    token = credentials.credentials

    # Obtener usuarios_id desde USUARIOS_TOKENS
    query_token = text("SELECT usuarios_id FROM postventa.usuarios_tokens WHERE token = :token")
    result_token = db.execute(query_token, {"token": token}).fetchone()

    if not result_token:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido"})

    usuarios_id = result_token[0]

    # Obtener tipo_usuarios_id desde USUARIOS
    query_usuario = text("SELECT tipo_usuarios_id, empresa_id FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()

    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado"})

    tipo_usuarios_id, empresa_id = result_usuario

    # Validaciones de campos obligatorios
    errores = {}

    campos_obligatorios = [
        "motivos_producto_id", "tipo_correlativos_id", "serie", "correlativo",
        "fecha_venta", "cliente", "dni", "nombres", "apellidos", "correo", "telefono",
        "producto_id", "producto_cantidad", "detalle_reclamo"
    ]

    for campo in campos_obligatorios:
        if getattr(form_data, campo, None) is None or str(getattr(form_data, campo)).strip() == "":
            errores.setdefault(campo, []).append("Campo obligatorio")

    # Validación de tipo_correlativo_id
    tipo_correlativos_id = form_data.tipo_correlativos_id
    serie = form_data.serie
    correlativo = form_data.correlativo

    if tipo_correlativos_id in [1, 2]:
        if not serie or len(serie) != 4:
            errores.setdefault("serie", []).append("La serie debe tener exactamente 4 caracteres.")
        if not correlativo or len(correlativo) != 8:
            errores.setdefault("correlativo", []).append("El correlativo debe tener exactamente 8 dígitos.")
    elif tipo_correlativos_id == 3:
        if serie:
            errores.setdefault("serie", []).append("No debe incluir una serie.")
        if not correlativo or len(correlativo) != 7:
            errores.setdefault("correlativo", []).append("El correlativo debe tener exactamente 7 dígitos.")

    # Validación de DNI (Debe tener exactamente 8 dígitos numéricos)
    if len(form_data.dni) != 8 or not form_data.dni.isdigit():
        errores.setdefault("dni", []).append("El DNI debe tener exactamente 8 dígitos numéricos.")

    # Validar archivos
    if not archivo_data.form_5_images and not archivo_data.form_5_videos:
        errores.setdefault("archivos", []).append("Debe adjuntar al menos un archivo")

    if errores:
        return JSONResponse(status_code=422, content={"errores": errores, "estado": 422, "mensaje": "Datos incorrectos"})

    try:
        # Insertar en la tabla FORMULARIOS con serie y correlativo correctamente
        insert_reclamo = text("""
            INSERT INTO postventa.formularios (
                usuarios_id, tipo_usuarios_id, tipo_correlativos_id, queja_servicio, queja_producto, reclamo,
                motivos_producto_id, tipo_queja, cliente, dni, nombres, apellidos,
                email, telefono, estado_id, fecha, detalle_reclamo, fecha_creacion, 
                producto_id, producto_cantidad, serie, correlativo
            ) VALUES (
                :usuarios_id, :tipo_usuarios_id, :tipo_correlativos_id, 0, 1, 0,
                :motivos_producto_id, 'G1', :cliente, :dni, :nombres, :apellidos,
                :correo, :telefono, 2, CAST(:fecha_venta AS DATE), :detalle_reclamo, DEFAULT,
                :producto_id, :producto_cantidad, :serie, :correlativo
            ) RETURNING id, fecha_creacion
        """)

        result = db.execute(insert_reclamo, form_data.__dict__ | {
            "usuarios_id": usuarios_id,
            "tipo_usuarios_id": tipo_usuarios_id,
        })
        reclamo_id, fecha_creacion = result.fetchone()

        # Insertar archivos
        insert_archivo = text("""
            INSERT INTO postventa.archivos (formulario_id, archivo_url, tipo_archivo)
            VALUES (:formulario_id, :archivo_url, :tipo_archivo)
        """)

        archivos_insertados = []
        for file in archivo_data.form_5_images + archivo_data.form_5_videos:
            # Detectar si el archivo es imagen o video
            tipo_archivo = file.filename.split('.')[-1].upper()

            if tipo_archivo in ["JPG", "PNG"]:
                folder_path = UPLOADS_IMAGENES
                base_url = "http://localhost:8001/uploads/imagenes"
            elif tipo_archivo in ["MP4"]:
                folder_path = UPLOADS_VIDEOS
                base_url = "http://localhost:8001/uploads/videos"
            else:
                continue  # Si el archivo no es compatible, lo ignoramos

            # Ruta completa para guardar el archivo
            file_path = os.path.join(folder_path, file.filename)

            # Guardar el archivo en la carpeta correspondiente
            with open(file_path, "wb") as f:
                f.write(await file.read())

            # Construir la URL accesible
            archivo_url = f"{base_url}/{file.filename}"

            # Insertar en la base de datos
            db.execute(insert_archivo, {
                "formulario_id": reclamo_id,  
                "archivo_url": archivo_url,  # Guardamos la URL completa
                "tipo_archivo": tipo_archivo
            })

            archivos_insertados.append({"archivo_url": archivo_url, "tipo_archivo": tipo_archivo})

        # Insertar en trazabilidad
        insert_trazabilidad = text("""
            INSERT INTO postventa.trazabilidad (formulario_id, estado_id)
            VALUES (:formulario_id, :estado_id)
        """)

         # Ejecutar la inserción
        db.execute(insert_trazabilidad, {
            "formulario_id": reclamo_id,
            "estado_id": 2  # Estado en el que se encuentra el formulario
        })

        db.commit()

        # 🔹 Llamar a la generación de PDF en segundo plano
        background_tasks.add_task(generar_pdf_background, reclamo_id, token, SessionLocal)

        # Construcción de la respuesta con toda la data ingresada
        response_data = {
            "estado": 200,
            "mensaje": "Reclamo de producto registrado correctamente.",
            "fecha_creacion": fecha_creacion.strftime("%Y-%m-%d"),
            "id_reclamo": reclamo_id,
            "usuarios_id": usuarios_id,
            "tipo_usuarios_id": tipo_usuarios_id,
            "motivos_producto_id": form_data.motivos_producto_id,
            "tipo_correlativos_id": form_data.tipo_correlativos_id,
            "serie": form_data.serie,
            "correlativo": form_data.correlativo,
            "fecha_venta": form_data.fecha_venta,
            "cliente": form_data.cliente,
            "dni": form_data.dni,
            "nombres": form_data.nombres,
            "apellidos": form_data.apellidos,
            "correo": form_data.correo,
            "telefono": form_data.telefono,
            "producto_id": form_data.producto_id,
            "producto_cantidad": form_data.producto_cantidad,
            "detalle_reclamo": form_data.detalle_reclamo,
            "archivos": archivos_insertados
        }

        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"estado": 500, "mensaje": f"Error en el servidor: {str(e)}"})

@router.post("/registrar-queja-servicio")
async def registrar_queja_servicio(
    form_data: QuejaServicioForm = Depends(),
    archivo_data: ArchivoServicioForm = Depends(),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    token = credentials.credentials

    # Obtener usuarios_id desde USUARIOS_TOKENS
    query_token = text("SELECT usuarios_id FROM postventa.usuarios_tokens WHERE token = :token")
    result_token = db.execute(query_token, {"token": token}).fetchone()

    if not result_token:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido"})

    usuarios_id = result_token[0]

    # Obtener tipo_usuarios_id desde USUARIOS
    query_usuario = text("SELECT tipo_usuarios_id, empresa_id FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()

    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado"})

    tipo_usuarios_id, empresa_id = result_usuario

    # Validaciones de campos obligatorios
    errores = {}

    campos_obligatorios = [
        "tipo_queja", "motivo", "fecha_queja", "descripcion",
        "cliente", "dni", "nombres", "apellidos", "correo", "telefono"
    ]

    for campo in campos_obligatorios:
        if getattr(form_data, campo, None) is None or str(getattr(form_data, campo)).strip() == "":
            errores.setdefault(campo, []).append("Campo obligatorio")

    # Validación de DNI (Debe tener exactamente 8 dígitos numéricos)
    if len(form_data.dni) != 8 or not form_data.dni.isdigit():
        errores.setdefault("dni", []).append("El DNI debe tener exactamente 8 dígitos numéricos.")

    # Validar archivos
    if not archivo_data.images and not archivo_data.videos:
        errores.setdefault("archivos", []).append("Debe adjuntar al menos un archivo")

    if errores:
        return JSONResponse(status_code=422, content={"errores": errores, "estado": 422, "mensaje": "Datos incorrectos"})

    try:
        # Insertar en la tabla FORMULARIOS
        insert_queja = text("""
            INSERT INTO postventa.formularios (
                usuarios_id, tipo_usuarios_id, queja_servicio, queja_producto, reclamo, motivos_servicio_id,
                tipo_queja, cliente, dni, nombres, apellidos,
                email, telefono, estado_id, fecha, detalle_queja, fecha_creacion
            ) VALUES (
                :usuarios_id, :tipo_usuarios_id, 1, 0, 0, :motivo,
                'G2', :cliente, :dni, :nombres, :apellidos,
                :correo, :telefono, 1, :fecha_queja, :descripcion, DEFAULT
            ) RETURNING id, fecha_creacion
        """)

        result = db.execute(insert_queja, {
            "usuarios_id": usuarios_id,
            "tipo_usuarios_id": tipo_usuarios_id,
            "motivo": form_data.motivo,
            "cliente": form_data.cliente,
            "dni": form_data.dni,
            "nombres": form_data.nombres,
            "apellidos": form_data.apellidos,
            "correo": form_data.correo,
            "telefono": form_data.telefono,
            "fecha_queja": form_data.fecha_queja,
            "descripcion": form_data.descripcion,
        })

        queja_id, fecha_creacion = result.fetchone()
        
        # Insertar archivos en la tabla ARCHIVOS
        insert_archivo = text("""
            INSERT INTO postventa.archivos (formulario_id, archivo_url, tipo_archivo)
            VALUES (:formulario_id, :archivo_url, :tipo_archivo)
        """)

        archivos_insertados = []
        for file in archivo_data.images + archivo_data.videos:
            # Detectar el tipo de archivo
            tipo_archivo = file.filename.split('.')[-1].upper()

            # Definir la carpeta y URL base según el tipo de archivo
            if tipo_archivo in ["JPG", "PNG"]:
                folder_path = UPLOADS_IMAGENES
                base_url = "http://localhost:8001/uploads/imagenes"
            elif tipo_archivo in ["MP4"]:
                folder_path = UPLOADS_VIDEOS
                base_url = "http://localhost:8001/uploads/videos"
            elif tipo_archivo in ["PDF", "DOCX", "PPTX"]:
                folder_path = UPLOADS_DOCUMENTOS  # Asegúrate de definir esta variable en tu código
                base_url = "http://localhost:8001/uploads/documentos"
            else:
                continue  # Si el archivo no es compatible, lo ignoramos

            # Ruta completa para guardar el archivo
            file_path = os.path.join(folder_path, file.filename)

            # Guardar el archivo en la carpeta correspondiente
            with open(file_path, "wb") as f:
                f.write(await file.read())

            # Construir la URL accesible
            archivo_url = f"{base_url}/{file.filename}"

            # Insertar en la base de datos
            db.execute(insert_archivo, {
                "formulario_id": queja_id,
                "archivo_url": archivo_url,  # Guardamos la URL completa
                "tipo_archivo": tipo_archivo
            })

            archivos_insertados.append({"archivo_url": archivo_url, "tipo_archivo": tipo_archivo})
        
        # Insertar en trazabilidad
        insert_trazabilidad = text("""
            INSERT INTO postventa.trazabilidad (formulario_id, estado_id)
            VALUES (:formulario_id, :estado_id)
        """)

         # Ejecutar la inserción
        db.execute(insert_trazabilidad, {
            "formulario_id": queja_id,
            "estado_id": 1  # Estado en el que se encuentra el formulario
        })

        # Confirmar cambios en la base de datos
        db.commit()

        # Construcción de la respuesta con toda la data ingresada
        response_data = {
            "estado": 200,
            "mensaje": "Queja registrada correctamente.",
            "id_queja": queja_id,
            "usuarios_id": usuarios_id,
            "tipo_usuarios_id": tipo_usuarios_id,
            "tipo_queja": "G2",
            "motivo": form_data.motivo,
            "fecha_queja": form_data.fecha_queja,
            "descripcion": form_data.descripcion,
            "cliente": form_data.cliente,
            "dni": form_data.dni,
            "nombres": form_data.nombres,
            "apellidos": form_data.apellidos,
            "correo": form_data.correo,
            "telefono": form_data.telefono,
            "estado": "Registrada",
            "fecha_creacion": fecha_creacion.strftime("%Y-%m-%d %H:%M:%S"),
            "archivos": archivos_insertados  
        }

        return JSONResponse(status_code=200, content=response_data)

    except ValueError as ve:
        db.rollback()  # Revierte la transacción en caso de error en validaciones
        return JSONResponse(status_code=400, content={"estado": 400, "mensaje": str(ve)})

    except Exception as e:
        db.rollback()  # Revierte la transacción en caso de error general
        return JSONResponse(status_code=500, content={"estado": 500, "mensaje": f"Error en el servidor: {str(e)}"})

@router.get("/buscar-documento")
async def buscar_documento(
    tipo_documento: int = Query(..., description="1 para BOLETA, 2 para FACTURA, 3 para NOTA DE VENTA"),
    serie: Optional[str] = Query("", description="Serie para BOLETA o FACTURA. No se utiliza para NOTA DE VENTA"),
    correlativo: str = Query(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    # Validar token y obtener usuarios_id
    query_token = text("SELECT usuarios_id FROM postventa.usuarios_tokens WHERE token = :token")
    result_token = db.execute(query_token, {"token": token}).fetchone()
    
    if not result_token:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido"})
    
    usuarios_id = result_token[0]

    # Obtener tipo_usuarios_id del usuario
    query_usuario = text("SELECT tipo_usuarios_id FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()

    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado"})

    tipo_usuarios_id = result_usuario[0]

    # Validaciones de tipo de documento
    if tipo_documento in [1, 2]:  # BOLETA o FACTURA
        if not serie or not re.fullmatch(r'[A-Za-z0-9]{4}', serie.strip()):
            return JSONResponse(
                status_code=422,
                content={
                    "errores": {"serie": ["Para BOLETA o FACTURA, la serie es obligatoria y debe contener exactamente 4 caracteres alfanuméricos."]},
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )
        if not re.fullmatch(r'\d{8}', correlativo):
            return JSONResponse(
                status_code=422,
                content={
                    "errores": {"correlativo": ["Para BOLETA o FACTURA, el correlativo debe contener exactamente 8 dígitos."]},
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )
        doc_type = "BOLETA" if tipo_documento == 1 else "FACTURA"

    elif tipo_documento == 3:  # NOTA DE VENTA
        if serie and serie.strip() != "":
            return JSONResponse(
                status_code=422,
                content={
                    "errores": {"serie": ["Para NOTA DE VENTA, no se debe enviar serie."]},
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )
        if not re.fullmatch(r'\d{7}', correlativo):
            return JSONResponse(
                status_code=422,
                content={
                    "errores": {"correlativo": ["Para NOTA DE VENTA, el correlativo debe contener exactamente 7 dígitos."]},
                    "estado": 422,
                    "mensaje": "No es posible procesar los datos enviados."
                }
            )
        doc_type = "NOTA DE VENTA"

    else:
        return JSONResponse(
            status_code=422,
            content={
                "errores": {"tipo_documento": ["Tipo de documento no reconocido. Use 1 para BOLETA, 2 para FACTURA o 3 para NOTA DE VENTA."]},
                "estado": 422,
                "mensaje": "No es posible procesar los datos enviados."
            }
        )

    # Obtener la información simulada del documento
    documento_info = simulated_docs[doc_type].copy()
    documento_info["documento"] = f"{serie}-{correlativo}" if tipo_documento in [1, 2] else correlativo

    # Si el usuario es tipo_usuarios_id = 1, eliminar los campos clasificacion_venta y potencial_venta
    if tipo_usuarios_id == 1:
        documento_info.pop("clasificacion_venta", None)
        documento_info.pop("potencial_venta", None)

        # 🔹 Recorrer la lista de productos y eliminar precio_venta
        for producto in documento_info.get("productos", []):
            producto.pop("precio_venta", None)

    # Retornar la información del documento
    return JSONResponse(content={"data": documento_info})


@router.get("/buscar-cliente")
async def buscar_cliente(buscar: str = Query(..., description="Código del cliente a buscar")):
    """
    Endpoint para buscar un cliente por código.
    """
    cliente = clientes.get(buscar)

    if not cliente:
        return JSONResponse(
            status_code=404,
            content={"mensaje": "Cliente no encontrado"}
        )

    return [cliente]

@router.get("/seguimiento")
async def obtener_seguimiento(
    page: int = Query(1, description="Número de página (debe ser un entero)", gt=0),
    tipo_registro: Optional[str] = Query(None, description="Tipo de registro: 'reclamos', 'quejas' o vacío"),
    estado: Optional[str] = Query(None, description="ID del estado (debe ser un entero positivo)"),
    leyenda: Optional[str] = Query(None, description="Leyenda: 'NNC' o 'NNP'"),
    buscar: Optional[str] = Query(None, description="Código, razón social o RUC del cliente"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    items_per_page = 10  # 🔹 Cantidad de registros por página

    # 🔹 Validar usuario con el token
    query_usuario = text("SELECT usuarios_id FROM postventa.usuarios_tokens WHERE token = :token")
    result_usuario = db.execute(query_usuario, {"token": token}).fetchone()

    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido o usuario no encontrado"})

    usuarios_id = result_usuario[0]

    # 🔹 Construcción del Query Base
    base_query = """
        FROM postventa.formularios f
        LEFT JOIN postventa.estados e ON f.estado_id = e.id_estado
        WHERE 1=1
    """
    filters = ""
    params = {}

    # 🔹 Filtrar por tipo de registro
    if tipo_registro:
        if tipo_registro == "reclamos":
            filters += " AND (f.reclamo = 1 OR f.queja_producto = 1)"
        elif tipo_registro == "quejas":
            filters += " AND f.queja_servicio = 1"

    # 🔹 Filtrar por estado solo si tiene un valor válido
    if estado:
        try:
            estado_int = int(estado)
            if estado_int > 0:
                filters += " AND f.estado_id = :estado"
                params["estado"] = estado_int
        except ValueError:
            pass

    # 🔹 Buscar por cliente
    if buscar:
        filters += """
            AND (
                LOWER(f.nombres) LIKE LOWER(:buscar) 
                OR LOWER(f.apellidos) LIKE LOWER(:buscar) 
                OR f.dni = :buscar
            )
        """
        params["buscar"] = buscar if buscar.isdigit() else f"%{buscar}%"

    # 🔹 Obtener el total de registros
    total_query = f"SELECT COUNT(*) {base_query} {filters}"
    total_items = db.execute(text(total_query), params).scalar()
    total_pages = (total_items + items_per_page - 1) // items_per_page  # 🔹 Redondeo hacia arriba

    # 🔹 Aplicar paginación
    offset = (page - 1) * items_per_page
    data_query = f"""
        SELECT f.id, 
               f.estado_id, 
               COALESCE(e.nombre, 'Sin estado') AS estado_desc, 
               f.fecha_creacion AS fecha_registro, 
               f.reclamo, f.queja_servicio, f.queja_producto,
               f.motivos_servicio_id, f.motivos_producto_id
        {base_query} 
        {filters}
        ORDER BY f.reclamo DESC, f.fecha_creacion DESC
        LIMIT :limit OFFSET :offset
    """
    params.update({"limit": items_per_page, "offset": offset})
    result = db.execute(text(data_query), params).fetchall()

    # 🔹 Formatear la respuesta
    seguimiento_list = []
    for idx, row in enumerate(result, start=offset + 1):
        id_prefix = "R" if (row.reclamo == 1 or row.queja_producto == 1) else "Q" if row.queja_servicio == 1 else "X"
        motivo = obtener_motivo(row.reclamo, row.queja_servicio, row.queja_producto, row.motivos_servicio_id, row.motivos_producto_id, db)
        leyenda_texto = leyenda.strip() if leyenda and leyenda.strip() else "NNC"

        seguimiento_list.append({
            "nro": idx,
            "id": f"{id_prefix}{row.id:03d}",
            "motivo": motivo,
            "fecha_registro": row.fecha_registro.strftime('%d/%m/%Y') if row.fecha_registro else "Sin fecha",
            "codigo_cliente": "CL123456",
            "razon_social": "Cliente S.A.",
            "clasificacion_venta": "xxxxxxxx",
            "potencial_venta": "xxxxxxxxx",
            "documento": "4564684684",
            "modalidad": "Crédito",
            "cl_cm": "Compra Local",
            "proveedor": "EMPRESA PROVEEDOR",
            "nc": "Nota crédito cliente" if leyenda_texto == "NNC" else "Nota crédito proveedor",
            "estado": row.estado_id if row.estado_id is not None else None,
            "estado_desc": row.estado_desc
        })

    # 🔹 Información de paginación
    paginacion = {
        "page": page,
        "items_per_page": items_per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

    return JSONResponse(status_code=200, content={"estado": 200, "data": seguimiento_list, "pagination_info": paginacion})

@router.get("/usuario-notificaciones")
async def obtener_notificaciones(
    top: int = Query(5, description="Cantidad máxima de notificaciones a devolver"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    # Obtener el usuario desde el token
    query_usuario = text("""
        SELECT u.id AS usuarios_id, u.tipo_usuarios_id
        FROM postventa.usuarios_tokens ut
        JOIN postventa.usuarios u ON ut.usuarios_id = u.id
        WHERE ut.token = :token
    """)
    
    result_usuario = db.execute(query_usuario, {"token": token}).fetchone()

    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido o usuario no encontrado"})

    usuarios_id, tipo_usuarios_id = result_usuario

    # Si es trabajador, ve todas las notificaciones. Si es cliente, solo sus notificaciones.
    query = """
        SELECT id, leido_en, tipo, icono, mensaje, creado_en
        FROM postventa.notificaciones
    """
    
    params = {}
    if tipo_usuarios_id == 1:  # Cliente
        query += " WHERE usuarios_id = :usuarios_id"
        params["usuarios_id"] = usuarios_id

    query += " ORDER BY creado_en DESC LIMIT :top"
    params["top"] = top

    result = db.execute(text(query), params).fetchall()

    notificaciones = [
        {
            "id": row.id,
            "leido_en": row.leido_en.strftime('%Y-%m-%d %H:%M:%S') if row.leido_en else None,
            "tipo": row.tipo,
            "icono": row.icono,
            "mensaje": row.mensaje,
            "creado_en": row.creado_en.strftime('%Y-%m-%d %H:%M:%S')
        }
        for row in result
    ]

    return JSONResponse(status_code=200, content={"estado": 200, "data": notificaciones})

@router.post("/leido-notificacion")
async def marcar_notificacion_leida(
    request_body: LeidoNotificacionRequest,  # 🔹 Ahora recibe un modelo Pydantic
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    # 🔹 Obtener usuario desde el token
    query_usuario = text("""
        SELECT u.id AS usuarios_id, u.tipo_usuarios_id 
        FROM postventa.usuarios_tokens ut 
        JOIN postventa.usuarios u ON ut.usuarios_id = u.id 
        WHERE ut.token = :token
    """)
    result_usuario = db.execute(query_usuario, {"token": token}).fetchone()

    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido o usuario no encontrado"})

    usuarios_id, tipo_usuarios_id = result_usuario

    # 🔹 Verificar si la notificación existe y pertenece al usuario
    query_notificacion = text("""
        SELECT id, usuarios_id, leido_en, tipo, icono, mensaje, creado_en
        FROM postventa.notificaciones 
        WHERE id = :id
    """)
    result_notificacion = db.execute(query_notificacion, {"id": request_body.id}).fetchone()

    if not result_notificacion:
        return JSONResponse(status_code=404, content={"estado": 404, "mensaje": "Notificación no encontrada"})

    notificacion_id, notificacion_usuario_id, leido_en, tipo, icono, mensaje, creado_en = result_notificacion

    # 🔹 Si es cliente, solo puede marcar sus propias notificaciones
    if tipo_usuarios_id == 1 and notificacion_usuario_id != usuarios_id:
        return JSONResponse(status_code=403, content={"estado": 403, "mensaje": "No tienes permiso para modificar esta notificación."})

    # 🔹 Si la notificación ya está marcada como leída, devolver la misma información
    if leido_en:
        return JSONResponse(status_code=200, content={
            "estado": 200,
            "id": notificacion_id,
            "leido_en": leido_en.strftime('%Y-%m-%d %H:%M:%S'),
            "tipo": tipo,
            "icono": icono,
            "mensaje": mensaje,
            "creado_en": creado_en.strftime('%Y-%m-%d %H:%M:%S')
        })

    # 🔹 Marcar la notificación como leída
    update_query = text("""
        UPDATE postventa.notificaciones
        SET leido_en = NOW()
        WHERE id = :id
    """)
    db.execute(update_query, {"id": request_body.id})
    db.commit()

    # 🔹 Volver a obtener la notificación actualizada
    result_notificacion_actualizada = db.execute(query_notificacion, {"id": request_body.id}).fetchone()
    notificacion_id, notificacion_usuario_id, leido_en, tipo, icono, mensaje, creado_en = result_notificacion_actualizada

    return JSONResponse(status_code=200, content={
        "estado": 200,
        "id": notificacion_id,
        "leido_en": leido_en.strftime('%Y-%m-%d %H:%M:%S'),
        "tipo": tipo,
        "icono": icono,
        "mensaje": mensaje,
        "creado_en": creado_en.strftime('%Y-%m-%d %H:%M:%S')
    })

@router.post("/reclamo-queja/anular")
async def anular_reclamo_queja(
    data: AnularRequest = Body(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    # 🔒 Validar token
    query_usuario = text("SELECT usuarios_id FROM postventa.usuarios_tokens WHERE token = :token")
    result_usuario = db.execute(query_usuario, {"token": token}).fetchone()

    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido"})

    usuarios_id = result_usuario[0]

    # 🔎 Buscar el formulario y verificar que esté en estado 'GENERADO' (estado_id = 2)
    query_formulario = text("""
        SELECT id, estado_id 
        FROM postventa.formularios 
        WHERE id = :id
    """)
    formulario = db.execute(query_formulario, {"id": data.id}).fetchone()

    if not formulario:
        return JSONResponse(status_code=404, content={"estado": 404, "mensaje": "Formulario no encontrado"})

    if formulario.estado_id != 2:
        return JSONResponse(status_code=400, content={"estado": 400, "mensaje": "Solo se puede anular formularios en estado 'GENERADO'"})

    # 📝 Actualizar el estado del formulario a 'ANULADO' (estado_id = 4)
    update_query = text("""
        UPDATE postventa.formularios
        SET estado_id = 4
        WHERE id = :id
    """)
    db.execute(update_query, {"id": data.id})

    # 🗒 Insertar trazabilidad con el motivo
    insert_trazabilidad = text("""
        INSERT INTO postventa.trazabilidad (formulario_id, estado_id, fecha_cambio, mensaje)
        VALUES (:formulario_id, 4, :fecha_cambio, :mensaje)
    """)
    db.execute(insert_trazabilidad, {
        "formulario_id": data.id,
        "fecha_cambio": datetime.now(),
        "mensaje": data.motivo
    })

    db.commit()

    return JSONResponse(status_code=200, content={"estado": 200, "mensaje": "Se ha anulado"})


