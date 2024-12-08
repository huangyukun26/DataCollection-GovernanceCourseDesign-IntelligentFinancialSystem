from fastapi import FastAPI
from app.core.config import settings
from app.db.database import init_minio
from app.db.init_db import init_db
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
    # 不在这里初始化数据库，因为已经在 docker-compose 命令中处理了
    # init_db()

@app.get("/")
def read_root():
    return {"message": "Financial Data System API"} 