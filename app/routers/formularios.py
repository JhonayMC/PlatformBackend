from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.models.formularios import ReclamoRequest, QuejaRequest, ConsultarEstadoRequest, simulated_docs 
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
    query_usuario = text("SELECT tipo_usuarios_id, empresa_id FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()

    if not result_usuario:
        return JSONResponse(status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado"})

    tipo_usuarios_id, empresa_id = result_usuario

    #Validamos si es trabajador o cliente
    es_trabajador = empresa_id is not None

    # Validar que los campos obligatorios NO estén vacíos
    errores = {}
    if isinstance(request, dict):
        request_dict = request
    else:
        request_dict = request.dict()

    campos_obligatorios = [
        "tipo_correlativos_id", "correlativo", "fecha_venta", "provincia",
        "n_interno", "guia_remision", "sucursal", "almacen", "condicion_pago",
        "vendedor", "transportista", "cliente_ruc_dni", "dni", "nombres",
        "apellidos", "email", "telefono", "placa_vehiculo", "modelo_vehiculo",
        "marca", "modelo_motor", "anio", "tipo_operacion_id", "fecha_instalacion", "horas_uso_reclamo", "km_instalacion",
        "km_actual", "km_recorridos", "detalle_reclamo"
    ]
    # Si es trabajador, validar los nuevos campos
    if es_trabajador:
        nuevos_campos_reclamos = ["clasificacion_venta", "potencial_venta", "producto_tienda"]
        for campo in nuevos_campos_reclamos:
            # Imprime para depuración
            print(f"Campo {campo}: {request_dict.get(campo)}")
            if campo not in request_dict or request_dict.get(campo) is None or str(request_dict.get(campo)).strip() == "":
                errores.setdefault(campo, []).append("Campo obligatorio para trabajadores")

        # Validar `precio` en productos
        productos = request_dict.get("productos", [])
        if not productos:
            errores.setdefault("productos", []).append("Debe agregar al menos un producto")
        else:
            for i, producto in enumerate(productos):
                # Imprime para depuración
                print(f"Producto {i}, precio: {producto.get('precio')}")
                if "precio" not in producto or producto.get("precio") is None or str(producto.get("precio")).strip() == "":
                    errores.setdefault("precio", []).append("Campo obligatorio para trabajadores en productos")

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
            for campo in ["itm", "lin", "org", "marc", "descrp_marc", "fabrica", "articulo", "descripcion", "cantidad_reclamo", "und_reclamo"]:
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
        if isinstance(request, dict):
            request_dict = request
        else:
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
        if es_trabajador:
            insert_reclamo = text("""
                INSERT INTO postventa.reclamos (
                    documento_id, usuarios_id, tipo_usuarios_id, dni, nombres, apellidos, email, telefono, 
                    detalle_reclamo, estado, fecha_creacion,
                    placa_vehiculo, modelo_vehiculo, marca, modelo_motor, anio, tipo_operacion_id,
                    fecha_instalacion, horas_uso_reclamo, 
                    km_instalacion, km_actual, km_recorridos,
                    clasificacion_venta, potencial_venta, producto_tienda
                ) VALUES (
                    :documento_id, :usuarios_id, :tipo_usuarios_id, :dni, :nombres, :apellidos, :email, :telefono, 
                    :detalle_reclamo, 'Generado', CURRENT_TIMESTAMP,
                    :placa_vehiculo, :modelo_vehiculo, :marca, :modelo_motor, :anio, :tipo_operacion_id,
                    :fecha_instalacion, :horas_uso_reclamo, 
                    :km_instalacion, :km_actual, :km_recorridos,
                    :clasificacion_venta, :potencial_venta, :producto_tienda
                ) RETURNING id_reclamo, fecha_creacion
            """)
        else:
            insert_reclamo = text("""
                INSERT INTO postventa.reclamos (
                    documento_id, usuarios_id, tipo_usuarios_id, dni, nombres, apellidos, email, telefono, 
                    detalle_reclamo, estado, fecha_creacion,
                    placa_vehiculo, modelo_vehiculo, marca, modelo_motor, anio, tipo_operacion_id,
                    fecha_instalacion, horas_uso_reclamo, 
                    km_instalacion, km_actual, km_recorridos
                ) VALUES (
                    :documento_id, :usuarios_id, :tipo_usuarios_id, :dni, :nombres, :apellidos, :email, :telefono, 
                    :detalle_reclamo, 'Generado', CURRENT_TIMESTAMP,
                    :placa_vehiculo, :modelo_vehiculo, :marca, :modelo_motor, :anio, :tipo_operacion_id,
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
        if es_trabajador:
            insert_producto = text("""
                INSERT INTO postventa.productos (
                    reclamo_id, itm, lin, org, marc, descrp_marc, fabrica, articulo, descripcion, 
                    precio, cantidad_reclamo, und_reclamo
                ) VALUES (
                    :reclamo_id, :itm, :lin, :org, :marc, :descrp_marc, :fabrica, :articulo, :descripcion, 
                    :precio, :cantidad_reclamo, :und_reclamo
                ) RETURNING id_producto
            """)
        else:
            insert_producto = text("""
                INSERT INTO postventa.productos (
                    reclamo_id, itm, lin, org, marc, descrp_marc, fabrica, articulo, descripcion, 
                    cantidad_reclamo, und_reclamo
                ) VALUES (
                    :reclamo_id, :itm, :lin, :org, :marc, :descrp_marc, :fabrica, :articulo, :descripcion, 
                    :cantidad_reclamo, :und_reclamo
                ) RETURNING id_producto
            """)

        # Corregido: Sacando el bucle fuera del condicional para que siempre se ejecute
        for producto in request_dict["productos"]:
            if isinstance(producto, dict):
                producto_dict = producto
            else:
                producto_dict = producto.dict()
            producto_dict["reclamo_id"] = reclamo_id
            result = db.execute(insert_producto, producto_dict)
            db.commit()
            producto_id = result.fetchone()[0] # 🚀 Obtiene id_producto generado automáticamente

        #Insertar ARCHIVOS
        for archivo in request.archivos:
            insert_archivo = text("""
                INSERT INTO postventa.archivos (tipo_formulario, reclamo_id, archivo_url, tipo_archivo)
                VALUES ('Reclamo', :reclamo_id, :archivo_url, :tipo_archivo)
            """)
            for archivo in request_dict["archivos"]:
                if isinstance(archivo, dict):
                    archivo_dict = archivo
                else:
                    archivo_dict = archivo.dict()
                archivo_dict["reclamo_id"] = reclamo_id
                db.execute(insert_archivo, archivo_dict)

        db.commit()

        #Serializar date antes de enviar la respuesta
        response_data = json.loads(json.dumps(request_dict, default=json_serial))

        # Limpiar el reclamo_id de cada producto y archivo en la respuesta
        if "productos" in response_data:
            for producto in response_data["productos"]:
                if "reclamo_id" in producto:
                    del producto["reclamo_id"]

        if "archivos" in response_data:
            for archivo in response_data["archivos"]:
                if "reclamo_id" in archivo:
                    del archivo["reclamo_id"]

        # Agregar los nuevos campos en la respuesta si es trabajador
        if es_trabajador:
            response_data["clasificacion_venta"] = request_dict["clasificacion_venta"]
            response_data["potencial_venta"] = request_dict["potencial_venta"]
            response_data["producto_tienda"] = request_dict["producto_tienda"]

        return JSONResponse(status_code=200, content={"estado": 200, "mensaje": "Reclamo registrado correctamente.", "data": response_data})

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"estado": 500, "mensaje": f"Error en el servidor: {str(e)}"})

@router.get("/consultar-estado-reclamo-queja")
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

    # Si el usuario NO es trabajador, obtener todos sus reclamos y quejas
    if empresa_id is None:
        query_reclamos = text("""
            SELECT 
                'R' || id_reclamo AS id, detalle_reclamo, fecha_creacion
            FROM postventa.reclamos
            WHERE usuarios_id = :usuarios_id
        """)

        query_quejas = text("""
            SELECT 
                'Q' || id_queja AS id, motivo_queja, fecha_creacion
            FROM postventa.quejas
            WHERE usuarios_id = :usuarios_id
        """)

        # Ejecutar ambas consultas
        result_reclamos = db.execute(query_reclamos, {"usuarios_id": usuarios_id}).fetchall()
        result_quejas = db.execute(query_quejas, {"usuarios_id": usuarios_id}).fetchall()

        # Convertir los resultados a diccionarios con la fecha formateada
        reclamos = [{"id": row[0], "detalle_reclamo": row[1], "fecha_creacion": row[2].strftime("%d/%m/%Y %H:%M")} for row in result_reclamos]
        quejas = [{"id": row[0], "motivo_queja": row[1], "fecha_creacion": row[2].strftime("%d/%m/%Y %H:%M")} for row in result_quejas]

        # Combinar y ordenar por fecha_creacion DESC
        data_completa = sorted(reclamos + quejas, key=lambda x: x["fecha_creacion"], reverse=True)

        return JSONResponse(
            status_code=200,
            content={"estado": 200, "mensaje": "Consulta exitosa.", "data": data_completa}
        )

    # Si el usuario es trabajador, aquí manejaríamos la lógica específica (veremos después)
    return JSONResponse(
        status_code=400, content={"estado": 400, "mensaje": "Acción no permitida para trabajadores en esta etapa."}
    )

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
    query_usuario = text("SELECT tipo_usuarios_id, empresa_id FROM postventa.usuarios WHERE id = :usuarios_id")
    result_usuario = db.execute(query_usuario, {"usuarios_id": usuarios_id}).fetchone()

    if not result_usuario:
        return JSONResponse(
            status_code=401, content={"estado": 401, "mensaje": "Usuario no encontrado"}
        )

    tipo_usuarios_id, empresa_id = result_usuario

    # Validamos si es cliente o trabajador
    es_trabajador = empresa_id is not None

    # Convertir el request a diccionario y agregar los IDs necesarios
    request_dict = request.model_dump()
    request_dict["usuarios_id"] = usuarios_id
    request_dict["tipo_usuarios_id"] = tipo_usuarios_id

    # Validaciones
    errores = {}

    # Validar campos obligatorios generales
    campos_obligatorios = [
        "tipo_queja", "descripcion", "cliente_ruc_dni", "dni",
        "nombres", "apellidos", "email", "telefono"
    ]

    # Añadir validaciones adicionales para trabajadores
    if es_trabajador:
        if request_dict["tipo_queja"] == "Producto":
            campos_obligatorios.extend([
                "clasificacion_venta", "potencial_venta", "producto_tienda"
            ])
            # Validar precio en productos
            if "productos" in request_dict and request_dict["productos"]:
                for producto in request_dict["productos"]:
                    if not producto.get("precio"):
                        errores.setdefault("precio", []).append("Campo obligatorio para trabajadores")
        elif request_dict["tipo_queja"] == "Servicio":
            campos_obligatorios.extend([
                "clasificacion_venta", "potencial_venta"
            ])

    if request_dict["tipo_queja"] == "Servicio":
        campos_obligatorios.extend(["fecha_queja","motivos_servicio_id"])
    elif request_dict["tipo_queja"] == "Producto":
        campos_obligatorios.extend([
            "tipo_correlativos_id", "serie", "correlativo","motivos_producto_id", "fecha_venta", "provincia",
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
                campos_producto = [
                    "itm", "lin", "org", "marc", "descrp_marc", "fabrica",
                    "articulo", "descripcion", "cantidad_reclamo", "und_reclamo"
                ]
                
                # Si es trabajador, validar que tenga precio
                if es_trabajador:
                    campos_producto.append("precio")
                
                for campo in campos_producto:
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
            # Insertar en documentos
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

        # Definir el valor de `tipog` automáticamente
        tipog = "G1" if request_dict["tipo_queja"] == "Producto" else "G2"
        request_dict["tipog"] = tipog

        # Insertar en quejas
        estado = "Generado" if request_dict["tipo_queja"] == "Producto" else "Registrada"

        # Construcción dinámica de la consulta SQL según tipo de usuario y tipo de queja
        insert_queja_fields = [
            "usuarios_id", "tipo_usuarios_id", "tipo_queja", "tipog",
            "descripcion", "cliente_ruc_dni", "dni_solicitante", "nombre", "apellido",
            "email", "telefono", "estado", "fecha_creacion"
        ]

        insert_queja_values = [
            ":usuarios_id", ":tipo_usuarios_id", ":tipo_queja", ":tipog",
            ":descripcion", ":cliente_ruc_dni", ":dni", ":nombres", ":apellidos",
            ":email", ":telefono", ":estado", "CURRENT_TIMESTAMP"
        ]

        # Añadir documento_id si tipo_queja es Producto
        if request_dict["tipo_queja"] == "Producto":
            insert_queja_fields.insert(0, "documento_id")
            insert_queja_values.insert(0, ":documento_id")

            insert_queja_fields.append("motivos_producto_id")
            insert_queja_values.append(":motivos_producto_id")

            # Añadir fecha_venta
            insert_queja_fields.append("fecha_venta")
            insert_queja_values.append(":fecha_venta")

        elif request_dict["tipo_queja"] == "Servicio":
            insert_queja_fields.append("motivos_servicio_id")
            insert_queja_values.append(":motivos_servicio_id")
            # Añadir fecha_queja
            insert_queja_fields.append("fecha_queja")
            insert_queja_values.append(":fecha_queja")

        # Añadir campos adicionales para trabajadores
        if es_trabajador:
            insert_queja_fields.extend(["clasificacion_venta", "potencial_venta"])
            insert_queja_values.extend([":clasificacion_venta", ":potencial_venta"])

            if request_dict["tipo_queja"] == "Producto":
                insert_queja_fields.append("producto_tienda")
                insert_queja_values.append(":producto_tienda")

        # Construir la consulta SQL
        insert_queja_sql = f"""
            INSERT INTO postventa.quejas (
                {', '.join(insert_queja_fields)}
            ) VALUES (
                {', '.join(insert_queja_values)}
            ) RETURNING id_queja, fecha_creacion
        """

        request_dict["estado"] = estado

        # Convertir a objeto text() antes de ejecutar
        result = db.execute(text(insert_queja_sql), request_dict)
        queja_id, fecha_creacion = result.fetchone()
        request_dict["queja_id"] = queja_id
        request_dict["fecha_creacion"] = fecha_creacion.isoformat()


        # Insertar en productos_reclamos si tipo_queja es Producto
        if request_dict["tipo_queja"] == "Producto":
            # Determinar los campos a insertar basados en si es trabajador o no
            producto_fields = [
                "queja_id", "itm", "lin", "org", "marc", "descrp_marc", "fabrica", 
                "articulo", "descripcion", "cantidad_reclamo", "und_reclamo"
            ]
            producto_values = [
                ":queja_id", ":itm", ":lin", ":org", ":marc", ":descrp_marc", ":fabrica", 
                ":articulo", ":descripcion", ":cantidad_reclamo", ":und_reclamo"
            ]
            
            # Añadir precio si es trabajador
            if es_trabajador:
                producto_fields.append("precio")
                producto_values.append(":precio")
            
            insert_producto_sql = f"""
                INSERT INTO postventa.productos (
                    {', '.join(producto_fields)}
                ) VALUES (
                    {', '.join(producto_values)}
                )
            """

            producto_dict = request_dict["productos"][0]
            producto_dict["queja_id"] = queja_id
            db.execute(text(insert_producto_sql), producto_dict)

        # Insertar en archivos con tipo_formulario = "Queja"
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
        # Filtrar los valores `None` de la respuesta antes de enviarla
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
