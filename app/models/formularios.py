from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from fastapi import Form, UploadFile, File

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

#probado la funcionalidad con el FormData
# Modelo para productos en FormData con ID
class ProductoReclamoForm:
    def __init__(
        self,
        #form_3_itm: str = Form(...),
        #form_3_lin: str = Form(...),
        #form_3_org: str = Form(...),
        #form_3_marc: str = Form(...),
        #form_3_descrp_marc: str = Form(...),
        #form_3_fabrica: str = Form(...),
        #form_3_articulo: str = Form(...),
        #form_3_descripcion: str = Form(...),
        form_3_precio: Optional[float] = Form(None),
        form_3_cantidad: int = Form(...),
        #form_3_und_reclamo: str = Form(...)
    ):
        #self.itm = form_3_itm
        #self.lin = form_3_lin
        #self.org = form_3_org
        #self.marc = form_3_marc
        #self.descrp_marc = form_3_descrp_marc
        #self.fabrica = form_3_fabrica
        #self.articulo = form_3_articulo
        #self.descripcion = form_3_descripcion
        self.precio = form_3_precio
        self.cantidad = form_3_cantidad
        #self.und_reclamo = form_3_und_reclamo

# Modelo para archivos en FormData
class ArchivoForm:
    def __init__(
        self,
        form_5_images: List[UploadFile] = File(None),
        form_5_videos: List[UploadFile] = File(None),
    ):
        self.images = form_5_images
        self.videos = form_5_videos

# Modelo principal del reclamo usando FormData
class ReclamoForm:
    def __init__(
        self,
        form_1_tipocorrelativo_id: int = Form(...),
        form_1_serie: Optional[str] = Form(None),
        form_1_correlativo: str = Form(...),
        form_1_fechaventa: str = Form(...),
        form_1_nrointerno: str = Form(...),
        form_1_guiaremision: Optional[str] = Form(None),
        form_1_condicionpago: str = Form(...),
        form_1_vendedor: str = Form(...),
        form_1_departamento: str = Form(...),
        form_1_sucursal: str = Form(...),
        form_1_almacen: str = Form(...),
        form_1_transportista: Optional[str] = Form(None),

        form_2_cliente: str = Form(...),
        form_2_dni: str = Form(...),
        form_2_nombres: str = Form(...),
        form_2_apellidos: str = Form(...),
        form_2_correo: str = Form(...),
        form_2_telefono: str = Form(...),

        form_4_nroplaca: Optional[str] = Form(None),
        form_4_marca: Optional[str] = Form(None),
        form_4_modelo: Optional[str] = Form(None),
        form_4_anio: Optional[int] = Form(None),
        form_4_motor: Optional[str] = Form(None),
        form_4_tipoOperacion: int = Form(...),
        form_4_fechaInstalacion: Optional[str] = Form(None),
        form_4_horaUso: Optional[int] = Form(None),
        form_4_kmInstalacion: Optional[int] = Form(None),
        form_4_kmActual: Optional[int] = Form(None),

        form_5_descripcion: str = Form(...),
    ):
        self.tipocorrelativo_id = form_1_tipocorrelativo_id
        self.serie = form_1_serie
        self.correlativo = form_1_correlativo
        self.fechaventa = form_1_fechaventa
        self.nrointerno = form_1_nrointerno
        self.guiaremision = form_1_guiaremision
        self.condicionpago = form_1_condicionpago
        self.vendedor = form_1_vendedor
        self.departamento = form_1_departamento
        self.sucursal = form_1_sucursal
        self.almacen = form_1_almacen
        self.transportista = form_1_transportista

        self.cliente = form_2_cliente
        self.dni = form_2_dni
        self.nombres = form_2_nombres
        self.apellidos = form_2_apellidos
        self.correo = form_2_correo
        self.telefono = form_2_telefono

        self.nroplaca = form_4_nroplaca
        self.marca = form_4_marca
        self.modelo = form_4_modelo
        self.anio = form_4_anio
        self.motor = form_4_motor
        self.tipoOperacion = form_4_tipoOperacion
        self.fechaInstalacion = form_4_fechaInstalacion
        self.horaUso = form_4_horaUso
        self.kmInstalacion = form_4_kmInstalacion
        self.kmActual = form_4_kmActual

        self.descripcion = form_5_descripcion

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

#Form Data Para Quejas Servicio
class ArchivoServicioForm:
    def __init__(
        self,
        form_2_images: List[UploadFile] = File(None),
        form_2_videos: List[UploadFile] = File(None),
    ):
        self.images = form_2_images
        self.videos = form_2_videos

class QuejaServicioForm:
    def __init__(
        self,
        tipo_queja: str = Form(...),
        form_1_motivo: int = Form(...),
        form_2_fecha: str = Form(...),
        form_2_descripcion: str = Form(...),
        form_3_cliente: str = Form(...),
        form_3_dni: str = Form(...),
        form_3_nombres: str = Form(...),
        form_3_apellidos: str = Form(...),
        form_3_correo: str = Form(...),
        form_3_telefono: str = Form(...),
    ):
        self.tipo_queja = tipo_queja
        self.motivo = form_1_motivo
        self.fecha_queja = form_2_fecha
        self.descripcion = form_2_descripcion
        self.cliente = form_3_cliente
        self.dni = form_3_dni
        self.nombres = form_3_nombres
        self.apellidos = form_3_apellidos
        self.correo = form_3_correo
        self.telefono = form_3_telefono



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