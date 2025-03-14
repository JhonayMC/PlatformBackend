from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from fastapi import Form, UploadFile, File


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
        tipo_queja: str = Form("G2"), 
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

class ReclamoProductoForm:
    def __init__(
        self,
        form_1_motivo: int = Form(...),  
        form_2_tipocorrelativo_id: int = Form(...),
        form_2_serie: str = Form(...),
        form_2_correlativo: str = Form(...),
        form_2_fechaventa: str = Form(...),
        form_2_nrointerno: str = Form(...),
        form_2_guiaremision: str = Form(...),
        form_2_condicionpago: str = Form(...),
        form_2_vendedor: str = Form(...),
        form_2_departamento: str = Form(...),
        form_2_sucursal: str = Form(...),
        form_2_almacen: str = Form(...),
        form_2_transportista: str = Form(...),
        form_3_cliente: str = Form(...),
        form_3_dni: str = Form(...),
        form_3_nombres: str = Form(...),
        form_3_apellidos: str = Form(...),
        form_3_correo: str = Form(...),
        form_3_telefono: str = Form(...),
        form_4_producto_id: str = Form(...),  
        form_4_cantidad: int = Form(...),  
        form_5_descripcion: str = Form(...)
    ):
        self.motivos_producto_id = form_1_motivo
        self.tipo_correlativos_id = form_2_tipocorrelativo_id
        self.serie = form_2_serie
        self.correlativo = form_2_correlativo
        self.fecha_venta = form_2_fechaventa
        self.nro_interno = form_2_nrointerno
        self.guia_remision = form_2_guiaremision
        self.condicion_pago = form_2_condicionpago
        self.vendedor = form_2_vendedor
        self.departamento = form_2_departamento
        self.sucursal = form_2_sucursal
        self.almacen = form_2_almacen
        self.transportista = form_2_transportista
        self.cliente = form_3_cliente
        self.dni = form_3_dni
        self.nombres = form_3_nombres
        self.apellidos = form_3_apellidos
        self.correo = form_3_correo
        self.telefono = form_3_telefono
        self.producto_id = form_4_producto_id
        self.producto_cantidad = form_4_cantidad
        self.detalle_reclamo = form_5_descripcion

class ArchivoReclamoForm:
    def __init__(
        self,
        form_5_images: List[UploadFile] = File(None),
        form_5_videos: List[UploadFile] = File(None),
    ):
        self.form_5_images = form_5_images
        self.form_5_videos = form_5_videos

class ReclamoForm:
    def __init__(
        self,
        form_1_tipocorrelativo_id: int = Form(...),
        form_1_serie: str = Form(...),
        form_1_correlativo: str = Form(...),
        form_1_fechaventa: str = Form(...),
        form_1_nrointerno: str = Form(...),
        form_1_guiaremision: str = Form(...),
        form_1_condicionpago: str = Form(...),
        form_1_vendedor: str = Form(...),
        form_1_departamento: str = Form(...),
        form_1_sucursal: str = Form(...),
        form_1_almacen: str = Form(...),
        form_1_transportista: str = Form(...),
        form_2_cliente: str = Form(...),
        form_2_dni: str = Form(...),
        form_2_nombres: str = Form(...),
        form_2_apellidos: str = Form(...),
        form_2_correo: str = Form(...),
        form_2_telefono: str = Form(...),
        form_3_producto_id: str = Form(...),
        form_3_cantidad: int = Form(...),
        form_4_nroplaca: str = Form(...),
        form_4_marca: str = Form(...),
        form_4_modelo: str = Form(...),
        form_4_anio: int = Form(...),
        form_4_motor: str = Form(...),
        form_4_tipoOperacion: int = Form(...),
        form_4_fechaInstalacion: str = Form(...),
        form_4_horaUso: int = Form(...),
        form_4_kmInstalacion: int = Form(...),
        form_4_kmActual: int = Form(...),
        form_4_kmRecorridos: Optional[int] = Form(None),
        form_5_descripcion: str = Form(...),
        # Campos adicionales para trabajadores (no requeridos por clientes)
        form_2_clasificacion_venta: Optional[str] = Form(None),
        form_2_potencial_venta: Optional[str] = Form(None),
        form_3_en_tienda: Optional[bool] = Form(None)
    ):
        self.tipo_correlativos_id = form_1_tipocorrelativo_id
        self.serie = form_1_serie
        self.correlativo = form_1_correlativo
        self.fecha_venta = form_1_fechaventa
        self.nro_interno = form_1_nrointerno
        self.guia_remision = form_1_guiaremision
        self.condicion_pago = form_1_condicionpago
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
        self.producto_id = form_3_producto_id
        self.producto_cantidad = form_3_cantidad
        self.placa_vehiculo = form_4_nroplaca
        self.marca = form_4_marca
        self.modelo_vehiculo = form_4_modelo
        self.anio = form_4_anio
        self.modelo_motor = form_4_motor
        self.tipo_operacion_id = form_4_tipoOperacion
        self.fecha_instalacion = form_4_fechaInstalacion
        self.horas_uso_reclamo = form_4_horaUso
        self.km_instalacion = form_4_kmInstalacion
        self.km_actual = form_4_kmActual
        self.km_recorridos = form_4_kmRecorridos
        self.detalle_reclamo = form_5_descripcion
         #Campos que solo se asignan si es trabajador
        self.clasificacion_venta = form_2_clasificacion_venta
        self.potencial_venta = form_2_potencial_venta
        self.en_tienda = form_3_en_tienda

class ArchivoReclamoForm:
    def __init__(
        self,
        form_5_images: List[UploadFile] = File(None),
        form_5_videos: List[UploadFile] = File(None),
    ):
        self.form_5_images = form_5_images
        self.form_5_videos = form_5_videos


class SeguimientoRequest(BaseModel):
    page: int = Field(ge=1)
    tipo_registro: Optional[str]  # "reclamos", "quejas" o vacío
    estado: Optional[int]  # ID del estado (entero)
    leyenda: Optional[str]  # "NNC" o "NNP" (Nota de crédito cliente/proveedor)
    cliente: Optional[str]  

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
        "clasificacion_venta" : "xxxxxxxx",
        "potencial_venta": "xxxxxxxxxx",
        "cliente": {
            "nombre_completo": "Samuel Roman Tito",
            "documento": "65465445"
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
                "precio_venta": 250,
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
                "precio_venta": 250,
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
                "precio_venta": 250,
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
                "precio_venta": 250,
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
                "precio_venta": 250,
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
        "clasificacion_venta" : "xxxxxxxx",
        "potencial_venta": "xxxxxxxxxx",
        "cliente": {
            "nombre_completo": "Samuel Roman Tito",
            "documento": "65465445"
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
                "precio_venta": 250,
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
                "precio_venta": 250,
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
                "precio_venta": 250,
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
                "precio_venta": 250,
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
                "precio_venta": 250,
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
        "clasificacion_venta" : "xxxxxxxx",
        "potencial_venta": "xxxxxxxxxx",
        "cliente": {
            "nombre_completo": "Samuel Roman Tito",
            "documento": "65465445" 
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
                "precio_venta": 250,
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
                "precio_venta": 250,
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
                "precio_venta": 250,
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
                "precio_venta": 250,
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
                "precio_venta": 250,
                "cantidad": 1
            }
        ]
    }
}

clientes = {
    "70981525": {
        "nombre_completo": "angel obregon",
        "documento": "4648846",
        "clasificación_venta": "venta normal",
        "potencial_venta": "potencial"
    }
}