from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errores = {}
    for err in exc.errors():
        campo = err.get("loc")[-1]
        errores.setdefault(campo, []).append(err.get("msg"))
    return JSONResponse(
        status_code=422,
        content={
            "errores": errores,
            "estado": 422,
            "mensaje": "No es posible procesar los datos enviados."
        }
    )
