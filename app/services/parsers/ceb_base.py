from datetime import datetime
import re
from typing import Dict, Any, List
import json

from .base import BankStatementParser
from app.services.baidu_service import BaiduOCRService, BaiduNLPService

class CEBBaseParser(BankStatementParser):
    """光大银行基础解析器"""
    
    def __init__(self):
        self.ocr_service = BaiduOCRService()
        self.nlp_service = BaiduNLPService()
    
    def parse(self, image_data: bytes) -> Dict[str, Any]:
        """解析银行流水图片"""
        # OCR识别表格
        ocr_result = self.ocr_service.recognize_table(image_data)
        print("OCR识别结果:", json.dumps(ocr_result, ensure_ascii=False, indent=2))
        
        # 处理OCR结果
        if not isinstance(ocr_result, dict):
            raise Exception(f"OCR返回格式错误: {type(ocr_result)}")
            
        if "tables_result" not in ocr_result:
            raise Exception("未识别到表格内容")
            
        if not ocr_result["tables_result"]:
            raise Exception("未识别到表格内容")
            
        table_data = ocr_result["tables_result"][0]
        print("表格数据:", json.dumps(table_data, ensure_ascii=False, indent=2))
        
        if not isinstance(table_data, dict):
            raise Exception(f"表格数据格式错误: {type(table_data)}")
        
        return table_data
    
    def clean_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """清洗数据"""
        transactions = []
        
        # 初始化数据结构
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
        if "header" in raw_data and isinstance(raw_data["header"], list):
            header_texts = []
            for item in raw_data["header"]:
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
                    # 查找账号
                    card_matches = [
                        r'卡号[：:]\s*(\d+)',
                        r'账号[：:]\s*(\d+)',
                        r'账户[：:]\s*(\d+)',
                        r'(\d{16,19})'  # 银行卡号一般是16-19位
                    ]
                    for pattern in card_matches:
                        match = re.search(pattern, text)
                        if match:
                            statement_data["account_number"] = match.group(1)
                            break
        
        # 处理表格主体
        row_cells = {}
        if "body" in raw_data:
            for cell in raw_data["body"]:
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
            
            # 提取所有单元格文本
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
                
                # 2. 处理存入金额和转出金额
                deposit_amount = 0.0
                withdraw_amount = 0.0
                
                # 存入金额列
                if 2 in cell_texts:
                    try:
                        amount_text = cell_texts[2].replace(',', '')
                        amount_text = re.sub(r'[^\d.]', '', amount_text)
                        if amount_text:
                            deposit_amount = float(amount_text)
                    except:
                        print(f"  解析存入金额失败: {cell_texts[2]}")
                
                # 转出金额列
                if 3 in cell_texts:
                    try:
                        amount_text = cell_texts[3].replace(',', '')
                        amount_text = re.sub(r'[^\d.]', '', amount_text)
                        if amount_text:
                            withdraw_amount = float(amount_text)
                    except:
                        print(f"  解析转出金额失败: {cell_texts[3]}")
                
                # 设置交易类型和金额
                if deposit_amount > 0:
                    transaction["transaction_type"] = "收入"
                    transaction["amount"] = deposit_amount
                elif withdraw_amount > 0:
                    transaction["transaction_type"] = "支出"
                    transaction["amount"] = withdraw_amount
                
                # 3. 处理账户余额（第4列）
                if 4 in cell_texts:
                    try:
                        balance_text = cell_texts[4].replace(',', '')
                        balance_text = re.sub(r'[^\d.]', '', balance_text)
                        if balance_text:
                            transaction["balance"] = float(balance_text)
                    except:
                        print(f"  解析余额失败: {cell_texts[4]}")
                
                # 4. 处理交易摘要（第5列）
                if 5 in cell_texts:
                    transaction["description"] = cell_texts[5].strip()
                
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
    
    def validate_data(self, cleaned_data: List[Dict[str, Any]]) -> bool:
        """验证数据有效性"""
        if not cleaned_data:
            return False
            
        for transaction in cleaned_data:
            # 必需字段检查
            if transaction.get("amount") is None:
                return False
                
            # 日期格式检查
            if transaction.get("transaction_date") and not isinstance(transaction["transaction_date"], datetime):
                return False
                
            # 金额格式检查
            if not isinstance(transaction.get("amount"), (int, float)):
                return False
                
            if transaction.get("balance") is not None and not isinstance(transaction["balance"], (int, float)):
                return False
        
        return True 