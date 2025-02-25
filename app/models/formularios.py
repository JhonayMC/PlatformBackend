from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# Modelo para la carga de archivos
class ArchivoRequest(BaseModel):
    archivo_url: str
    tipo_archivo: str = Field(..., pattern="^(JPG|PNG|MP4|PDF|DOC)$")  # Cambio aquí

# Modelo para productos afectados en el reclamo
class ProductoReclamoRequest(BaseModel):
    itm: str
    lin: str
    org: str
    marc: str
    descrp_marc: str
    fabrica: str
    articulo: str
    descripcion: str
    precio: float
    cantidad_reclamo: int
    und_reclamo: str

# Modelo principal para guardar reclamos
class ReclamoRequest(BaseModel):
    tipo_correlativos_id: int    
    serie: Optional[str] = Field(None, min_length=4, max_length=4)
    correlativo: str = Field(..., min_length=7, max_length=8)
    fecha_venta: date
    provincia: str
    n_interno: str
    guia_remision: Optional[str]
    sucursal: str
    almacen: str
    condicion_pago: str
    vendedor: str
    transportista: Optional[str]
    cliente_ruc_dni: str
    dni: str
    nombres: str
    apellidos: str
    email: str
    telefono: str
    placa_vehiculo: Optional[str]
    modelo_vehiculo: Optional[str]
    marca: Optional[str]
    modelo_motor: Optional[str]
    anio: Optional[int]
    tipo_operacion: str
    fecha_instalacion: Optional[date]
    horas_uso_reclamo: Optional[int]
    km_instalacion: Optional[int]
    km_actual: Optional[int]
    km_recorridos: Optional[int]
    detalle_reclamo: str
    productos: List[ProductoReclamoRequest]
    archivos: List[ArchivoRequest]

class ProductoRequest(BaseModel):
    itm: str
    lin: str
    org: str
    marc: str
    descrp_marc: str
    fabrica: str
    articulo: str
    descripcion: str
    precio: float
    cantidad_reclamo: int
    und_reclamo: str

class QuejaRequest(BaseModel):
    tipo_queja: str
    motivo_queja: str
    descripcion: str
    cliente_ruc_dni: str
    dni: str
    nombres: str
    apellidos: str
    email: str
    telefono: str
    #tipog: str
    # Campos opcionales para tipo "Servicio"
    fecha_queja: Optional[str] = None
    # Campos opcionales para tipo "Producto"
    tipo_correlativos_id: Optional[int] = None
    serie: Optional[str] = None
    correlativo: Optional[str] = None
    fecha_venta: Optional[str] = None
    provincia: Optional[str] = None
    n_interno: Optional[str] = None
    guia_remision: Optional[str] = None
    sucursal: Optional[str] = None
    almacen: Optional[str] = None
    condicion_pago: Optional[str] = None
    vendedor: Optional[str] = None
    transportista: Optional[str] = None
    productos: Optional[List[ProductoRequest]] = None
    archivos: List[ArchivoRequest]
