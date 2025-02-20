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
    tipo_documento: str = Field(..., pattern="^(Factura|Boleta|Nota de Venta)$")  # Cambio aquí
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
    clasificacion_venta: Optional[str]
    potencial_venta: Optional[str]
    fecha_instalacion: Optional[date]
    horas_uso_reclamo: Optional[int]
    km_instalacion: Optional[int]
    km_actual: Optional[int]
    km_recorridos: Optional[int]
    detalle_reclamo: str
    productos: List[ProductoReclamoRequest]
    archivos: List[ArchivoRequest]
