from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
from minio import Minio
from app.core.config import settings

# PostgreSQL
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB
mongo_client = MongoClient(settings.MONGODB_URL)
mongodb = mongo_client.financial_data

# MinIO
minio_client = Minio(
    settings.MINIO_URL,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False
)

# 确保MinIO bucket存在
def init_minio():
    bucket_name = "financial-data"
    found = minio_client.bucket_exists(bucket_name)
    if not found:
        minio_client.make_bucket(bucket_name)

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 