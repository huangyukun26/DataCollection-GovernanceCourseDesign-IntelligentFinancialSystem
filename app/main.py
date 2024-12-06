from fastapi import FastAPI
from app.core.config import settings
from app.db.database import init_minio
from app.api.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    init_minio()

@app.get("/")
def read_root():
    return {"message": "Financial Data System API"} 