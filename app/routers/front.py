from fastapi import FastAPI, Depends, APIRouter, HTTPException, Header
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.security import JWT_SECRET_KEY, ALGORITHM
import jwt

router = APIRouter(prefix="/api/v1")
app = FastAPI()

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
def obtener_tipo_correlativos(token = Depends(get_token)):
    # Si token es un JSONResponse, lo retornamos (error 401)
    if isinstance(token, JSONResponse):
        return token
        
    return [
        {"id": 1, "nombre": "Boleta"},
        {"id": 2, "nombre": "Factura"},
        {"id": 3, "nombre": "Nota de Venta"},
    ]

@router.get("/tipo-operaciones")
def obtener_tipo_operaciones(token = Depends(get_token)):
    if isinstance(token, JSONResponse):
        return token
        
    return [
        {"id": 1, "nombre": "Transporte de Carga"},
        {"id": 2, "nombre": "Transporte de Pasajeros"},
        {"id": 3, "nombre": "Construcción"},
        {"id": 4, "nombre": "Minería"},
        {"id": 5, "nombre": "Agrícola"},
    ]

@router.get("/motivos")
def obtener_motivos(tipo: str, token = Depends(get_token)):
    if isinstance(token, JSONResponse):
        return token
        
    if tipo == "producto":
        return [
            {"id": 1, "nombre": "Datos mal consignados (razón social, RUC, destino)"},
            {"id": 2, "nombre": "Doble Facturación"},
            {"id": 3, "nombre": "Precio"},
            {"id": 4, "nombre": "Cantidad"},
            {"id": 5, "nombre": "Producto no solicitado"},
            {"id": 6, "nombre": "Marca errada"},
            {"id": 7, "nombre": "Código errado"},
            {"id": 8, "nombre": "Empaque/repuesto en mal estado"},
            {"id": 9, "nombre": "Mercadería sin empaque de marca"},
            {"id": 10, "nombre": "Repuesto incompleto"},
            {"id": 11, "nombre": "Repuesto diferente a la muestra/original"},
        ]
    elif tipo == "servicio":
        return [
            {"id": 1, "nombre": "Mala atención del Cliente"},
            {"id": 2, "nombre": "Personal de M&M"},
            {"id": 3, "nombre": "Demora en la atención"},
            {"id": 4, "nombre": "Ambiente"},
            {"id": 5, "nombre": "Demora en la entrega de productos"},
            {"id": 6, "nombre": "Desabasto"},
            {"id": 7, "nombre": "Falta de información"},
        ]
    else:
        return JSONResponse(status_code=400, content={"estado": 400, "mensaje": "Tipo de motivo no válido"})