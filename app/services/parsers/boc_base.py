from typing import Dict, Any, List
from datetime import datetime
import re
import json

from .base import BankStatementParser
from app.services.baidu_service import BaiduOCRService, BaiduNLPService

class BOCBaseParser(BankStatementParser):
    """交通银行解析器基类"""
    
    def __init__(self):
        self.ocr_service = BaiduOCRService()
        self.nlp_service = BaiduNLPService()
        # 交易类型关键词映射
        self.transaction_type_keywords = {
            "收入": ["收入", "转入", "存入", "退款", "利息", "红包", "汇入", "代发工资"],
            "支出": ["支出", "转出", "消费", "取款", "手续费", "年费", "跨行汇款"],
            "转账": ["转账", "汇款", "代付", "代发"],
            "其他": ["冲正", "撤销", "退回"]
        }
    
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
            
        # 尝试识别账号
        try:
            # 使用通用文字识别获取完整文本
            general_result = self.ocr_service.recognize_general(image_data)
            if isinstance(general_result, dict) and "words_result" in general_result:
                words_result = general_result["words_result"]
                if isinstance(words_result, list):
                    # 遍历所有文本行，查找账号
                    for item in words_result:
                        if isinstance(item, dict) and "words" in item:
                            text = item["words"]
                            # 尝试匹配账号
                            account_match = re.search(r'账[号|户][:：]?\s*(\d{10,})', text)
                            if account_match:
                                table_data["account_number"] = account_match.group(1)
                                break
        except Exception as e:
            print(f"识别账号失败: {str(e)}")
        
        return table_data
    
    def validate_data(self, cleaned_data: List[Dict[str, Any]]) -> bool:
        """验证数据有效性"""
        if not cleaned_data:
            return False
            
        for transaction in cleaned_data:
            # 验证必要字段
            if not all(key in transaction for key in ["transaction_date", "amount", "transaction_type"]):
                return False
                
            # 验证字段类型
            if not isinstance(transaction["transaction_date"], datetime):
                return False
            if not isinstance(transaction["amount"], (int, float)):
                return False
            if not isinstance(transaction["transaction_type"], str):
                return False
                
            # 验证金额
            if transaction["amount"] <= 0:
                return False
                
            # 验证交易类型
            if transaction["transaction_type"] not in ["收入", "支出", "转账", "其他"]:
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
        """转换金额字符串为float
        
        Args:
            amount_str: 金额字符串
            
        Returns:
            float: 转换后的金额，如果转换失败返回None
        """
        try:
            if not amount_str or not isinstance(amount_str, str):
                return None
                
            # 清理金额字符串
            amount_str = amount_str.strip()
            
            # 处理特殊符号
            amount_str = amount_str.replace('¥', '')  # 处理人民币符号
            amount_str = amount_str.replace('￥', '')
            amount_str = amount_str.replace(',', '')  # 处理千位分隔符
            amount_str = amount_str.replace('，', '')  # 处理中文逗号
            amount_str = amount_str.replace(' ', '')  # 处理空格
            
            # 处理中文数字
            cn_nums = {'零':0, '一':1, '二':2, '三':3, '四':4, '五':5, '六':6, '七':7, '八':8, '九':9}
            for cn, num in cn_nums.items():
                amount_str = amount_str.replace(cn, str(num))
            
            # 移除其他非数字字符（保留小数点和负号）
            amount_str = ''.join(c for c in amount_str if c.isdigit() or c in '.-')
            
            if not amount_str:
                return None
                
            # 处理多个小数点
            if amount_str.count('.') > 1:
                # 只保留第一个小数点
                first_dot = amount_str.index('.')
                amount_str = amount_str[:first_dot+1] + amount_str[first_dot+1:].replace('.', '')
            
            # 转换为float
            amount = float(amount_str)
            
            # 处理异常值
            if amount > 999999999999:  # 金额不应超过1万亿
                print(f"警告：金额 {amount} 可能异常")
                return None
                
            return amount
            
        except Exception as e:
            print(f"金额转换失败: {amount_str}, 错误: {str(e)}")
            return None 