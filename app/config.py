import os
from pydantic_settings import BaseSettings, SettingsConfigDict

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
TOKEN_EXPIRE_HOURS = 3  # Para el vencimiento del token en la BD

# Configuración de CORS
CORS_ORIGINS = [
    "http://localhost:5174",
    "http://localhost:5173",
    "http://localhost:5175"
]

# Configuración para envío de correos
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
