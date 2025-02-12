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