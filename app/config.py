import os
from pydantic_settings import BaseSettings, SettingsConfigDict

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
TOKEN_EXPIRE_HOURS = 3  # Para el vencimiento del token en la BD

# Configuración de CORS
CORS_ORIGINS = [
    'http://localhost:5174',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:5175'
]

from fastapi_mail import ConnectionConfig
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()   

conf = ConnectionConfig( 
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
)

