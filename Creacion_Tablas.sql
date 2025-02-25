CREATE SCHEMA IF NOT EXISTS POSTVENTA;

SET search_path TO POSTVENTA;

CREATE TABLE TIPO_USUARIOS (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    aplicaciones VARCHAR(5000) NULL,
    accesos VARCHAR(5000) NULL,
    subaccesos VARCHAR(5000) NULL,
    permisos VARCHAR(5000) NULL,
    creado_el TIMESTAMP NULL,
    creado_por VARCHAR(50) NULL,
    modificado_el TIMESTAMP NULL,
    modificado_por VARCHAR(50) NULL
);

CREATE TABLE USUARIOS (
    id BIGSERIAL PRIMARY KEY,
    tipo_usuarios_id BIGINT NOT NULL,
    tipo_documentos_id BIGINT NOT NULL,
    nombre_completo VARCHAR(100) NOT NULL,
    documento VARCHAR(15) NOT NULL,
    correo VARCHAR(50) NOT NULL UNIQUE,
    contrasena VARCHAR(250) NOT NULL,
    accesos VARCHAR(5000) NULL,
    permisos VARCHAR(5000) NULL,
    estado CHAR(1) NOT NULL,
    creado_el TIMESTAMP NULL,
    creado_por VARCHAR(50) NULL,
    modificado_el TIMESTAMP NULL,
    modificado_por VARCHAR(50) NULL,
    codigo_recuperacion VARCHAR(255),
    codigo_expiracion TIMESTAMP,
    CONSTRAINT fk_tipo_usuario 
        FOREIGN KEY (tipo_usuarios_id) 
        REFERENCES TIPO_USUARIOS(id)
);

CREATE TABLE TIPO_DOCUMENTOS (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    creado_el TIMESTAMP NOT NULL,
    creado_por VARCHAR(50) NOT NULL,
    modificado_el TIMESTAMP NULL,
    modificado_por VARCHAR(50) NULL
);

CREATE TABLE USUARIOS_TOKENS (
    id BIGSERIAL PRIMARY KEY,
    usuarios_id BIGINT NOT NULL,
    token VARCHAR(250) NOT NULL,
    creado_el TIMESTAMP NOT NULL,
    expira_el TIMESTAMP NOT NULL,
    FOREIGN KEY (usuarios_id) REFERENCES USUARIOS(id)
);

CREATE TABLE PERMISOS (
    id BIGSERIAL PRIMARY KEY,
    aplicaciones_id BIGINT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    componente VARCHAR(50) NOT NULL,
    estado CHAR(1) NOT NULL,
    creado_el TIMESTAMP NOT NULL,
    creado_por VARCHAR(50) NOT NULL,
    modificado_el TIMESTAMP NULL,
    modificado_por VARCHAR(50) NULL
);

CREATE TABLE APLICACIONES (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    componente VARCHAR(50) NOT NULL,
    estado CHAR(1) NOT NULL,
    creado_el TIMESTAMP NOT NULL,
    creado_por VARCHAR(50) NOT NULL,
    modificado_el TIMESTAMP NULL,
    modificado_por VARCHAR(50) NULL
);

CREATE TABLE MENU_ADM_1NV (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    icono VARCHAR(50) NOT NULL,
    componente VARCHAR(50) NOT NULL,
    orden INT NOT NULL,
    estado CHAR(1) NOT NULL,
    creado_el TIMESTAMP NOT NULL,
    creado_por VARCHAR(50) NOT NULL,
    modificado_el TIMESTAMP NULL,
    modificado_por VARCHAR(50) NULL
);

CREATE TABLE MENU_ADM_2NV (
    id BIGSERIAL PRIMARY KEY,
    aplicaciones_id BIGINT NOT NULL,
    menu_adm_1nv_id BIGINT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    icono VARCHAR(50) NOT NULL,
    componente VARCHAR(50) NOT NULL,
    orden INT NOT NULL,
    estado CHAR(1) NOT NULL,
    creado_el TIMESTAMP NOT NULL,
    creado_por VARCHAR(50) NOT NULL,
    modificado_el TIMESTAMP NULL,
    modificado_por VARCHAR(50) NULL,
    FOREIGN KEY (menu_adm_1nv_id) REFERENCES MENU_ADM_1NV(id),
    FOREIGN KEY (aplicaciones_id) REFERENCES APLICACIONES(id)
);

CREATE TABLE MENU_ADM_3NV (
    id BIGSERIAL PRIMARY KEY,
    menu_adm_2nv_id BIGINT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    icono VARCHAR(50) NOT NULL,
    componente VARCHAR(50) NOT NULL,
    orden INT NOT NULL,
    estado CHAR(1) NOT NULL,
    creado_el TIMESTAMP NOT NULL,
    creado_por VARCHAR(50) NOT NULL,
    modificado_el TIMESTAMP NULL,
    modificado_por VARCHAR(50) NULL,
    FOREIGN KEY (menu_adm_2nv_id) REFERENCES MENU_ADM_2NV(id)
);

ALTER TABLE POSTVENTA.USUARIOS ADD COLUMN usuario VARCHAR;
ALTER TABLE POSTVENTA.USUARIOS ADD COLUMN empresa_id int;


--TABLAS PARA LOS FORMULARIOS
-- Tabla: DOCUMENTOS
CREATE TABLE postventa.documentos (
    id_documento BIGSERIAL PRIMARY KEY,
    tipo_correlativos_id BIGINT NOT NULL,
    serie VARCHAR(4),
    correlativo VARCHAR(8) NOT NULL,
    fecha_venta DATE NOT NULL,
    provincia VARCHAR(100) NOT NULL,
    n_interno VARCHAR(20) NOT NULL,
    guia_remision VARCHAR(20),
    sucursal VARCHAR(100) NOT NULL,
    almacen VARCHAR(100) NOT NULL,
    condicion_pago VARCHAR(10) CHECK (condicion_pago IN ('Crédito', 'Contado')),
    vendedor VARCHAR(100) NOT NULL,
    transportista VARCHAR(100),
    usuarios_id BIGINT NOT NULL,
    cliente_ruc_dni VARCHAR(11) NOT NULL,
    CONSTRAINT fk_documentos_usuarios FOREIGN KEY (usuarios_id) REFERENCES postventa.usuarios(id),
    CONSTRAINT fk_documentos_tipo_correlativos FOREIGN KEY (tipo_correlativos_id) REFERENCES postventa.tipo_correlativos(id)
);

-- Tabla: RECLAMOS
CREATE TABLE postventa.reclamos (
    id_reclamo BIGSERIAL PRIMARY KEY,
    documento_id BIGINT NOT NULL,
    usuarios_id BIGINT NOT NULL,
    tipo_usuarios_id BIGINT NOT NULL,
    dni VARCHAR(15) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    telefono VARCHAR(15) NOT NULL,
    detalle_reclamo TEXT NOT NULL,
    estado VARCHAR(20) CHECK (estado IN ('Evaluc. Tec.', 'Solucionado', 'Procede', 'No procede', 'Generado')),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    placa_vehiculo VARCHAR(8),
    modelo_vehiculo VARCHAR(50),
    marca VARCHAR(50),
    modelo_motor VARCHAR(50),
    anio INT,
    tipo_operacion VARCHAR(50) CHECK (tipo_operacion IN ('Transporte de carga', 'Transporte de pasajeros', 'Construcción', 'Minería', 'Agrícola')),
    clasificacion_venta VARCHAR(100),
    potencial_venta VARCHAR(100),
    producto_tienda CHAR(1) CHECK (producto_tienda IN ('S', 'N')),
    precio DECIMAL(10,2),
    fecha_instalacion DATE,
    horas_uso_reclamo INT,
    km_instalacion INT,
    km_actual INT,
    km_recorridos INT,
    CONSTRAINT fk_reclamos_documentos FOREIGN KEY (documento_id) REFERENCES postventa.documentos(id_documento),
    CONSTRAINT fk_reclamos_usuarios FOREIGN KEY (usuarios_id) REFERENCES postventa.usuarios(id),
    CONSTRAINT fk_reclamos_tipo_usuarios FOREIGN KEY (tipo_usuarios_id) REFERENCES postventa.tipo_usuarios(id)
);

-- Tabla: QUEJAS
CREATE TABLE postventa.quejas (
    id_queja BIGSERIAL PRIMARY KEY,
    documento_id BIGINT NULL,
    usuarios_id BIGINT NOT NULL,
    tipo_usuarios_id BIGINT NOT NULL,
    tipo_queja VARCHAR(20) CHECK (tipo_queja IN ('Producto', 'Servicio')),
    tipog VARCHAR(2) CHECK (tipog IN ('G1', 'G2')),
    motivo_queja VARCHAR(100) CHECK (
        (tipo_queja = 'Producto' AND motivo_queja IN (
            'Datos mal consignados (razón social, RUC, destino)',
            'Doble facturación',
            'Precio',
            'Cantidad',
            'Producto no solicitado',
            'Marca errada',
            'Código errado',
            'Empaque / repuesto en mal estado',
            'Mercadería sin empaque de marca',
            'Repuesto incompleto',
            'Repuesto diferente a la muestra / original'
        )) OR
        (tipo_queja = 'Servicio' AND motivo_queja IN (
            'Mala atención',
            'Personal de M&M',
            'Demora en la atención',
            'Ambiente',
            'Demora en la entrega',
            'Desabasto',
            'Falta de información'
        ))
    ),
    fecha_queja DATE,
    descripcion TEXT NOT NULL,
    cliente_ruc_dni VARCHAR(11) NOT NULL,
    dni_solicitante VARCHAR(8) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    telefono VARCHAR(15) NOT NULL,
    estado VARCHAR(20) CHECK (estado IN ('Registrada','Evaluc. Tec.', 'Solucionado', 'Procede', 'No procede')),
    clasificacion_venta VARCHAR(100),
    potencial_venta VARCHAR(100),
    producto_tienda CHAR(1) CHECK (producto_tienda IN ('S', 'N')),
    precio DECIMAL(10,2),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_quejas_documentos FOREIGN KEY (documento_id) REFERENCES postventa.documentos(id_documento),
    CONSTRAINT fk_quejas_usuarios FOREIGN KEY (usuarios_id) REFERENCES postventa.usuarios(id),
    CONSTRAINT fk_quejas_tipo_usuarios FOREIGN KEY (tipo_usuarios_id) REFERENCES postventa.tipo_usuarios(id)
);

-- Tabla: PRODUCTOS_RECLAMOS
CREATE TABLE postventa.productos (
    id_producto BIGSERIAL PRIMARY KEY,
    reclamo_id BIGINT NULL UNIQUE, -- Solo un producto por reclamo
    queja_id BIGINT NULL,
    itm VARCHAR(50),
    lin VARCHAR(50),
    org VARCHAR(50),
    marc VARCHAR(50),
    descrp_marc VARCHAR(100),
    fabrica VARCHAR(50),
    articulo VARCHAR(50),
    descripcion TEXT,
    precio DECIMAL(10,2),
    cantidad_reclamo INT NOT NULL CHECK (cantidad_reclamo > 0),
    und_reclamo VARCHAR(50),
    CONSTRAINT fk_productos_reclamos FOREIGN KEY (reclamo_id) REFERENCES postventa.reclamos(id_reclamo),
    CONSTRAINT fk_productos_quejas FOREIGN KEY (queja_id) REFERENCES postventa.quejas(id_queja)
);

-- Tabla: ARCHIVOS
CREATE TABLE postventa.archivos (
    id_archivo BIGSERIAL PRIMARY KEY,
    tipo_formulario VARCHAR(20) CHECK (tipo_formulario IN ('Reclamo', 'Queja')),
    reclamo_id BIGINT,
    queja_id BIGINT,
    archivo_url VARCHAR(255) NOT NULL,
    tipo_archivo VARCHAR(10) CHECK (tipo_archivo IN ('JPG', 'PNG', 'MP4', 'PDF', 'DOC')),
    CONSTRAINT fk_archivos_reclamos FOREIGN KEY (reclamo_id) REFERENCES postventa.reclamos(id_reclamo),
    CONSTRAINT fk_archivos_quejas FOREIGN KEY (queja_id) REFERENCES postventa.quejas(id_queja)
);

CREATE TABLE postventa.tipo_correlativos (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL,
    estado CHAR(1) NOT NULL
);

-- Insertar tipos de documentos
INSERT INTO postventa.tipo_correlativos (id, nombre, estado) VALUES (1, 'Boleta', 'A');
INSERT INTO postventa.tipo_correlativos (id, nombre, estado) VALUES (2, 'Factura', 'A');
INSERT INTO postventa.tipo_correlativos (id, nombre, estado) VALUES (3, 'Nota de Venta', 'A');




