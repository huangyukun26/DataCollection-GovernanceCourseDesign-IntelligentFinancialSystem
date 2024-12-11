from sqlalchemy import create_engine
from ..core.config import settings

def test_db_connection():
    """测试数据库连接"""
    try:
        # 构建数据库URL
        SQLALCHEMY_DATABASE_URL = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        
        # 创建引擎并尝试连接
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        with engine.connect() as conn:
            print("数据库连接成功！")
            
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")

if __name__ == "__main__":
    test_db_connection() 