from fastapi import FastAPI, Depends, APIRouter, HTTPException, Header
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.security import JWT_SECRET_KEY, ALGORITHM
from sqlalchemy.orm import Session
from sqlalchemy import text
import jwt
from app.db.connection import SessionLocal


router = APIRouter(prefix="/api/v1")
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función personalizada para validar token a partir del encabezado Authorization
async def get_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"mensaje": "Token inválido", "estado": 401}
        )
    
    token = authorization.replace("Bearer ", "")
    try:
        # Utiliza tu función de validación existente pero sin pasar HTTPAuthorizationCredentials
        # Adaptamos para que trabaje directamente con el string del token
        payload = validar_token_directo(token)
        return payload
    except Exception:
        return JSONResponse(
            status_code=401,
            content={"mensaje": "Token inválido", "estado": 401}
        )

# Función auxiliar que adapta tu validar_token para trabajar con strings
def validar_token_directo(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expirado")
    except jwt.JWTError:
        raise Exception("Token inválido")

@router.get("/tipo-correlativos")
def obtener_tipo_correlativos(db: Session = Depends(get_db), token=Depends(get_token)):
    if isinstance(token, JSONResponse):
        return token

    query = text("SELECT id, nombre FROM postventa.tipo_correlativos")
    result = db.execute(query).fetchall()

    return [{"id": row[0], "nombre": row[1]} for row in result]

@router.get("/tipo-operaciones")
def obtener_tipo_operaciones(db: Session = Depends(get_db), token=Depends(get_token)):
    if isinstance(token, JSONResponse):
        return token

    query = text("SELECT id, nombre FROM postventa.tipo_operaciones")
    result = db.execute(query).fetchall()

    return [{"id": row[0], "nombre": row[1]} for row in result]

@router.get("/motivos")
def obtener_motivos(tipo: str, db: Session = Depends(get_db), token=Depends(get_token)):
    if isinstance(token, JSONResponse):
        return token

    if tipo == "producto":
        query = text("SELECT id, nombre FROM postventa.motivos_producto")
    elif tipo == "servicio":
        query = text("SELECT id, nombre FROM postventa.motivos_servicio")
    else:
        return JSONResponse(status_code=400, content={"estado": 400, "mensaje": "Tipo de motivo no válido"})

    result = db.execute(query).fetchall()
    return [{"id": row[0], "nombre": row[1]} for row in result]

@router.get("/estados")
def obtener_tipo_operaciones(db: Session = Depends(get_db), token=Depends(get_token)):
    if isinstance(token, JSONResponse):
        return token

    query = text("SELECT id_estado, nombre FROM postventa.estados")
    result = db.execute(query).fetchall()

    return [{"id": row[0], "nombre": row[1]} for row in result]   


@router.get("/buscar-dni/{dni}")
def buscar_dni(dni: str, token=Depends(get_token)):
    if isinstance(token, JSONResponse):
        return token  # Retorna error 401 si el token es inválido
    
    # Datos de vehículo por defecto
    cliente_default = {
        "nombres": "Samuel", 
        "apellidos": "Roman Tito"
    }
    
    # Usa los datos por defecto para cualquier placa ingresada
    return JSONResponse(
        status_code=200, 
        content={
            "estado": 200, 
            "mensaje": "Cliente encontrado", 
            "data": cliente_default,
            "DNI": dni.upper() 
        }
    )

    
@router.get("/buscar-placa/{placa}")
def buscar_placa(placa: str, token=Depends(get_token)):
    if isinstance(token, JSONResponse):
        return token  # Retorna error 401 si el token es inválido
    
    # Datos de vehículo por defecto
    vehiculo_default = {
        "marca": "Toyota", 
        "modelo": "Corolla", 
        "anio": 2022, 
        "motor": "1.8L VVT-i"
    }
    
    # Usa los datos por defecto para cualquier placa ingresada
    return JSONResponse(
        status_code=200, 
        content={
            "estado": 200, 
            "mensaje": "Vehículo encontrado", 
            "data": vehiculo_default,
            "placa": placa.upper() 
        }
    )
