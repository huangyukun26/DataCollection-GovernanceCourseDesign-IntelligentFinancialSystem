from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
import os
from minio import Minio
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

from app.models.bank_statement import BankStatement
from app.schemas.bank_statement import BankStatementCreate, BankStatementUpdate
from .parsers import BankParserFactory
from .parsers.base import BankStatementParser

load_dotenv()

# 配置日志
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logger = logging.getLogger("bank_statement_service")
logger.setLevel(logging.DEBUG)

# 文件处理器 - 按日期滚动
file_handler = RotatingFileHandler(
    os.path.join(log_dir, "bank_statement_service.log"),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)

# 格式化器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 添加处理器
logger.addHandler(file_handler)

class MinioStorage:
    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_URL"),
            access_key=os.getenv("MINIO_ROOT_USER"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
            secure=False
        )
        self.bucket = os.getenv("MINIO_BUCKET")
        
        # 确保bucket存在
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            
    def upload_file(self, file_data: bytes, file_name: str, content_type: str) -> str:
        """上传文件到MinIO"""
        try:
            from io import BytesIO
            file_obj = BytesIO(file_data)
            self.client.put_object(
                self.bucket,
                file_name,
                file_obj,
                len(file_data),
                content_type=content_type
            )
            return f"{self.bucket}/{file_name}"
        except Exception as e:
            raise Exception(f"上传文件失败: {str(e)}")
            
    def delete_file(self, file_path: str) -> bool:
        """从MinIO删除文件"""
        try:
            bucket, file_name = file_path.split("/", 1)
            self.client.remove_object(bucket, file_name)
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            return False

class BankStatementService:
    def __init__(self):
        self.storage = MinioStorage()
    
    def process_bank_statement(self, image_data: bytes, bank_type: str = "beijing_bank") -> List[dict]:
        """处理银行流水图片"""
        try:
            logger.info("\n" + "="*50)
            logger.info(f"[处理银行流水] 开始处理，bank_type: {bank_type}")
            logger.info("="*50)
            
            # 获取对应的解析器
            parser = BankParserFactory.get_parser(bank_type)
            logger.info(f"[处理银行流水] 使用解析器: {parser.__class__.__name__}")
            
            # 1. OCR识别和初步解析
            logger.info("\n" + "-"*30 + " OCR识别开始 " + "-"*30)
            raw_data = parser.parse(image_data)
            logger.info("-"*30 + " OCR识别完成 " + "-"*30 + "\n")
            
            # 2. 数据清洗
            logger.info("\n" + "-"*30 + " 数据清洗开始 " + "-"*30)
            transactions = parser.clean_data(raw_data)
            logger.info(f"[数据清洗] 清洗结果示例（第一条记录）:")
            if transactions:
                logger.info(f"账号: {transactions[0].get('account_number')}")
                logger.info(f"日期: {transactions[0].get('transaction_date')}")
                logger.info(f"类型: {transactions[0].get('transaction_type')}")
                logger.info(f"金额: {transactions[0].get('amount')}")
                logger.info(f"余额: {transactions[0].get('balance')}")
                logger.info(f"对手方: {transactions[0].get('counterparty')}")
                logger.info(f"描述: {transactions[0].get('description')}")
            logger.info("-"*30 + " 数据清洗完成 " + "-"*30 + "\n")
            
            # 3. 数据验证
            logger.info("\n" + "-"*30 + " 数据验证开始 " + "-"*30)
            if not parser.validate_data(transactions):
                raise Exception("数据验证失败")
            logger.info("-"*30 + " 数据验证完成 " + "-"*30 + "\n")
            
            logger.info(f"[处理银行流水] 成功处理，解析到{len(transactions)}条记录")
            logger.info("="*50 + "\n")
            return transactions
            
        except Exception as e:
            logger.error(f"\n[错误] 处理银行流水图片失败: {str(e)}")
            logger.error("="*50 + "\n")
            raise Exception(f"处理银行流水图片失败: {str(e)}")
    
    def create_bank_statement(
        self,
        db: Session,
        file_data: bytes,
        file_name: str,
        bank_type: str = "beijing_bank"
    ) -> List[BankStatement]:
        """创建银行流水记录"""
        try:
            logger.info("\n" + "="*50)
            logger.info(f"[创建银行流水记录] 开始创建，bank_type: {bank_type}")
            logger.info("="*50)
            
            # 1. 上传文件
            file_path = self.storage.upload_file(
                file_data,
                f"bank_statements/{datetime.now().strftime('%Y%m%d')}/{uuid4()}_{file_name}",
                "image/jpeg"
            )
            logger.info(f"[创建银行流水记录] 文件上传成功: {file_path}")
            
            # 2. 处理图片
            transactions = self.process_bank_statement(file_data, bank_type)
            logger.info(f"[创建银行流水记录] 图片处理完成，获取到{len(transactions)}条交易记录")
            
            # 3. 保存到数据库
            logger.info("\n" + "-"*30 + " 保存到数据库开始 " + "-"*30)
            db_statements = []
            for trans in transactions:
                db_statement = BankStatement(
                    account_number=trans["account_number"],
                    transaction_date=trans["transaction_date"],
                    transaction_type=trans["transaction_type"],
                    amount=trans["amount"],
                    balance=trans["balance"],
                    counterparty=trans["counterparty"],
                    description=trans["description"],
                    bank_type=bank_type,
                    file_path=file_path,
                    created_at=datetime.now()
                )
                db.add(db_statement)
                db_statements.append(db_statement)
            
            db.commit()
            logger.info("-"*30 + " 保存到数据库完成 " + "-"*30 + "\n")
            logger.info("="*50 + "\n")
            return db_statements
            
        except Exception as e:
            logger.error(f"\n[错误] 创建银行流水记录失败: {str(e)}")
            logger.error("="*50 + "\n")
            db.rollback()
            # 删除已上传的文件
            if "file_path" in locals():
                self.storage.delete_file(file_path)
            raise e
    
    def get_bank_statements(
        self,
        db: Session,
        skip: int = 0,
        limit: Optional[int] = 100,
        bank_type: Optional[str] = None,
        account_number: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[BankStatement]:
        """获取银行流水记录列表"""
        query = db.query(BankStatement)
        
        if bank_type:
            query = query.filter(BankStatement.bank_type == bank_type)
        if account_number:
            query = query.filter(BankStatement.account_number == account_number)
        if start_date:
            query = query.filter(BankStatement.transaction_date >= start_date)
        if end_date:
            query = query.filter(BankStatement.transaction_date <= end_date)
            
        if limit:
            query = query.offset(skip).limit(limit)
        
        return query.all()
    
    def get_bank_statement(self, db: Session, statement_id: int) -> Optional[BankStatement]:
        """获取单条银行流水记录"""
        return db.query(BankStatement).filter(BankStatement.id == statement_id).first()
    
    def update_bank_statement(
        self,
        db: Session,
        statement_id: int,
        statement: BankStatementUpdate
    ) -> Optional[BankStatement]:
        """更新银行流水记录"""
        db_statement = self.get_bank_statement(db, statement_id)
        if not db_statement:
            return None
            
        for field, value in statement.dict(exclude_unset=True).items():
            setattr(db_statement, field, value)
        
        db.commit()
        db.refresh(db_statement)
        return db_statement
    
    def delete_bank_statement(self, db: Session, statement_id: int) -> bool:
        """删除银行流水记录"""
        db_statement = self.get_bank_statement(db, statement_id)
        if not db_statement:
            return False
            
        # 删除关联的文件
        if db_statement.file_path:
            self.storage.delete_file(db_statement.file_path)
        
        db.delete(db_statement)
        db.commit()
        return True
        
    def get_statistics(
        self,
        db: Session,
        account_number: Optional[str] = None,
        bank_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """获取统计数据
        
        Args:
            db: 数据库会话
            account_number: 账号
            bank_type: 银行类型
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            统计结果字典，包含：
            - total_income: 总收入
            - total_expense: 总支出
            - net_amount: 净额
            - transaction_count: 交易笔数
        """
        # 获取符合条件的所有记录
        statements = self.get_bank_statements(
            db=db,
            skip=0,
            limit=None,  # 不限制数量，获取所有记录
            account_number=account_number,
            bank_type=bank_type,
            start_date=start_date,
            end_date=end_date
        )
        
        # 计算统计数据
        total_income = sum(
            s.amount for s in statements 
            if s.transaction_type == "收入"
        )
        total_expense = sum(
            s.amount for s in statements 
            if s.transaction_type == "支出"
        )
        
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_amount": total_income - total_expense,
            "transaction_count": len(statements)
        }
        
    def batch_delete_bank_statements(self, db: Session, statement_ids: List[int]) -> bool:
        """批量删除银行流水记录
        
        Args:
            db: 数据库会话
            statement_ids: 要删除的记录ID列表
            
        Returns:
            是否删除成功
        """
        try:
            # 获取要删除的记录
            statements = db.query(BankStatement).filter(
                BankStatement.id.in_(statement_ids)
            ).all()
            
            # 删除关联的文件
            for statement in statements:
                if statement.file_path:
                    self.storage.delete_file(statement.file_path)
            
            # 批量删除记录
            db.query(BankStatement).filter(
                BankStatement.id.in_(statement_ids)
            ).delete(synchronize_session=False)
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            print(f"批量删除失败: {str(e)}")
            raise Exception(f"批量删除失败: {str(e)}")