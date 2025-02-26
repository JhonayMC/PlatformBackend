from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, formularios, front
from app.config import CORS_ORIGINS
from fastapi.exceptions import RequestValidationError
from app.exception_handlers import validation_exception_handler
import logging

app = FastAPI()

app.add_exception_handler(RequestValidationError, validation_exception_handler)

logging.basicConfig(level=logging.DEBUG)  # Habilita logs detallados


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(formularios.router)
app.include_router(front.router)
