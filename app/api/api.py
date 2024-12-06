from fastapi import APIRouter
from app.api.endpoints import documents, test

api_router = APIRouter()
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(test.router, prefix="/test", tags=["test"]) 