from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
import os
from minio import Minio
from dotenv import load_dotenv
import json
import re

from app.models.bank_statement import BankStatement
from app.schemas.bank_statement import BankStatementCreate, BankStatementUpdate
from app.services.baidu_service import BaiduOCRService, BaiduNLPService

load_dotenv()

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
            print(f"删除文件失败: {str(e)}")
            return False

class BankStatementService:
    def __init__(self):
        self.storage = MinioStorage()
        self.ocr_service = BaiduOCRService()
        self.nlp_service = BaiduNLPService()
    
    def process_bank_statement(self, image_data: bytes) -> dict:
        """处理银行流水图片"""
        try:
            # 1. OCR识别表格
            ocr_result = self.ocr_service.recognize_table(image_data)
            print("OCR识别结果:", json.dumps(ocr_result, ensure_ascii=False, indent=2))
            
            # 2. 处理OCR结果
            if not isinstance(ocr_result, dict):
                raise Exception(f"OCR返回格式错误: {type(ocr_result)}")
                
            if "tables_result" not in ocr_result:
                # 如果没有识别到表格，尝试普通文字识别
                return self.process_text_ocr(image_data)
                
            if not ocr_result["tables_result"]:
                raise Exception("未识别到表格内容")
                
            table_data = ocr_result["tables_result"][0]
            print("表格数据:", json.dumps(table_data, ensure_ascii=False, indent=2))
            
            if not isinstance(table_data, dict):
                raise Exception(f"表格数据格式错误: {type(table_data)}")
            
            # 3. 提取关键信息
            statement_data = {
                "account_number": None,
                "transaction_date": None,
                "transaction_type": None,
                "amount": None,
                "balance": None,
                "counterparty": None,
                "description": None
            }
            
            # 处理表头信息(账号等)
            if "header" in table_data and isinstance(table_data["header"], list):
                header_texts = []
                for item in table_data["header"]:
                    if isinstance(item, dict) and "words" in item:
                        header_texts.append(item["words"])
                
                print("表头文本:", header_texts)
                
                # 尝试从表头中提取账号
                for text in header_texts:
                    # 1. 首先尝试NLP实体识别
                    try:
                        entities = self.nlp_service.entity_recognize(text)
                        if isinstance(entities, list):
                            for entity in entities:
                                if isinstance(entity, dict) and entity.get("type") == "BANK_CARD":
                                    statement_data["account_number"] = entity.get("item")
                                    break
                    except Exception as e:
                        print(f"NLP实体识别失败: {str(e)}")
                    
                    # 2. 如果NLP失败，尝试直接匹配数字
                    if not statement_data["account_number"]:
                        # 查找"卡/账号:"后面的数字
                        card_match = re.search(r'[卡账][/号][:：]\s*(\d+)', text)
                        if card_match:
                            statement_data["account_number"] = card_match.group(1)
                            continue
                            
                        # 直接查找连续数字
                        numbers = re.findall(r'\d{10,}', text)
                        if numbers:
                            statement_data["account_number"] = numbers[0]
            
            # 处理表格主体
            transactions = []
            rows = []
            
            # 根据行号分组单元格
            row_cells = {}
            if "body" in table_data:
                for cell in table_data["body"]:
                    if isinstance(cell, dict) and "row_start" in cell and "words" in cell:
                        row_idx = cell.get("row_start")
                        col_idx = cell.get("col_start", 0)
                        if row_idx not in row_cells:
                            row_cells[row_idx] = []
                        row_cells[row_idx].append((col_idx, cell["words"]))
            
            # 处理每一行
            for row_idx in sorted(row_cells.keys()):
                cells = row_cells[row_idx]
                cells.sort(key=lambda x: x[0])  # 按列索引排序
                
                transaction = statement_data.copy()
                print(f"\n处理第{row_idx}行:")
                
                # 提取所有单元格文本，用于后续处理
                cell_texts = {col: text.strip() for col, text in cells}
                print("  单元格文本:", cell_texts)
                
                try:
                    # 跳过表头行
                    if row_idx == 0 or any(header in str(cell_texts.get(0, "")) for header in ["交易日期", "日期"]):
                        print("  跳过表头行")
                        continue
                        
                    # 1. 处理交易日期（第0列）
                    if 0 in cell_texts:
                        date_text = cell_texts[0].split('\n')[0]  # 如果有重复日期，只取第一个
                        date_text = re.sub(r'[^\d]', '', date_text)  # 只保留数字
                        try:
                            transaction["transaction_date"] = datetime.strptime(date_text, "%Y%m%d")
                        except:
                            print(f"  解析日期失败: {date_text}")
                    
                    # 2. 处理业务种类（第1列）
                    if 1 in cell_texts:
                        business_type = cell_texts[1].split('\n')[0].strip()  # 如果有重复，只取第一个
                        transaction["description"] = business_type
                        
                        # 根据业务种类辅助判断交易类型
                        if any(word in business_type for word in ["收款", "收入", "利息", "汇入", "转入", "医保"]):
                            transaction["transaction_type"] = "收入"
                        elif any(word in business_type for word in ["支付", "汇款", "转账", "消费", "支取", "转出"]):
                            transaction["transaction_type"] = "支出"
                    
                    # 3. 处理收支标志（第2列）
                    if 2 in cell_texts:
                        text = cell_texts[2].split('\n')[0].strip()  # 如果有重复，只取第一个
                        if text:
                            # 如果有明确的收支标志，优先使用
                            transaction["transaction_type"] = "收入" if "收入" in text else "支出"
                    
                    # 4. 处理发生额（第3列）
                    if 3 in cell_texts:
                        try:
                            # 如果有重复金额，只取第一个
                            amount_text = cell_texts[3].split('\n')[0]
                            # 移除千位分隔符和其他非数字字符
                            amount_text = amount_text.replace(',', '')
                            amount_text = re.sub(r'[^\d.-]', '', amount_text)
                            transaction["amount"] = abs(float(amount_text))  # 使用绝对值
                        except:
                            print(f"  解析金额失败: {cell_texts[3]}")
                    
                    # 5. 处理余额（第4列）
                    if 4 in cell_texts:
                        try:
                            # 如果有重复余额，只取第一个
                            balance_text = cell_texts[4].split('\n')[0]
                            # 移除千位分隔符和其他非数字字符
                            balance_text = balance_text.replace(',', '')
                            balance_text = re.sub(r'[^\d.-]', '', balance_text)
                            transaction["balance"] = float(balance_text)
                        except:
                            print(f"  解析余额失败: {cell_texts[4]}")
                    
                    # 6. 处理对方信息（第5列及以后）
                    all_texts = []
                    
                    # 收集所有文本
                    for col in sorted(cell_texts.keys()):
                        if col >= 5:
                            texts = cell_texts[col].split('\n')
                            all_texts.extend(texts)
                    
                    # 合并所有文���并清理
                    if all_texts:
                        # 合并所有文本，保留空格以防止不同部分的数字意外连接
                        combined_text = ' '.join(text.strip() for text in all_texts if text.strip())
                        cleaned_text = self.clean_counterparty_text(combined_text)
                        if cleaned_text:
                            transaction["counterparty"] = cleaned_text
                    
                    print("  处理后的交易数据:", transaction)
                    # 放宽验证条件：只要有金额就认为是有效记录
                    if transaction["amount"] is not None:
                        transactions.append(transaction)
                        
                except Exception as e:
                    print(f"  处理行数据失败: {str(e)}")
            
            if not transactions:
                raise Exception("未能提取到有效的交易记录")
                
            print(f"成功提取到{len(transactions)}条交易记录")
            return transactions
            
        except Exception as e:
            print(f"处理银行流水图片失败: {str(e)}")
            raise Exception(f"处理银行流水图片失败: {str(e)}")
            
    def process_text_ocr(self, image_data: bytes) -> dict:
        """处理普通文字识别结果"""
        try:
            # 使用手写文字识别
            ocr_result = self.ocr_service.recognize_handwriting(image_data)
            print("文字识别结果:", json.dumps(ocr_result, ensure_ascii=False, indent=2))
            
            if "words_result" not in ocr_result:
                raise Exception("未识别到文字内容")
                
            # 提取所有文本
            texts = [item["words"] for item in ocr_result["words_result"]]
            print("识别到的文本:", texts)
            
            # 尝试从文本中提取交易信息
            transaction = {
                "account_number": None,
                "transaction_date": None,
                "transaction_type": None,
                "amount": None,
                "balance": None,
                "counterparty": None,
                "description": None
            }
            
            # 遍历每一行文本
            for text in texts:
                # 1. 尝试提取账号
                if not transaction["account_number"]:
                    numbers = re.findall(r'\d{10,}', text)
                    if numbers:
                        transaction["account_number"] = numbers[0]
                        continue
                
                # 2. 尝试提取日期
                if not transaction["transaction_date"]:
                    date_patterns = [
                        r'(\d{4})[/-.](\d{1,2})[/-.](\d{1,2})',
                        r'(\d{4})年(\d{1,2})月(\d{1,2})日'
                    ]
                    for pattern in date_patterns:
                        match = re.search(pattern, text)
                        if match:
                            try:
                                year, month, day = match.groups()
                                transaction["transaction_date"] = datetime(int(year), int(month), int(day))
                                break
                            except:
                                continue
                
                # 3. 尝试提取金额
                if not transaction["amount"]:
                    amount_pattern = r'(?:金额|￥|¥)\s*([0-9,.]+)'
                    match = re.search(amount_pattern, text)
                    if match:
                        try:
                            amount_text = match.group(1).replace(',', '')
                            transaction["amount"] = float(amount_text)
                        except:
                            pass
                
                # 4. 判断交易类型
                if "收入" in text or "存入" in text:
                    transaction["transaction_type"] = "收入"
                elif "支出" in text or "转出" in text:
                    transaction["transaction_type"] = "支出"
                
                # 5. 其他信息为描述
                if not transaction["description"]:
                    transaction["description"] = text
            
            # 只要有金额就认为是有记录
            if transaction["amount"] is not None:
                return [transaction]
            else:
                raise Exception("未能从文本中提取到交易信息")
                
        except Exception as e:
            print(f"处理文字识别失败: {str(e)}")
            raise Exception(f"处理文字识别失败: {str(e)}")
    
    def create_bank_statement(self, db: Session, file_data: bytes, statement_data: BankStatementCreate) -> BankStatement:
        """创建银行流水记录"""
        try:
            # 1. 处理图片
            transactions = self.process_bank_statement(file_data)
            
            # 2. 生成唯一文件名并保存文件
            file_name = f"{uuid4()}.jpg"
            file_path = self.storage.upload_file(
                file_data,
                file_name,
                content_type="image/jpeg"
            )
            
            # 3. 创建记录
            created_statements = []
            for transaction in transactions:
                db_statement = BankStatement(
                    file_path=file_path,
                    **transaction
                )
                db.add(db_statement)
                created_statements.append(db_statement)
            
            db.commit()
            for statement in created_statements:
                db.refresh(statement)
            
            return created_statements[0] if created_statements else None
            
        except Exception as e:
            db.rollback()
            raise Exception(f"创建银行流水记录失败: {str(e)}")
    
    def get_bank_statement(self, db: Session, statement_id: int) -> Optional[BankStatement]:
        """获取单条银行流水记录"""
        return db.query(BankStatement).filter(BankStatement.id == statement_id).first()
    
    def get_bank_statements(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        account_number: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[BankStatement], int]:
        """获取银行流水列表"""
        query = db.query(BankStatement)
        
        if account_number:
            query = query.filter(BankStatement.account_number == account_number)
        if start_date:
            query = query.filter(BankStatement.transaction_date >= start_date)
        if end_date:
            query = query.filter(BankStatement.transaction_date <= end_date)
            
        # 先获取总记录数
        total = query.count()
        
        # 再获取分页数据
        statements = query.offset(skip).limit(limit).all()
            
        return statements, total
    
    def update_bank_statement(
        self,
        db: Session,
        statement_id: int,
        statement_data: BankStatementUpdate
    ) -> Optional[BankStatement]:
        """更新银行流水记录"""
        db_statement = self.get_bank_statement(db, statement_id)
        if not db_statement:
            return None
            
        for field, value in statement_data.dict(exclude_unset=True).items():
            setattr(db_statement, field, value)
            
        db.commit()
        db.refresh(db_statement)
        return db_statement
    
    def delete_bank_statement(self, db: Session, statement_id: int) -> bool:
        """删除银行流水记录"""
        db_statement = self.get_bank_statement(db, statement_id)
        if not db_statement:
            return False
            
        # 删除MinIO中的文件
        if db_statement.file_path:
            try:
                self.storage.delete_file(db_statement.file_path)
            except Exception as e:
                print(f"删除文件失败: {str(e)}")
        
        db.delete(db_statement)
        db.commit()
        return True
    
    def get_statistics(
        self,
        db: Session,
        account_number: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """获取统计数据"""
        query = db.query(BankStatement)
        
        if account_number:
            query = query.filter(BankStatement.account_number == account_number)
        if start_date:
            query = query.filter(BankStatement.transaction_date >= start_date)
        if end_date:
            query = query.filter(BankStatement.transaction_date <= end_date)
            
        statements = query.all()
        
        total_income = sum(s.amount for s in statements if s.transaction_type == "收入")
        total_expense = sum(s.amount for s in statements if s.transaction_type == "支出")
        
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_amount": total_income - total_expense,
            "transaction_count": len(statements)
        } 
    
    def batch_delete_bank_statements(self, db: Session, ids: List[int]) -> bool:
        """批量删除银行流水记录"""
        try:
            # 获取所有要删除的记录
            statements = db.query(BankStatement).filter(BankStatement.id.in_(ids)).all()
            
            # 删除MinIO中的文件
            file_paths = set()  # 使用集合去重，因为可能多条记录使用同一个文件
            for statement in statements:
                if statement.file_path:
                    file_paths.add(statement.file_path)
            
            # 删除文件
            for file_path in file_paths:
                try:
                    self.storage.delete_file(file_path)
                except Exception as e:
                    print(f"删除文件失败: {str(e)}")
            
            # 删除数据库记录
            db.query(BankStatement).filter(BankStatement.id.in_(ids)).delete(synchronize_session=False)
            db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            print(f"批量删除失败: {str(e)}")
            raise Exception(f"批量删除失败: {str(e)}") 
    
    def clean_counterparty_text(self, text: str) -> str:
        """清理交易对方文本信息，只保留有效的账号"""
        if not text or text.isspace():
            return ""
            
        # 1. 定义已知的账号模式
        ACCOUNT_PATTERNS = [
            # 银联卡号（16-19位）
            r'(?<!\d)([3-6]\d{15,18})(?!\d)',
            # 银行账号（10-32位）
            r'(?<!\d)([1-9]\d{9,31})(?!\d)',
            # 特定前缀的账号
            r'(?<!\d)(621\d{13,16})(?!\d)',  # 银联借记卡
            r'(?<!\d)(622\d{13,16})(?!\d)',  # 银联借记卡
            r'(?<!\d)(623\d{13,16})(?!\d)',  # 银联借记卡
            r'(?<!\d)(620\d{13,16})(?!\d)',  # 银联借记卡
            # 特定格式的账号（例如：308999847890032）
            r'(?<!\d)(308\d{12})(?!\d)',
            # 其他常见账号格式
            r'(?<!\d)(215500\d{4})(?!\d)',
            r'(?<!\d)(180000\d{4})(?!\d)',
            r'(?<!\d)(243300\d{3})(?!\d)',
            r'(?<!\d)(118397\d{4})(?!\d)'
        ]
        
        # 2. 查找所有可能的账号
        candidates = []
        for pattern in ACCOUNT_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                number = match.group(1)
                # 基本验证
                if self.is_valid_account_number(number):
                    candidates.append(number)
        
        if not candidates:
            return ""
            
        # 3. 如果找到多个账号，选择最合适的一个
        if len(candidates) == 1:
            return candidates[0]
            
        # 优先选择已知格式的账号
        for number in candidates:
            # 优先选择308开头的账号
            if number.startswith('308'):
                return number
            # 其次选择21550开头的账号
            if number.startswith('21550'):
                return number
            # 再次选择11839开头的账号
            if number.startswith('11839'):
                return number
        
        # 如果没有特定格式的账号，返回最长的那个
        return max(candidates, key=len)
    
    def is_valid_account_number(self, number: str) -> bool:
        """验证是否是有效的账号"""
        # 1. 长度检查（10-32位）
        if not (10 <= len(number) <= 32):
            return False
            
        # 2. 不能全是相同的数字
        if len(set(number)) == 1:
            return False
            
        # 3. 不能是简单的递增或递减序列
        is_increasing = all(int(number[i]) <= int(number[i+1]) for i in range(len(number)-1))
        is_decreasing = all(int(number[i]) >= int(number[i+1]) for i in range(len(number)-1))
        if is_increasing or is_decreasing:
            return False
            
        # 4. 必须以非0数字开头
        if not number[0].isdigit() or number[0] == '0':
            return False
            
        # 5. Luhn算法校验（针对银行卡号）
        if len(number) in [16, 19]:
            digits = [int(d) for d in number]
            checksum = 0
            for i in range(len(digits)-1, -1, -1):
                d = digits[i]
                if i % 2 == len(digits) % 2:  # 奇偶性取决于卡号长度
                    d *= 2
                    if d > 9:
                        d -= 9
                checksum += d
            if checksum % 10 != 0:
                return False
                
        return True