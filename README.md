1-LEVANTAR PROYECTO EN PYTHON:
Primero en la terminal en Vscode ejecutar:
py -m venv venv
2-Ingresar a la carpeta 
cd app
3-Ejecutar el script de las depencias 
pip install -r ".\requirements.txt"
4- luego ejecutar comando 
si esta  en la carpeta app
python -m uvicorn main:app --port 8001 --reload
si no esta  en la carpeta mym_plataforma
python -m uvicorn app.main:app --port 8001 --reload

5- luego ejecutar comando para simular el api de mym debe ser en otro puerto y terminal
python -m uvicorn app.main_simulacion:app --port 8002 --reload


PLATAFORMA_POST_VENTA_BACKEND/
├── app/
│   ├── main.py # Archivo principal para inicializar la aplicación y agregar middlewares
│   ├── config.py # Configuración global y carga de variables de entorno
│   ├── db/
│   │   ├── init.py
│   │   └── connection.py # Lógica para establecer la conexión a la base de datos (como tu archivo db_connection.py)
│   ├── models/
│   │   ├── init.py
│   │   └── usuario.py # Modelos Pydantic y, si usas SQLAlchemy, tus modelos ORM
│   ├── routers/
│   │   ├── init.py
│   │   └── auth.py # Endpoints de autenticación, registro, recuperación de contraseña, etc.
│   ├── services/
│   │   ├── init.py
│   │   ├── auth_service.py # Lógica de negocio: validación de credenciales, generación de tokens, etc.
│   │   └── email_service.py # Funciones para el envío de correos
│   └── utils/
│   ├── init.py
│   ├── security.py # Funciones para generación/verificación de JWT y encriptación de contraseñas
│   └── logger.py # Configuración centralizada del logging
├── .env
└── requirements.txt

pip install python-jose>=3.0.0
pip install python-multipart