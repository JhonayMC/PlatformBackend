from pydantic import BaseModel
from typing import Optional
from fastapi import UploadFile

class GuiaCreateRequest(BaseModel):
    fecha_llegada: str 

class EnTiendaUpdate(BaseModel):
    en_tienda: bool

class ComentarioCreate(BaseModel):
    comentario: str

class CierreFormulario(BaseModel):
    origen: int
    detalle: str
