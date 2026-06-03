from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import extract, formats, health

app = FastAPI(
    title="Hemia Extract API",
    description="Lightweight text extraction and OCR service.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(formats.router, prefix="/v1")
app.include_router(extract.router, prefix="/v1")
