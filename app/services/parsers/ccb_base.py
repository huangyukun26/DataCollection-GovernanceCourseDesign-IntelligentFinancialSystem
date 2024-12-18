from datetime import datetime
import re
from typing import Dict, Any, List
import json

from .base import BankStatementParser
from app.services.baidu_service import BaiduOCRService, BaiduNLPService

class CCBBaseParser(BankStatementParser):
    """建设银行流水解析器基类"""
    
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
    
    def _convert_date(self, date_str: str) -> datetime:
        """转换日期字符串为datetime对象"""
        try:
            # 移除非数字字符
            date_str = re.sub(r'[^\d]', '', date_str)
            if len(date_str) >= 8:
                return datetime.strptime(date_str[:8], '%Y%m%d')
        except:
            pass
        return None
    
    def _convert_amount(self, amount_str: str) -> float:
        """转换金额字符串为float"""
        try:
            # 移除逗号和空格
            amount_str = amount_str.replace(',', '').strip()
            # 提取数字（包括小数点）
            amount_str = re.sub(r'[^\d.]', '', amount_str)
            if amount_str:
                return float(amount_str)
        except:
            pass
        return 0.0
