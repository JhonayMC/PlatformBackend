CREATE SCHEMA IF NOT EXISTS POSTVENTA;

SET search_path TO POSTVENTA;

CREATE TABLE TIPO_USUARIOS (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
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


CREATE TABLE postventa.formularios (
    id SERIAL PRIMARY KEY,
    usuarios_id BIGINT NOT NULL,
    tipo_usuarios_id BIGINT NOT NULL,
    tipo_correlativos_id INT,
    reclamo INT,
    queja_servicio INT,
    queja_producto INT,
    motivos_servicio_id INT,
    motivos_producto_id INT,
    tipo_queja VARCHAR(2) NULL,
    serie VARCHAR(4) NULL,
    correlativo VARCHAR(8) NULL,
    cliente VARCHAR(25) NOT NULL,
    dni VARCHAR(8) NOT NULL, 
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    telefono VARCHAR(15) NOT NULL,
    producto_id INT,
    productO_cantidad INT,
    estado_id INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detalle_queja TEXT NULL,
    placa_vehiculo VARCHAR(8),
    modelo_vehiculo VARCHAR(50),
    marca VARCHAR(50),
    modelo_motor VARCHAR(50),
    anio INT,
    tipo_operacion_id INT,
    en_tienda BOOLEAN DEFAULT FALSE,
    fecha_instalacion DATE,
    horas_uso_reclamo INT,
    km_instalacion INT,
    km_actual INT,
    km_recorridos INT,
    detalle_reclamo TEXT,
    CONSTRAINT fk_formularios_tipo_correlativos FOREIGN KEY (tipo_correlativos_id) REFERENCES postventa.tipo_correlativos(id),
    CONSTRAINT fk_formularios_motivos_servicio FOREIGN KEY (motivos_servicio_id) REFERENCES postventa.motivos_servicio(id),
    CONSTRAINT fk_formularios_motivos_producto FOREIGN KEY (motivos_producto_id) REFERENCES postventa.motivos_producto(id),
    CONSTRAINT fk_formularios_usuarios FOREIGN KEY (usuarios_id) REFERENCES postventa.usuarios(id),
    CONSTRAINT fk_formularios_tipo_usuarios FOREIGN KEY (tipo_usuarios_id) REFERENCES postventa.tipo_usuarios(id),
    CONSTRAINT fk_formularios_tipo_operacion FOREIGN KEY (tipo_operacion_id) REFERENCES postventa.tipo_operaciones(id),
    CONSTRAINT fk_formularios_estado FOREIGN KEY (estado_id) REFERENCES postventa.estados(id_estado)
);
-- Tabla: ARCHIVOS
CREATE TABLE postventa.archivos (
    id_archivo BIGSERIAL PRIMARY KEY,
    archivo_url VARCHAR(255) NOT NULL,
    tipo_archivo VARCHAR(10) CHECK (tipo_archivo IN ('JPG', 'PNG', 'MP4', 'PDF', 'DOC')),
    formulario_id INT,
    CONSTRAINT fk_archivos_formularios FOREIGN KEY (formulario_id) REFERENCES postventa.formularios(id)
);

ALTER TABLE postventa.archivos 
ADD CONSTRAINT archivos_tipo_archivo_check 
CHECK (tipo_archivo IN ('JPG', 'PNG', 'PDF', 'DOCX', 'MP4', 'PPTX'));  -- Agregar los tipos permitidos

CREATE TABLE postventa.trazabilidad (
    id_trazabilidad SERIAL PRIMARY KEY,
    formulario_id INT NOT NULL,
    estado_id INT NOT NULL,
    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_trazabilidad_formulario FOREIGN KEY (formulario_id) REFERENCES postventa.formularios(id) ON DELETE CASCADE,
    CONSTRAINT fk_trazabilidad_estado FOREIGN KEY (estado_id) REFERENCES postventa.estados(id_estado) ON DELETE CASCADE
);

CREATE TABLE postventa.notificaciones (
    id SERIAL PRIMARY KEY,
    usuarios_id BIGINT NOT NULL,
    formulario_id BIGINT NOT NULL,
    tipo VARCHAR(50) NOT NULL,  -- Tipo de notificación (Ej: "Notificación por sistema")
    icono VARCHAR(50) NOT NULL, -- Ícono de la notificación
    mensaje TEXT NOT NULL,      -- Mensaje de la notificación
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Fecha de creación
    leido_en TIMESTAMP NULL,    -- Fecha en que el usuario leyó la notificación (NULL si no se ha leído)
    
    -- Relación con la tabla de usuarios y formularios
    CONSTRAINT fk_notificaciones_usuarios FOREIGN KEY (usuarios_id) REFERENCES postventa.usuarios(id),
    CONSTRAINT fk_notificaciones_formularios FOREIGN KEY (formulario_id) REFERENCES postventa.formularios(id)
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


CREATE TABLE postventa.tipo_correlativos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL
);

CREATE TABLE postventa.tipo_operaciones (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);

CREATE TABLE postventa.motivos_producto (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL
);

CREATE TABLE postventa.motivos_servicio (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL
);

-- Insertar en tipo_correlativos
INSERT INTO postventa.tipo_correlativos (nombre) VALUES
('Boleta'),
('Factura'),
('Nota de Venta');

-- Insertar en tipo_operaciones
INSERT INTO postventa.tipo_operaciones (nombre) VALUES
('Transporte de Carga'),
('Transporte de Pasajeros'),
('Construcción'),
('Minería'),
('Agrícola');

-- Insertar en motivos_producto
INSERT INTO postventa.motivos_producto (nombre) VALUES
('Datos mal consignados (razón social, RUC, destino)'),
('Doble Facturación'),
('Precio'),
('Cantidad'),
('Producto no solicitado'),
('Marca errada'),
('Código errado'),
('Empaque/repuesto en mal estado'),
('Mercadería sin empaque de marca'),
('Repuesto incompleto'),
('Repuesto diferente a la muestra/original');

--Insertar en motivos_servicio
INSERT INTO postventa.motivos_servicio (nombre) VALUES
('Mala atención del Cliente'),
('Personal de M&M'),
('Demora en la atención'),
('Ambiente'),
('Demora en la entrega de productos'),
('Desabasto'),
('Falta de información');

CREATE TABLE postventa.estados (
    id_estado SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

-- Insertar los estados únicos
INSERT INTO postventa.estados (nombre) VALUES
('Registrada'),
('Generado'),
('Cerrado'),
('Anulado'),
('Evaluac. Téc.'),
('Report. Fábric.'),
('Evaluac. Com'),
('No procede'),
('Procede'),
('Solucionado');


