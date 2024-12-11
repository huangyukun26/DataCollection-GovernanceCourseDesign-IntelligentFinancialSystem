from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

app = FastAPI(title="智慧金融数据采集系统")

# 挂载静态文件
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# 设置模板
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# 页面路由
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/invoices")
async def invoice_list(request: Request):
    return templates.TemplateResponse("invoices/list.html", {"request": request})

@app.get("/invoices/upload")
async def invoice_upload(request: Request):
    return templates.TemplateResponse("invoices/upload.html", {"request": request})

# 导入API路由
from app.api.endpoints import invoice
app.include_router(invoice.router, prefix="/api/invoices", tags=["invoices"])