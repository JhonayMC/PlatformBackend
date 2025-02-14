from pydantic import BaseModel, EmailStr
from typing import Optional

class UsuarioLogin(BaseModel):
    usuario: Optional[str] = None
    contrasena: Optional[str] = None

class RegistrarUsuarioRequest(BaseModel):
    tipo_usuarios_id: int
    tipo_documentos_id: int
    documento: str
    nombre_completo: str
    correo: EmailStr
    contrasena: str
    recontrasena: str

class CambiarContrasenaRequest(BaseModel):
    usuarios_id: Optional[int] = None
    contrasena: Optional[str] = None
    recontrasena: Optional[str] = None

class ObtenerCodigoRequest(BaseModel):
    correo: str

class RecuperarContrasenaRequest(BaseModel):
    correo: str
    codigo: str
    contrasena: str
    recontrasena: str
