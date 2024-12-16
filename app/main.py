from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import invoice, bank_statement
from app.db.base_class import Base
from app.db.session import engine
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="智慧金融数据采集系统",
    description="发票识别与银行流水管理系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置文件上传大小限制为10MB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 注册路由
app.include_router(
    invoice.router,
    prefix="/api/invoices",
    tags=["发票管理"]
)

app.include_router(
    bank_statement.router,
    prefix="/api/bank-statements",
    tags=["银行流水管理"]
)

@app.get("/")
async def root():
    return {
        "message": "欢迎使用智慧金融数据采集系统",
        "version": "1.0.0"
    }