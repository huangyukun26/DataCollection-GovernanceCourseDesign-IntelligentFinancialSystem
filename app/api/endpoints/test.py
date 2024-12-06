from fastapi import APIRouter, HTTPException
from app.db.database import engine, mongodb, minio_client
import cv2
import numpy as np
from PIL import Image
import io

router = APIRouter()

@router.get("/test-environment")
async def test_environment():
    results = {
        "database": False,
        "mongodb": False,
        "minio": False,
        "opencv": False,
        "tesseract": False
    }
    
    try:
        # 测试PostgreSQL连接
        with engine.connect() as connection:
            results["database"] = True
    except Exception as e:
        results["database_error"] = str(e)
    
    try:
        # 测试MongoDB连接
        mongodb.list_collection_names()
        results["mongodb"] = True
    except Exception as e:
        results["mongodb_error"] = str(e)
    
    try:
        # 测试MinIO连接
        buckets = minio_client.list_buckets()
        results["minio"] = True
    except Exception as e:
        results["minio_error"] = str(e)
    
    try:
        # 测试OpenCV
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.rectangle(img, (10, 10), (90, 90), (255, 255, 255), 2)
        results["opencv"] = True
    except Exception as e:
        results["opencv_error"] = str(e)
        
    try:
        # 测试Tesseract
        import pytesseract
        pytesseract.get_tesseract_version()
        results["tesseract"] = True
    except Exception as e:
        results["tesseract_error"] = str(e)
    
    return results 