import threading
import requests
import datetime
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from sqlalchemy import text
import pdfkit
import asyncio 
import httpx
import logging
import time
from app.services.email_service import enviar_correo_reclamo  
logger = logging.getLogger(__name__)

UPLOADS_PDFS = "uploads/pdfs"  # Ruta donde se guardan los PDFs

def generar_pdf_background(reclamo_id: int, token: str, db_session):
    """
    Función que se ejecuta en segundo plano para generar un PDF sin bloquear la API principal.
    """
    with db_session() as db:
        # 🔹 Obtener datos del reclamo o queja
        query_reclamo = text("""
            SELECT f.tipo_correlativos_id, tc.nombre AS tipo_correlativo_nombre, 
                   f.motivos_producto_id, mp.nombre AS motivo_producto_nombre, 
                   f.serie, f.correlativo, f.cliente, f.dni, f.nombres, f.apellidos, 
                   f.email, f.telefono, f.producto_id, f.producto_cantidad, f.fecha_creacion,
                   f.detalle_reclamo, f.reclamo, f.queja_producto,
                   f.placa_vehiculo, f.marca, f.modelo_vehiculo, f.anio, f.modelo_motor,
                   f.tipo_operacion_id, tp.nombre AS tipo_operacion_nombre,
                   f.fecha_instalacion, f.horas_uso_reclamo, f.km_instalacion, f.km_actual
            FROM postventa.formularios f
            LEFT JOIN postventa.tipo_correlativos tc ON f.tipo_correlativos_id = tc.id
            LEFT JOIN postventa.motivos_producto mp ON f.motivos_producto_id = mp.id
            LEFT JOIN postventa.tipo_operaciones tp ON f.tipo_operacion_id = tp.id
            WHERE f.id = :reclamo_id
        """)
        
        result_reclamo = db.execute(query_reclamo, {"reclamo_id": reclamo_id}).fetchone()

        if not result_reclamo:
            print(f"❌ Error: Reclamo {reclamo_id} no encontrado en la base de datos")
            return

        datos_reclamo = dict(result_reclamo._mapping)

        # 🔹 Determinar si es un RECLAMO o una QUEJA
        es_reclamo = datos_reclamo["reclamo"] == 1
        tipo_reporte = "Reclamo" if es_reclamo else "Queja_Producto"

        # Buscar imágenes en la tabla archivos (máximo 2)
        query_imagenes = text("""
            SELECT archivo_url FROM postventa.archivos 
            WHERE formulario_id = :reclamo_id AND LOWER(tipo_archivo) IN ('jpg', 'png')
            ORDER BY id_archivo DESC LIMIT 2
        """)

        result_imagenes = db.execute(query_imagenes, {"reclamo_id": reclamo_id}).fetchall()

        imagenes = [row[0] for row in result_imagenes]

        print(f"🖼️ Imágenes recuperadas para el reclamo {reclamo_id}: {imagenes}")  


        # 🔹 Determinar la URL de `buscar-documento`
        tipo_documento = datos_reclamo["tipo_correlativos_id"]
        serie = datos_reclamo.get("serie", "")
        correlativo = datos_reclamo["correlativo"]

        buscar_doc_url = f"http://localhost:8001/api/v1/buscar-documento?tipo_documento={tipo_documento}"
        if tipo_documento in [1, 2]:
            buscar_doc_url += f"&serie={serie}&correlativo={correlativo}"
        else:
            buscar_doc_url += f"&correlativo={correlativo}"

        headers = {"Authorization": f"Bearer {token}"}

        # 🔹 Llamar a `buscar-documento` en un hilo separado para evitar bloqueos
        def fetch_document_data():
            try:
                response = requests.get(buscar_doc_url, headers=headers, timeout=5)
                doc_data = response.json().get("data", {})
            except Exception as e:
                doc_data = {"estado": 500, "mensaje": f"Error al buscar documento: {str(e)}"}

            # 🔹 Filtrar solo el producto específico según `producto_id`
            producto_id = datos_reclamo["producto_id"]
            productos = doc_data.get("productos", [])

            producto_filtrado = next((p for p in productos if p.get("codigo") == producto_id), None)

            # 🔹 Limpiar los productos y solo dejar el seleccionado
            doc_data["productos"] = [producto_filtrado] if producto_filtrado else []

            generar_pdf_con_datos(datos_reclamo, doc_data, reclamo_id, tipo_reporte, es_reclamo, imagenes, db)

        thread = threading.Thread(target=fetch_document_data)
        thread.start()

from jinja2 import Environment, FileSystemLoader
import pdfkit
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Subir un nivel desde 'services'


TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")



def generar_pdf_con_datos(datos_reclamo, doc_data, reclamo_id, tipo_reporte, es_reclamo, imagenes, db):
    """
    Función que genera el PDF usando una plantilla HTML y lo convierte en PDF.
    """
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template_name = "reclamo_template.html" if es_reclamo else "queja_producto.html"
    template = env.get_template(template_name)

    # Fusionar datos
    datos_finales = {**datos_reclamo, **doc_data}
    datos_finales.update({
        "reclamo_id": reclamo_id,
        "fecha_creacion": datos_reclamo["fecha_creacion"].strftime('%Y-%m-%d'),
        "producto": doc_data.get("productos", [{}])[0],
        "imagenes": imagenes
    })


    # Renderizar el HTML con los datos finales
    html_content = template.render(datos_finales)

    # Configurar la ruta de wkhtmltopdf manualmente
    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

    # Generar PDF
    pdf_filename = f"R_{reclamo_id}.pdf"
    pdf_path = os.path.join(UPLOADS_PDFS, pdf_filename)

    options = {
        "enable-local-file-access": ""  # Permite que wkhtmltopdf acceda a archivos locales
    }

    pdfkit.from_string(html_content, pdf_path, configuration=config, options=options)

    print(f"📄 PDF generado correctamente: {pdf_path}")

    # 🔹 Guardar en la base de datos la URL del PDF generado
    archivo_url = f"http://localhost:8001/uploads/pdfs/{pdf_filename}"

    try:
        insert_query = text("""
            INSERT INTO postventa.archivos (formulario_id, archivo_url, tipo_archivo) 
            VALUES (:formulario_id, :archivo_url, :tipo_archivo)
        """)

        db.execute(insert_query, {
            "formulario_id": reclamo_id,
            "archivo_url": archivo_url,
            "tipo_archivo": "PDF"
        })
        db.commit()

        print(f"✅ PDF guardado en la base de datos con URL: {archivo_url}")

        # 🔹 Una vez guardado el PDF, obtenemos el correo del usuario y enviamos el email
        query_correo = text("SELECT email, cliente FROM postventa.formularios WHERE id = :reclamo_id")
        result_correo = db.execute(query_correo, {"reclamo_id": reclamo_id}).fetchone()

        if result_correo:
            email_usuario, cliente = result_correo
            print(f"📧 Enviando correo a {email_usuario} con el PDF adjunto.")

            # 🔹 Manejo correcto del event loop
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(enviar_correo_reclamo(email_usuario, cliente, reclamo_id))
            except RuntimeError:
                asyncio.run(enviar_correo_reclamo(email_usuario, cliente, reclamo_id))

    except Exception as e:
        print(f"❌ Error al insertar en la base de datos: {str(e)}")


async def buscar_documento_background(url: str, token: str):
    """
    Función que se ejecuta en segundo plano para buscar un documento sin bloquear la API principal.
    """
    logger.info(f"Iniciando búsqueda en background: {url}")
    try:
        # Usar timeout para evitar bloqueos indefinidos
        logger.info("Enviando solicitud a API externa...")
        response = await httpx.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        data = response.json()
        logger.info(f"✅ Respuesta de API externa recibida en {time.time()}s")
        return data
    except Exception as e:
        logger.error(f"❌ Error al buscar documento en background: {str(e)}")
        return {"estado": 500, "mensaje": f"Error al buscar documento: {str(e)}"}
