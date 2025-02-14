INSERT INTO POSTVENTA.TIPO_USUARIOS (
    nombre, 
    aplicaciones, 
    accesos, 
    subaccesos, 
    permisos, 
    creado_el, 
    creado_por
) VALUES (
    'Administrador',  -- nombre
    '{}',  -- aplicaciones (puede ser un JSON vacío o con datos)
    '{}',  -- accesos (puede ser un JSON vacío o con datos)
    '{}',  -- subaccesos (puede ser un JSON vacío o con datos)
    '{}',  -- permisos (puede ser un JSON vacío o con datos)
    CURRENT_TIMESTAMP,  -- creado_el (fecha y hora actual)
    'admin'  -- creado_por (usuario que crea el registro)
);
INSERT INTO POSTVENTA.TIPO_DOCUMENTOS (
    nombre, 
    creado_el, 
    creado_por
) VALUES (
    'Cédula de Ciudadanía',  -- nombre
    CURRENT_TIMESTAMP,  -- creado_el (fecha y hora actual)
    'admin'  -- creado_por (usuario que crea el registro)
);