from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.models.formularios import ConsultarEstadoRequest, simulated_docs 
from app.models.formularios import ReclamoForm,QuejaServicioForm, ArchivoServicioForm, ReclamoProductoForm,ArchivoReclamoForm
from app.db.connection import SessionLocal
from app.services.auth_service import verificar_token
from app.utils.security import JWT_SECRET_KEY, ALGORITHM
from fastapi.responses import JSONResponse
from typing import Optional
import re


router = APIRouter(prefix="/api/v1")
security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


import datetime
import json

def json_serial(obj):
    """Función para convertir `date` y `datetime` a string en JSON"""
    if isinstance(obj, (datetime.date, datetime.datetime)):  # Soporta `date` y `datetime`
        return obj.isoformat()  # Convierte a `YYYY-MM-DD` o `YYYY-MM-DDTHH:MM:SS`
    raise TypeError(f"Type {type(obj)} not serializable")


@router.get("/consultar-reclamo-queja")
def consultar_estado_reclamo_queja(
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

    # Si el usuario NO es trabajador, obtener todos sus reclamos y quejas desde `formularios`
    if empresa_id is None:
        query_formularios = text("""
            SELECT 
                id, 
                reclamo, 
                queja_servicio, 
                queja_producto, 
                detalle_reclamo, 
                detalle_queja, 
                fecha_creacion
            FROM postventa.formularios
            WHERE usuarios_id = :usuarios_id
        """)

        result_formularios = db.execute(query_formularios, {"usuarios_id": usuarios_id}).fetchall()

        data_completa = []
        for row in result_formularios:
            id_formulario, reclamo, queja_servicio, queja_producto, detalle_reclamo, detalle_queja, fecha_creacion = row

            # Determinar el prefijo del ID y el detalle a extraer
            if reclamo == 1:
                prefijo = "R"
                detalle = detalle_reclamo
            elif queja_servicio == 1 or queja_producto == 1:
                prefijo = "Q"
                detalle = detalle_queja
            else:
                continue  # Si no es reclamo ni queja, lo ignoramos

            data_completa.append({
                "id": f"{prefijo}{id_formulario}",
                "detalle": detalle,
                "fecha_creacion": fecha_creacion.strftime("%d/%m/%Y %H:%M")
            })

        # Ordenar por fecha de creación DESC
        data_completa = sorted(data_completa, key=lambda x: x["fecha_creacion"], reverse=True)

        return JSONResponse(
            status_code=200,
            content={"estado": 200, "mensaje": "Consulta exitosa.", "data": data_completa}
        )

    # Si el usuario es trabajador, aquí manejaríamos la lógica específica (veremos después)
    return JSONResponse(
        status_code=400, content={"estado": 400, "mensaje": "Acción no permitida para trabajadores en esta etapa."}
    )

@router.post("/registrar-reclamo")
def registrar_reclamo(
    form_data: ReclamoForm = Depends(),
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

    # Validaciones
    errores = {}

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
                estado, fecha, fecha_creacion, serie, correlativo, 
                producto_id, producto_cantidad, detalle_reclamo, 
                placa_vehiculo, marca, modelo_vehiculo, anio, modelo_motor, tipo_operacion_id,
                fecha_instalacion, horas_uso_reclamo, km_instalacion, km_actual
            ) VALUES (
                :usuarios_id, :tipo_usuarios_id, :tipo_correlativos_id, 1, 0, 0,
                :cliente, :dni, :nombres, :apellidos, :correo, :telefono,
                'Generado', CAST(:fecha_venta AS DATE), DEFAULT, :serie, :correlativo,
                :producto_id, :producto_cantidad, :detalle_reclamo, 
                :placa_vehiculo, :marca, :modelo_vehiculo, :anio, :modelo_motor, :tipo_operacion_id,
                :fecha_instalacion, :horas_uso_reclamo, :km_instalacion, :km_actual
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
            archivo_url = f"/uploads/{file.filename}"
            tipo_archivo = file.filename.split('.')[-1].upper()

            db.execute(insert_archivo, {
                "formulario_id": reclamo_id,  
                "archivo_url": archivo_url,
                "tipo_archivo": tipo_archivo
            })

            archivos_insertados.append({"archivo_url": archivo_url, "tipo_archivo": tipo_archivo})

        db.commit()
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
            "archivos": archivos_insertados
        }

        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"estado": 500, "mensaje": f"Error en el servidor: {str(e)}"})


@router.post("/registrar-queja-producto")
def registrar_queja_producto(
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
                email, telefono, estado, fecha, detalle_reclamo, fecha_creacion, 
                producto_id, producto_cantidad, serie, correlativo
            ) VALUES (
                :usuarios_id, :tipo_usuarios_id, :tipo_correlativos_id, 0, 1, 0,
                :motivos_producto_id, 'G1', :cliente, :dni, :nombres, :apellidos,
                :correo, :telefono, 'Generado', CAST(:fecha_venta AS DATE), :detalle_reclamo, DEFAULT,
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
            archivo_url = f"/uploads/{file.filename}"
            tipo_archivo = file.filename.split('.')[-1].upper()

            # Validar tipo de archivo
            tipos_permitidos = ["JPG", "PNG", "PDF", "DOCX", "MP4", "PPTX"]
            if tipo_archivo not in tipos_permitidos:
                raise ValueError(f"Tipo de archivo {tipo_archivo} no permitido.")

            db.execute(insert_archivo, {
                "formulario_id": reclamo_id,
                "archivo_url": archivo_url,
                "tipo_archivo": tipo_archivo
            })
            archivos_insertados.append({"archivo_url": archivo_url, "tipo_archivo": tipo_archivo})

        db.commit()
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
def registrar_queja_servicio(
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
                email, telefono, estado, fecha, detalle_queja, fecha_creacion
            ) VALUES (
                :usuarios_id, :tipo_usuarios_id, 1, 0, 0, :motivo,
                'G2', :cliente, :dni, :nombres, :apellidos,
                :correo, :telefono, 'Registrada', :fecha_queja, :descripcion, DEFAULT
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
            archivo_url = f"/uploads/{file.filename}"
            tipo_archivo = file.filename.split('.')[-1].upper()

            # Validar tipo de archivo
            tipos_permitidos = ["JPG", "PNG", "PDF", "DOCX", "MP4", "PPTX"]
            if tipo_archivo not in tipos_permitidos:
                raise ValueError(f"Tipo de archivo {tipo_archivo} no permitido.")

            db.execute(insert_archivo, {
                "formulario_id": queja_id,
                "archivo_url": archivo_url,
                "tipo_archivo": tipo_archivo
            })
            archivos_insertados.append({"archivo_url": archivo_url, "tipo_archivo": tipo_archivo})

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
    # Validar token
    query_token = text("SELECT usuarios_id FROM postventa.usuarios_tokens WHERE token = :token")
    result_token = db.execute(query_token, {"token": token}).fetchone()
    if not result_token:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido"})
    
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
        # Crear una copia del documento plantilla y actualizarlo con los datos proporcionados
        documento_info = simulated_docs[doc_type].copy()
        documento_info["documento"] = f"{serie}-{correlativo}"
        
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
        # Crear una copia del documento plantilla y actualizarlo con el correlativo proporcionado
        documento_info = simulated_docs[doc_type].copy()
        documento_info["documento"] = correlativo
        
    else:
        return JSONResponse(
            status_code=422,
            content={
                "errores": {"tipo_documento": ["Tipo de documento no reconocido. Use 1 para BOLETA, 2 para FACTURA o 3 para NOTA DE VENTA."]},
                "estado": 422,
                "mensaje": "No es posible procesar los datos enviados."
            }
        )
    
    # Retornar la información del documento
    return JSONResponse(content={"data": documento_info})



