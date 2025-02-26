from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.models.formularios import ReclamoRequest, QuejaRequest, simulated_docs 
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

import json

import datetime
import json

def json_serial(obj):
    """Función para convertir `date` y `datetime` a string en JSON"""
    if isinstance(obj, (datetime.date, datetime.datetime)):  # Soporta `date` y `datetime`
        return obj.isoformat()  # Convierte a `YYYY-MM-DD` o `YYYY-MM-DDTHH:MM:SS`
    raise TypeError(f"Type {type(obj)} not serializable")

@router.post("/registrar-reclamo")
def registrar_reclamo(
    request: ReclamoRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    # Obtener `usuarios_id` desde `USUARIOS_TOKENS`
    query_token = text("SELECT usuarios_id FROM postventa.usuarios_tokens WHERE token = :token")
    result_token = db.execute(query_token, {"token": token}).fetchone()

    if not result_token:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Token inválido"})

    usuarios_id = result_token[0]

    # Obtener `tipo_usuarios_id` desde `USUARIOS`
    query_usuario = text("SELECT tipo_usuarios_id FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()

    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado"})

    tipo_usuarios_id = result_usuario[0]

    # Validar que los campos obligatorios NO estén vacíos
    errores = {}
    request_dict = request.dict()

    campos_obligatorios = [
        "tipo_correlativos_id", "correlativo", "fecha_venta", "provincia",
        "n_interno", "guia_remision", "sucursal", "almacen", "condicion_pago",
        "vendedor", "transportista", "cliente_ruc_dni", "dni", "nombres",
        "apellidos", "email", "telefono", "placa_vehiculo", "modelo_vehiculo",
        "marca", "modelo_motor", "anio", "tipo_operacion", "fecha_instalacion", "horas_uso_reclamo", "km_instalacion",
        "km_actual", "km_recorridos", "detalle_reclamo"
    ]

    for campo in campos_obligatorios:
        if campo not in request_dict or str(request_dict[campo]).strip() == "":
            errores.setdefault(campo, []).append("Campo obligatorio")

    # Validar `tipo_correlativos_id`, `serie` y `correlativo`
    tipo_correlativos_id = request_dict.get("tipo_correlativos_id", "")
    serie = request_dict.get("serie", None)
    correlativo = request_dict.get("correlativo", "")

    if tipo_correlativos_id in [1, 2]:
        if not serie or len(serie) != 4:
            errores.setdefault("serie", []).append("La serie debe tener exactamente 4 caracteres.")
        if len(correlativo) != 8:
            errores.setdefault("correlativo", []).append("El correlativo debe tener exactamente 8 dígitos.")

    elif tipo_correlativos_id == 3:
        if serie:
            errores.setdefault("serie", []).append("No debe incluir una serie.")
        if len(correlativo) != 7:
            errores.setdefault("correlativo", []).append("El correlativo debe tener exactamente 7 dígitos.")

    # Validar `productos`
    productos = request_dict.get("productos", [])
    if not productos or len(productos) == 0:
        errores.setdefault("productos", []).append("Debe agregar al menos un producto")
    else:
        for producto in productos:
            for campo in ["itm", "lin", "org", "marc", "descrp_marc", "fabrica", "articulo", "descripcion", "precio", "cantidad_reclamo", "und_reclamo"]:
                if campo not in producto or str(producto[campo]).strip() == "":
                    errores.setdefault(campo, []).append("Campo obligatorio")  # Detectar múltiples errores

    # Validar `archivos`
    archivos = request_dict.get("archivos", [])
    if not archivos or len(archivos) == 0:
        errores.setdefault("archivos", []).append("Debe agregar al menos un archivo adjunto")
    else:
        for archivo in archivos:
            for campo in ["archivo_url", "tipo_archivo"]:
                if campo not in archivo or str(archivo[campo]).strip() == "":
                    errores.setdefault(campo, []).append("Campo obligatorio")  

    # Si hay errores, devolver `422`
    if errores:
        return JSONResponse(
            status_code=422,
            content={"errores": errores, "estado": 422, "mensaje": "No es posible procesar los datos enviados."}
        )

    try:
        #Convertir a diccionario y agregar usuarios_id manualmente
        request_dict = request.dict()
        request_dict["usuarios_id"] = usuarios_id
        request_dict["tipo_usuarios_id"] = tipo_usuarios_id

        #Insertar en la tabla DOCUMENTOS
        insert_documento = text("""
            INSERT INTO postventa.documentos (
                tipo_correlativos_id, serie, correlativo, fecha_venta, provincia, n_interno, 
                guia_remision, sucursal, almacen, condicion_pago, vendedor, transportista, 
                usuarios_id, cliente_ruc_dni
            ) VALUES (
                :tipo_correlativos_id, :serie, :correlativo, :fecha_venta, :provincia, :n_interno, 
                :guia_remision, :sucursal, :almacen, :condicion_pago, :vendedor, :transportista, 
                :usuarios_id, :cliente_ruc_dni
            ) RETURNING id_documento
        """)
        result = db.execute(insert_documento, request_dict)
        db.commit()
        documento_id = result.fetchone()[0]

        #Insertar en la tabla RECLAMOS y obtener fecha_creacion
        insert_reclamo = text("""
            INSERT INTO postventa.reclamos (
                documento_id, usuarios_id, tipo_usuarios_id, dni, nombres, apellidos, email, telefono, 
                detalle_reclamo, estado, fecha_creacion,
                placa_vehiculo, modelo_vehiculo, marca, modelo_motor, anio, tipo_operacion,
                fecha_instalacion, horas_uso_reclamo, 
                km_instalacion, km_actual, km_recorridos
            ) VALUES (
                :documento_id, :usuarios_id, :tipo_usuarios_id, :dni, :nombres, :apellidos, :email, :telefono, 
                :detalle_reclamo, 'Generado', CURRENT_TIMESTAMP,
                :placa_vehiculo, :modelo_vehiculo, :marca, :modelo_motor, :anio, :tipo_operacion,
                :fecha_instalacion, :horas_uso_reclamo, 
                :km_instalacion, :km_actual, :km_recorridos
            ) RETURNING id_reclamo, fecha_creacion
        """)

        # Asignar el ID del documento al diccionario antes de la ejecución
        request_dict["documento_id"] = documento_id

        # Ejecutar la consulta de inserción de RECLAMOS solo una vez
        result = db.execute(insert_reclamo, request_dict)
        db.commit()

        # Obtener el ID del reclamo y la fecha de creación correctamente
        reclamo_id, fecha_creacion = result.fetchone()

        # Agregar la información a `request_dict` para la respuesta
        request_dict["reclamo_id"] = reclamo_id
        request_dict["fecha_creacion"] = fecha_creacion


        #Insertar PRODUCTOS_RECLAMOS
        for producto in request.productos:
            insert_producto = text("""
                INSERT INTO postventa.productos (
                    reclamo_id, itm, lin, org, marc, descrp_marc, fabrica, articulo, descripcion, 
                    precio, cantidad_reclamo, und_reclamo
                ) VALUES (
                    :reclamo_id, :itm, :lin, :org, :marc, :descrp_marc, :fabrica, :articulo, :descripcion, 
                    :precio, :cantidad_reclamo, :und_reclamo
                ) RETURNING id_producto
            """)
            producto_dict = producto.dict()
            producto_dict["reclamo_id"] = reclamo_id
            result = db.execute(insert_producto, producto_dict)
            db.commit()
            producto_id = result.fetchone()[0]  # 🚀 Obtiene id_producto generado automáticamente

        #Insertar ARCHIVOS
        for archivo in request.archivos:
            insert_archivo = text("""
                INSERT INTO postventa.archivos (tipo_formulario, reclamo_id, archivo_url, tipo_archivo)
                VALUES ('Reclamo', :reclamo_id, :archivo_url, :tipo_archivo)
            """)
            archivo_dict = archivo.dict()
            archivo_dict["reclamo_id"] = reclamo_id
            db.execute(insert_archivo, archivo_dict)

        db.commit()

        #Serializar date antes de enviar la respuesta
        response_data = json.loads(json.dumps(request_dict, default=json_serial))

        return JSONResponse(status_code=200, content={"estado": 200, "mensaje": "Reclamo registrado correctamente.", "data": response_data})


    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"estado": 500, "mensaje": f"Error en el servidor: {str(e)}"})

@router.post("/registrar-queja")
def registrar_queja(
    request: QuejaRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    # Obtener usuarios_id desde USUARIOS_TOKENS
    query_token = text("SELECT usuarios_id FROM postventa.usuarios_tokens WHERE token = :token")
    result_token = db.execute(query_token, {"token": token}).fetchone()

    if not result_token:
        return JSONResponse(
            status_code=401, content={"estado": 401, "mensaje": "Token inválido"}
        )

    usuarios_id = result_token[0]

    # Obtener tipo_usuarios_id desde USUARIOS
    query_usuario = text("SELECT tipo_usuarios_id FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()

    if not result_usuario:
        return JSONResponse(
            status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado"}
        )

    tipo_usuarios_id = result_usuario[0]

    # Convertir el request a diccionario y agregar los IDs necesarios
    request_dict = request.model_dump()
    request_dict["usuarios_id"] = usuarios_id
    request_dict["tipo_usuarios_id"] = tipo_usuarios_id

    # Validaciones
    errores = {}

    # Validar campos obligatorios generales
    campos_obligatorios = [
        "tipo_queja", "motivo_queja", "descripcion", "cliente_ruc_dni", "dni",
        "nombres", "apellidos", "email", "telefono"
    ]

    if request_dict["tipo_queja"] == "Servicio":
        campos_obligatorios.append("fecha_queja")
    elif request_dict["tipo_queja"] == "Producto":
        campos_obligatorios.extend([
            "tipo_correlativos_id", "serie", "correlativo", "fecha_venta", "provincia",
            "n_interno", "guia_remision", "sucursal", "almacen", "condicion_pago",
            "vendedor", "transportista"
        ])

    for campo in campos_obligatorios:
        valor = request_dict.get(campo)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            errores[campo] = ["Campo obligatorio"]

    # Validar serie y correlativo según tipo_correlativos_id
    if request_dict["tipo_queja"] == "Producto":
        tipo_correlativos_id = request_dict.get("tipo_correlativos_id", "")
        serie = request_dict.get("serie", "")
        correlativo = request_dict.get("correlativo", "")

        if tipo_correlativos_id in [1, 2]:
            if not serie or len(serie) != 4:
                errores["serie"] = ["La serie debe tener exactamente 4 caracteres."]
            if not correlativo or len(correlativo) != 8:
                errores["correlativo"] = ["El correlativo debe tener exactamente 8 dígitos."]
        elif tipo_correlativos_id == 3:
            if serie:
                errores["serie"] = ["No debe incluir una serie."]
            if not correlativo or len(correlativo) != 7:
                errores["correlativo"] = ["El correlativo debe tener exactamente 7 dígitos."]

    # Validar productos si tipo_queja es Producto
    if request_dict["tipo_queja"] == "Producto":
        productos = request_dict.get("productos", [])
        if not productos:
            errores["productos"] = ["Debe agregar un producto"]
        else:
            for producto in productos:
                for campo in [
                    "itm", "lin", "org", "marc", "descrp_marc", "fabrica",
                    "articulo", "descripcion", "precio", "cantidad_reclamo", "und_reclamo"
                ]:
                    valor = producto.get(campo)
                    if valor is None or (isinstance(valor, str) and not valor.strip()):
                        errores.setdefault(campo, []).append("Campo obligatorio")

    # Validar archivos
    archivos = request_dict.get("archivos", [])
    if not archivos:
        errores["archivos"] = ["Debe agregar al menos un archivo adjunto"]
    else:
        for archivo in archivos:
            for campo in ["archivo_url", "tipo_archivo"]:
                if not archivo.get(campo, "").strip():
                    errores.setdefault(f"archivos.{campo}", []).append("Campo obligatorio")

    # Si hay errores, devolverlos en un solo response
    if errores:
        return JSONResponse(
            status_code=422,
            content={"errores": errores, "estado": 422, "mensaje": "No es posible procesar los datos enviados."}
        )

    try:
        documento_id = None

        if request_dict["tipo_queja"] == "Producto":
            # ✅ Insertar en documentos
            insert_documento = text("""
                INSERT INTO postventa.documentos (
                    tipo_correlativos_id, serie, correlativo, fecha_venta, provincia, n_interno, 
                    guia_remision, sucursal, almacen, condicion_pago, vendedor, transportista, 
                    usuarios_id, cliente_ruc_dni
                ) VALUES (
                    :tipo_correlativos_id, :serie, :correlativo, :fecha_venta, :provincia, :n_interno, 
                    :guia_remision, :sucursal, :almacen, :condicion_pago, :vendedor, :transportista, 
                    :usuarios_id, :cliente_ruc_dni
                ) RETURNING id_documento
            """)
            result = db.execute(insert_documento, request_dict)
            documento_id = result.fetchone()[0]
            request_dict["documento_id"] = documento_id

        # ✅ Definir el valor de `tipog` automáticamente
        tipog = "G1" if request_dict["tipo_queja"] == "Producto" else "G2"
        request_dict["tipog"] = tipog

        # ✅ Insertar en quejas
        estado = "Generado" if request_dict["tipo_queja"] == "Producto" else "Registrada"
        insert_queja_sql = """
            INSERT INTO postventa.quejas (
                usuarios_id, tipo_usuarios_id, tipo_queja, tipog, motivo_queja, fecha_queja, descripcion,
                cliente_ruc_dni, dni_solicitante, nombre, apellido, email, telefono,
                estado, fecha_creacion
            ) VALUES (
                :usuarios_id, :tipo_usuarios_id, :tipo_queja, :tipog, :motivo_queja, :fecha_queja, :descripcion,
                :cliente_ruc_dni, :dni, :nombres, :apellidos, :email, :telefono,
                :estado, CURRENT_TIMESTAMP
            ) RETURNING id_queja, fecha_creacion
        """

        if request_dict["tipo_queja"] == "Producto":
            insert_queja_sql = """
                INSERT INTO postventa.quejas (
                    documento_id, usuarios_id, tipo_usuarios_id, tipo_queja, tipog, motivo_queja, fecha_queja, descripcion,
                    cliente_ruc_dni, dni_solicitante, nombre, apellido, email, telefono,
                    estado, fecha_creacion
                ) VALUES (
                    :documento_id, :usuarios_id, :tipo_usuarios_id, :tipo_queja, :tipog, :motivo_queja, :fecha_queja, :descripcion,
                    :cliente_ruc_dni, :dni, :nombres, :apellidos, :email, :telefono,
                    :estado, CURRENT_TIMESTAMP
                ) RETURNING id_queja, fecha_creacion
            """
        else:
            insert_queja_sql = """
                INSERT INTO postventa.quejas (
                    usuarios_id, tipo_usuarios_id, tipo_queja, tipog, motivo_queja, fecha_queja, descripcion,
                    cliente_ruc_dni, dni_solicitante, nombre, apellido, email, telefono,
                    estado, fecha_creacion
                ) VALUES (
                    :usuarios_id, :tipo_usuarios_id, :tipo_queja, :tipog, :motivo_queja, :fecha_queja, :descripcion,
                    :cliente_ruc_dni, :dni, :nombres, :apellidos, :email, :telefono,
                    :estado, CURRENT_TIMESTAMP
                ) RETURNING id_queja, fecha_creacion
            """

            #Asegurarse de que tipo_documento_id NO se agregue accidentalmente
            insert_queja_sql = insert_queja_sql.replace("tipo_documento_id,", "").replace(":tipo_documento_id,", "")


        request_dict["estado"] = estado

        # ✅ Convertir a objeto text() antes de ejecutar
        result = db.execute(text(insert_queja_sql), request_dict)
        queja_id, fecha_creacion = result.fetchone()
        request_dict["queja_id"] = queja_id
        request_dict["fecha_creacion"] = fecha_creacion.isoformat()

        # ✅ Insertar en productos_reclamos si tipo_queja es Producto
        if request_dict["tipo_queja"] == "Producto":
            insert_producto = text("""
                INSERT INTO postventa.productos (
                    queja_id, itm, lin, org, marc, descrp_marc, fabrica, articulo, descripcion, 
                    precio, cantidad_reclamo, und_reclamo
                ) VALUES (
                    :queja_id, :itm, :lin, :org, :marc, :descrp_marc, :fabrica, :articulo, :descripcion, 
                    :precio, :cantidad_reclamo, :und_reclamo
                )
            """)

            producto_dict = request_dict["productos"][0]
            producto_dict["queja_id"] = queja_id
            db.execute(insert_producto, producto_dict)

        # ✅ Insertar en archivos con tipo_formulario = "Queja"
        for archivo in archivos:
            insert_archivo = text("""
                INSERT INTO postventa.archivos (
                    tipo_formulario, queja_id, archivo_url, tipo_archivo
                ) VALUES (
                    'Queja', :queja_id, :archivo_url, :tipo_archivo
                )
            """)

            archivo_data = {
                "queja_id": queja_id,
                "archivo_url": archivo["archivo_url"],
                "tipo_archivo": archivo["tipo_archivo"]
            }
            db.execute(insert_archivo, archivo_data)

        db.commit()
        # ✅ Filtrar los valores `None` de la respuesta antes de enviarla
        response_data = {k: v for k, v in request_dict.items() if v is not None}

        return JSONResponse(
            status_code=200,
            content={"estado": 200, "mensaje": "Queja registrada correctamente.", "data": response_data}
        )

    except Exception as e:
        db.rollback()
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
        key = f"{serie}-{correlativo}"
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
        key = correlativo
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

    # Buscar en la data simulada según el tipo de documento y la clave construida
    documento_info = simulated_docs.get(doc_type, {}).get(key)
    if not documento_info:
        return JSONResponse(
            status_code=422,
            content={
                "errores": {"documento": [f"No existe documento con {'serie y correlativo' if tipo_documento in [1,2] else 'correlativo'} especificado."]},
                "estado": 422,
                "mensaje": "No es posible procesar los datos enviados."
            }
        )

    return JSONResponse(content={"data": documento_info})
