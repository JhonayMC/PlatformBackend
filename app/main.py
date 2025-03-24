from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, formularios, front, postventa
from app.config import CORS_ORIGINS
from fastapi.exceptions import RequestValidationError
from app.exception_handlers import validation_exception_handler
import logging  
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

app.add_exception_handler(RequestValidationError, validation_exception_handler)

logging.basicConfig(level=logging.DEBUG)  # Habilita logs detallados


# Rutas de almacenamiento de archivos
UPLOADS_IMAGENES = "uploads/imagenes"
UPLOADS_VIDEOS = "uploads/videos"
UPLOADS_DOCUMENTOS = "uploads/documentos"
UPLOADS_PDFS = "uploads/pdfs"
UPLOADS_GUIA = "uploads/guia"

app.mount("/uploads/imagenes", StaticFiles(directory=UPLOADS_IMAGENES), name="imagenes")
app.mount("/uploads/videos", StaticFiles(directory=UPLOADS_VIDEOS), name="videos")
app.mount("/uploads/documentos", StaticFiles(directory=UPLOADS_DOCUMENTOS), name="documentos")
app.mount("/uploads/pdfs", StaticFiles(directory=UPLOADS_PDFS), name="pdfs")
app.mount("/uploads/guia", StaticFiles(directory=UPLOADS_GUIA), name="guia")


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Ruta para servir el favicon y evitar el error 404
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("uploads/favicon.ico")


app.include_router(auth.router)
app.include_router(formularios.router)
app.include_router(front.router)
app.include_router(postventa.router)