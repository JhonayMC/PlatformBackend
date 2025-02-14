from fastapi_mail import FastMail, MessageSchema
from app.config import settings, conf 
import logging

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
