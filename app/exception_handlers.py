from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errores = {}
    traducciones = {
        "Field required": "Campo requerido",
        "String should have at least 4 characters": "El numero de serie debe ser de 4 caracteres",
        "String should match pattern '^(JPG|PNG|MP4|PDF|DOC)$'":"Campo requerido",
        "Input should be a valid integer, unable to parse string as an integer":"Campo Rquerido"
    }
    
    for err in exc.errors():
        campo = err.get("loc")[-1]
        mensaje = err.get("msg")
        mensaje_traducido = traducciones.get(mensaje, mensaje)
        errores.setdefault(campo, []).append(mensaje_traducido)
    
    return JSONResponse(
        status_code=422,
        content={
            "errores": errores,
            "estado": 422,
            "mensaje": "No es posible procesar los datos enviados."
        }
    )
