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
        "transportista": "Transportista Boleta",
        "cliente": {
            "nombre_completo": "Samuel Roman Tito"  
        },
        "productos": [
            {
                "codigo": "P001",
                "nombre": "Producto 1",
                "linea": "Linea 1",
                "organizacion": "Organización 1",
                "marca": "Marca 1",
                "marca_desc": "Descripción Marca 1",
                "fabrica": "Fabrica 1",
                "articulo": "Articulo 1",
                "cantidad": 1
            },
            {
                "codigo": "P002",
                "nombre": "Smartphone Samsung Galaxy",
                "linea": "Electrónica",
                "organizacion": "Samsung Electronics",
                "marca": "Samsung",
                "marca_desc": "Tecnología de vanguardia",
                "fabrica": "Samsung Vietnam",
                "articulo": "SM-G110",
                "cantidad": 1
            },
            {
                "codigo": "P003",
                "nombre": "Zapatillas Deportivas Nike",
                "linea": "Calzado",
                "organizacion": "Nike Inc.",
                "marca": "Nike",
                "marca_desc": "Calidad deportiva premium",
                "fabrica": "Nike Indonesia",
                "articulo": "NK-ZD450",
                "cantidad": 1
            },
            {
                "codigo": "P004",
                "nombre": "Laptop HP Pavilion",
                "linea": "Computación",
                "organizacion": "HP Inc.",
                "marca": "HP",
                "marca_desc": "Tecnología confiable",
                "fabrica": "HP China",
                "articulo": "HP-LT220",
                "cantidad": 1
            },
            {
                "codigo": "P005",
                "nombre": "Refrigerador LG",
                "linea": "Electrodomésticos",
                "organizacion": "LG Electronics",
                "marca": "LG",
                "marca_desc": "Innovación para el hogar",
                "fabrica": "LG Corea",
                "articulo": "LG-RF345",
                "cantidad": 1
            }
        ]
    },
    "FACTURA": {
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
        "transportista": "Transportista Factura",
        "cliente": {
            "nombre_completo": "Samuel Roman Tito"  
        },
        "productos": [
            {
                "codigo": "P101",
                "nombre": "Impresora Multifuncional Canon",
                "linea": "Oficina",
                "organizacion": "Canon Inc.",
                "marca": "Canon",
                "marca_desc": "Tecnología japonesa de precisión",
                "fabrica": "Canon Tailandia",
                "articulo": "CN-MP450",
                "cantidad": 1
            },
            {
                "codigo": "P102",
                "nombre": "Escritorio Ejecutivo",
                "linea": "Mobiliario",
                "organizacion": "Muebles Modernos",
                "marca": "OfficePro",
                "marca_desc": "Mobiliario empresarial premium",
                "fabrica": "Maderas Finas Perú",
                "articulo": "ES-EJ320",
                "cantidad": 1
            },
            {
                "codigo": "P103",
                "nombre": "Monitor LG UltraWide",
                "linea": "Computación",
                "organizacion": "LG Electronics",
                "marca": "LG",
                "marca_desc": "Calidad de imagen superior",
                "fabrica": "LG México",
                "articulo": "LG-MU340",
                "cantidad": 1
            },
            {
                "codigo": "P104",
                "nombre": "Silla Ergonómica",
                "linea": "Mobiliario",
                "organizacion": "ErgoDesign",
                "marca": "ComfortPlus",
                "marca_desc": "Ergonomía avanzada",
                "fabrica": "ErgoDesign Brasil",
                "articulo": "CP-SE550",
                "cantidad": 1
            },
            {
                "codigo": "P105",
                "nombre": "Proyector Epson",
                "linea": "Audiovisuales",
                "organizacion": "Epson Corporation",
                "marca": "Epson",
                "marca_desc": "Proyección de alta definición",
                "fabrica": "Epson Indonesia",
                "articulo": "EP-PR750",
                "cantidad": 1
            }
        ]
    },
    "NOTA DE VENTA": {
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
        "transportista": "Transportista NV",
        "cliente": {
            "nombre_completo": "Samuel Roman Tito"  
        },
        "productos": [
            {
                "codigo": "P201",
                "nombre": "Mochila Escolar",
                "linea": "Escolar",
                "organizacion": "BackpackPro",
                "marca": "SchoolPlus",
                "marca_desc": "Materiales resistentes",
                "fabrica": "TextilPro Perú",
                "articulo": "ME-320",
                "cantidad": 1
            },
            {
                "codigo": "P202",
                "nombre": "Juego de Cuadernos",
                "linea": "Papelería",
                "organizacion": "PapelMax",
                "marca": "NotePro",
                "marca_desc": "Papel de alta calidad",
                "fabrica": "PapelMax Colombia",
                "articulo": "NP-JC100",
                "cantidad": 1
            },
            {
                "codigo": "P203",
                "nombre": "Bicicleta Montañera",
                "linea": "Deportes",
                "organizacion": "BikeMaster",
                "marca": "MountainPro",
                "marca_desc": "Alto rendimiento en terreno",
                "fabrica": "BikeMaster Taiwan",
                "articulo": "MP-B450",
                "cantidad": 1
            },
            {
                "codigo": "P204",
                "nombre": "Cafetera Eléctrica",
                "linea": "Electrodomésticos",
                "organizacion": "HomeAppliances",
                "marca": "CoffeeMaster",
                "marca_desc": "Preparación perfecta",
                "fabrica": "HomeApp China",
                "articulo": "CM-CE120",
                "cantidad": 1
            },
            {
                "codigo": "P205",
                "nombre": "Juego de Ollas",
                "linea": "Hogar",
                "organizacion": "KitchenPro",
                "marca": "CookMaster",
                "marca_desc": "Acero inoxidable premium",
                "fabrica": "KitchenPro Brasil",
                "articulo": "CM-JO500",
                "cantidad": 1
            }
        ]
    }
}