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
    precio: Optional[float] = None
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
    clasificacion_venta: Optional[str] = None  
    potencial_venta: Optional[str] = None  
    producto_tienda: Optional[str] = None  
    placa_vehiculo: Optional[str]
    modelo_vehiculo: Optional[str]
    marca: Optional[str]
    modelo_motor: Optional[str]
    anio: Optional[int]
    tipo_operacion_id: int
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
    precio: Optional[float] = None
    cantidad_reclamo: int
    und_reclamo: str

class QuejaRequest(BaseModel):
    tipo_queja: str
    motivos_producto_id: Optional[int] = None
    motivos_servicio_id: Optional[int] = None
    descripcion: str
    cliente_ruc_dni: str
    dni: str
    nombres: str
    apellidos: str
    email: str
    telefono: str
    clasificacion_venta: Optional[str] = None  
    potencial_venta: Optional[str] = None  
    producto_tienda: Optional[str] = None  
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

class ConsultarEstadoRequest(BaseModel):
    tipo_correlativos_id: Optional[int] = None
    cliente_ruc_dni: Optional[str] = None
    estado: Optional[str] = None


# Datos simulados predefinidos en una estructura de diccionario
simulated_docs = {
    "BOLETA": {
        "B001-12345678": {
            "documento": "B001-12345678",
            "tipo_documento": "BOLETA",
            "fechaventa": "2025-01-01",
            "nrointerno": "B1234",
            "guiaremision": "G001-12345678",
            "condicionpago": "Contado",
            "vendedor": "Vendedor Boleta",
            "departamento": "Lima",
            "sucursal": "Sucursal Boleta",
            "almacen": "Almacén Boleta",
            "transportista": "Transportista Boleta"
        }
    },
    "FACTURA": {
        "F001-87654321": {
            "documento": "F001-87654321",
            "tipo_documento": "FACTURA",
            "fechaventa": "2025-01-02",
            "nrointerno": "F5678",
            "guiaremision": "G001-87654321",
            "condicionpago": "Crédito",
            "vendedor": "Vendedor Factura",
            "departamento": "Arequipa",
            "sucursal": "Sucursal Factura",
            "almacen": "Almacén Factura",
            "transportista": "Transportista Factura"
        }
    },
    "NOTA DE VENTA": {
        "1234567": {
            "documento": "1234567",
            "tipo_documento": "NOTA DE VENTA",
            "fechaventa": "2025-01-03",
            "nrointerno": "NV9012",
            "guiaremision": "G001-1234567",
            "condicionpago": "Efectivo",
            "vendedor": "Vendedor NV",
            "departamento": "Cusco",
            "sucursal": "Sucursal NV",
            "almacen": "Almacén NV",
            "transportista": "Transportista NV"
        }
    }
}