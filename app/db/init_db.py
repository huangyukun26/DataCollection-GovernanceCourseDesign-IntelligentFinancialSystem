from sqlalchemy.orm import Session
from app.db.database import engine, Base
from alembic.config import Config
from alembic import command
import os

def init_db() -> None:
    # 删除所有表
    Base.metadata.drop_all(bind=engine)
    
    # 删除 alembic_version 表
    with engine.connect() as conn:
        conn.execute("DROP TABLE IF EXISTS alembic_version")
        conn.commit()
    
    # 运行迁移
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

def init_test_data(db: Session) -> None:
    # TODO: 添加测试数据
    pass 