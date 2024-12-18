from datetime import datetime
import re
from typing import Dict, Any, List
import json

from .base import BankStatementParser
from app.services.baidu_service import BaiduOCRService, BaiduNLPService

class BeijingBankParser(BankStatementParser):
    """北京银行流水解析器"""
    
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
                        amount_text = cell_texts[3].split('\n')[0]
                        amount_text = amount_text.replace(',', '')
                        amount_text = re.sub(r'[^\d.-]', '', amount_text)
                        transaction["amount"] = abs(float(amount_text))  # 使用绝对值
                    except:
                        print(f"  解析金额失败: {cell_texts[3]}")
                
                # 5. 处理余额（第4列）
                if 4 in cell_texts:
                    try:
                        balance_text = cell_texts[4].split('\n')[0]
                        balance_text = balance_text.replace(',', '')
                        balance_text = re.sub(r'[^\d.-]', '', balance_text)
                        transaction["balance"] = float(balance_text)
                    except:
                        print(f"  解析余额失败: {cell_texts[4]}")
                
                # 6. 处理对方信息（第5列及以后）
                all_texts = []
                for col in sorted(cell_texts.keys()):
                    if col >= 5:
                        texts = cell_texts[col].split('\n')
                        all_texts.extend(texts)
                
                if all_texts:
                    combined_text = ' '.join(text.strip() for text in all_texts if text.strip())
                    cleaned_text = self._clean_counterparty_text(combined_text)
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
    
    def _clean_counterparty_text(self, text: str) -> str:
        """清理对方信息文本"""
        if not text:
            return ""
            
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        
        return text.strip() 