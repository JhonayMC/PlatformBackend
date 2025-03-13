from fastapi_mail import FastMail, MessageSchema, MessageType
from app.config import settings, conf 
import logging
import os

logger = logging.getLogger(__name__)

async def enviar_correo(destinatario: str, codigo: str):
    message = MessageSchema(
        subject="Código de Recuperación",
        recipients=[destinatario],
        body=f"Tu código de recuperación es: {codigo}. Este código expira en 5 minutos.",
        subtype="plain"
    )
    try:
        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info("✅ Correo enviado correctamente.")
        return True  # 🔹 Ahora retorna True si el envío fue exitoso
    except Exception as e:
        logger.error(f"❌ Error enviando correo: {e}")
        return False  # 🔹 Retorna False si hay un error
    
    
async def enviar_correo_reclamo(destinatario: str, nombre_cliente: str, reclamo_id: int):
    """
    Envía un correo al cliente con el PDF del reclamo adjunto.
    """
    pdf_filename = f"R_{reclamo_id}.pdf"
    pdf_path = os.path.join("uploads/pdfs", pdf_filename)  # Ruta donde se guardó el PDF

    # Verifica si el archivo PDF existe antes de adjuntar
    if not os.path.exists(pdf_path):
        logger.error(f"❌ No se encontró el archivo PDF {pdf_path}. No se enviará el correo.")
        return False

    message = MessageSchema(
        subject=f"Reclamo N° R{reclamo_id:05d} Generado",
        recipients=[destinatario],
        cc=["postventa@mym.com.pe"],  # Correo en CC
        body=f"""
        Estimado/a {nombre_cliente},

        Hacemos de su conocimiento que el reclamo ya se encuentra registrado en nuestra base de datos, por lo que nos encontramos a la espera del envío del producto para continuar con la siguiente fase del proceso.

        Recuerde que el plazo de envío es de 24 hrs desde la fecha de registro del reclamo.

        Una vez recepcionado el producto, se le notificará mediante WhatsApp.

        Atentamente,
        Equipo de Postventa de M&M Repuestos y Servicios S.A
        """,
        subtype=MessageType.plain,
        attachments=[pdf_path]  # Adjuntar el PDF
    )

    try:
        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info(f"✅ Correo enviado correctamente a {destinatario}")
        return True
    except Exception as e:
        logger.error(f"❌ Error enviando correo: {e}")
        return False
