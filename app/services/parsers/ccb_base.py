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
        # OCR识别表格和文字
        ocr_result = self.ocr_service.recognize_table_and_text(image_data)
        print("完整OCR识别结果:", json.dumps(ocr_result, ensure_ascii=False, indent=2))
        
        # 处理OCR结果
        if not isinstance(ocr_result, dict):
            raise Exception(f"OCR返回格式错误: {type(ocr_result)}")
            
        if "tables_result" not in ocr_result:
            raise Exception("未识别到表格内容")
            
        if not ocr_result["tables_result"]:
            raise Exception("未识别到表格内容")
            
        table_data = ocr_result["tables_result"][0]
        print("\n表格数据:", json.dumps(table_data, ensure_ascii=False, indent=2))
        
        if not isinstance(table_data, dict):
            raise Exception(f"表格数据格式错误: {type(table_data)}")
        
        # 尝试从所有可能的位置提取账号
        account_number = None
        
        # 1. 从words_result提取（优先处理，因为可能包含表格外的文本）
        if "words_result" in ocr_result:
            print("\n尝试从words_result提取账号:")
            if isinstance(ocr_result["words_result"], list):
                # 合并所有文本
                all_text = ""
                for item in ocr_result["words_result"]:
                    if isinstance(item, dict) and "words" in item:
                        text = item.get("words", "").strip()
                        all_text += text + " "
                        print(f"处理文本: {text}")
                        # 单独处理每个文本
                        account_number = self._extract_account_number(text)
                        if account_number:
                            print(f"从单个words_result提取到账号: {account_number}")
                            break
                
                # 如果单独处理没找到，尝试处理合并后的文本
                if not account_number and all_text:
                    print(f"处理合并后的文本: {all_text}")
                    account_number = self._extract_account_number(all_text)
                    if account_number:
                        print(f"从合并的words_result提取到账号: {account_number}")
        
        # 2. 从表头提取
        if not account_number and "header" in table_data:
            print("\n尝试从header提取账号:")
            if isinstance(table_data["header"], list):
                # 合并所有表头文本
                header_text = ""
                for item in table_data["header"]:
                    if isinstance(item, dict) and "words" in item:
                        text = item.get("words", "").strip()
                        header_text += text + " "
                        print(f"处理文本: {text}")
                        # 单独处理每个表头
                        account_number = self._extract_account_number(text)
                        if account_number:
                            print(f"从单个header提取到账号: {account_number}")
                            break
                
                # 如果单独处理没找到，尝试处理合并后的文本
                if not account_number and header_text:
                    print(f"处理合并后的文本: {header_text}")
                    account_number = self._extract_account_number(header_text)
                    if account_number:
                        print(f"从合并的header提取到账号: {account_number}")
        
        # 3. 从title提取
        if not account_number and "title" in ocr_result:
            print("\n尝试从title提取账号:")
            if isinstance(ocr_result["title"], list):
                # 合并所有标题文本
                title_text = ""
                for item in ocr_result["title"]:
                    if isinstance(item, dict) and "words" in item:
                        text = item.get("words", "").strip()
                        title_text += text + " "
                        print(f"处理文本: {text}")
                        # 单独处理每个标题
                        account_number = self._extract_account_number(text)
                        if account_number:
                            print(f"从单个title提取到账号: {account_number}")
                            break
                
                # 如果单独处理没找到，尝试处理合并后的文本
                if not account_number and title_text:
                    print(f"处理合并后的文本: {title_text}")
                    account_number = self._extract_account_number(title_text)
                    if account_number:
                        print(f"从合并的title提取到账号: {account_number}")
        
        # 4. 从body提取（可能在表格的第一行）
        if not account_number and "body" in table_data:
            print("\n尝试从body提取账号:")
            if isinstance(table_data["body"], list):
                # 获取第一行的所有单元格
                first_row_text = ""
                for cell in table_data["body"]:
                    if isinstance(cell, dict) and cell.get("row_start", -1) == 0:
                        text = cell.get("words", "").strip()
                        first_row_text += text + " "
                        print(f"处理文本: {text}")
                        # 单独处理每个单元格
                        account_number = self._extract_account_number(text)
                        if account_number:
                            print(f"从单个body cell提取到账号: {account_number}")
                            break
                
                # 如果单独处理没找到，尝试处理合并后的文本
                if not account_number and first_row_text:
                    print(f"处理合并后的文本: {first_row_text}")
                    account_number = self._extract_account_number(first_row_text)
                    if account_number:
                        print(f"从合并的body提取到账号: {account_number}")
        
        # 5. 从原始文本中提取
        if not account_number and "raw_text" in ocr_result:
            print("\n尝试从raw_text提取账号:")
            text = str(ocr_result["raw_text"])
            print(f"处理文本: {text}")
            account_number = self._extract_account_number(text)
            if account_number:
                print(f"从raw_text提取到账号: {account_number}")
        
        # 6. 从所有文本合并提取
        if not account_number:
            print("\n尝试从所有文本合并提取账号:")
            all_text = ""
            
            # 合并所有可能的文本
            if "words_result" in ocr_result and isinstance(ocr_result["words_result"], list):
                for item in ocr_result["words_result"]:
                    if isinstance(item, dict) and "words" in item:
                        all_text += item.get("words", "").strip() + " "
            
            if "header" in table_data and isinstance(table_data["header"], list):
                for item in table_data["header"]:
                    if isinstance(item, dict) and "words" in item:
                        all_text += item.get("words", "").strip() + " "
            
            if "title" in ocr_result and isinstance(ocr_result["title"], list):
                for item in ocr_result["title"]:
                    if isinstance(item, dict) and "words" in item:
                        all_text += item.get("words", "").strip() + " "
            
            if "body" in table_data and isinstance(table_data["body"], list):
                for cell in table_data["body"]:
                    if isinstance(cell, dict) and cell.get("row_start", -1) == 0:
                        all_text += cell.get("words", "").strip() + " "
            
            if all_text:
                print(f"处理合并后的所有文本: {all_text}")
                account_number = self._extract_account_number(all_text)
                if account_number:
                    print(f"从合并的所有文本提取到账号: {account_number}")
        
        if account_number:
            table_data["account_number"] = account_number
            print(f"\n最终提取到的账号: {account_number}")
        else:
            print("\n未能从任何位置提取到账号")
            
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
        """转换金额字符串为float
        
        Args:
            amount_str: 金额字符串
            
        Returns:
            float: 转换后的金额，如果转换失败返回0.0
        """
        try:
            if not amount_str or not isinstance(amount_str, str):
                return 0.0
                
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
                return 0.0
                
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
                return 0.0
                
            return amount
            
        except Exception as e:
            print(f"金额转换失败: {amount_str}, 错误: {str(e)}")
            return 0.0
    
    def _extract_account_number(self, text: str) -> str:
        """从文本中提取银行账号
        
        Args:
            text: 待提取的文本
            
        Returns:
            str: 提取到的账号，如果未提取到返回None
        """
        if not text or not isinstance(text, str):
            return None
            
        # 清理文本
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # 合并多个空格
        print(f"处理文本: {text}")
        
        # 1. 直接匹��账号字段
        account_matches = [
            # 标准格式（支持中文冒号和英文冒号）
            r'账号[：:]\s*(\d{18,19})',
            r'账号[：:]\s*[：:]\s*(\d{18,19})',  # 支持双冒号
            r'账\s*号[：:]\s*(\d{18,19})',
            r'账\s*号[：:]\s*[：:]\s*(\d{18,19})',  # 支持双冒号
            r'账号[：:]\s*[：:]*\s*(\d{18,19})',  # 支持可选的双冒号
            r'账\s*号[：:]\s*[：:]*\s*(\d{18,19})',  # 支持可选的双冒号
            r'账\s*号\s*[：:]\s*(\d{18,19})',
            r'账\s*号\s*[：:]\s*[：:]\s*(\d{18,19})',  # 支持双冒号
            # 支持账号和其他文字混合的情况
            r'.*?账号.*?[：:]\s*(\d{18,19}).*',
            r'.*?账\s*号.*?[：:]\s*(\d{18,19}).*',
            r'.*?账号.*?[：:]*\s*(\d{18,19}).*',
            r'.*?账\s*号.*?[：:]*\s*(\d{18,19}).*',
            # 支持账号在开头的情况
            r'^[：:]*\s*(\d{18,19})',
            r'^\s*[：:]*\s*(\d{18,19})',
            r'^\s*(\d{18,19})',
            # 支持账号在末尾的情况
            r'[：:]*\s*(\d{18,19})\s*$',
            r'\s*(\d{18,19})\s*$',
            # 支持账号前后有其他字符的情况
            r'[^0-9](\d{18,19})[^0-9]',
            r'^(\d{18,19})[^0-9]',
            r'[^0-9](\d{18,19})$',
            # 支持账号在任意位置
            r'.*?(\d{18,19}).*',
            # 支持账号前有文字的情况
            r'.*账号.*?(\d{18,19})',
            r'.*账\s*号.*?(\d{18,19})',
            # 支持账号后有文字的情况
            r'(\d{18,19}).*账号',
            r'(\d{18,19}).*账\s*号',
            # 支持无冒号的情况
            r'账号\s*(\d{18,19})',
            r'账\s*号\s*(\d{18,19})',
            # 支持纯数字的情况（建设银行账号格式）
            r'(\d{18,19})',
            # 支持账号和其他标点符号混合的情况
            r'.*?[账帐][号码][^0-9]*(\d{18,19}).*',
            r'.*?[账帐][号码]\s*[:：]\s*(\d{18,19}).*',
            r'.*?[账帐][号码]\s*[:：]*\s*(\d{18,19}).*',
            # 支持账号和其他关键词混合的情况
            r'.*?户名.*?[账帐][号码].*?(\d{18,19}).*',
            r'.*?账户.*?[账帐][号码].*?(\d{18,19}).*',
            r'.*?账户名称.*?[账帐][号码].*?(\d{18,19}).*',
            # 支持账号和币种混合的情况
            r'.*?(\d{18,19}).*?人民币.*',
            r'.*?人民币.*?(\d{18,19}).*',
            # 支持特殊格式
            r'.*?[账帐][号码][：: ]*(\d{18,19}).*',
            r'.*?[账帐]\s*[号码][：: ]*(\d{18,19}).*',
            r'.*?[账帐][号码]\s*[：: ]*(\d{18,19}).*',
            r'.*?[账帐]\s*[号码]\s*[：: ]*(\d{18,19}).*'
        ]
        
        for pattern in account_matches:
            match = re.search(pattern, text)
            if match:
                account = match.group(1)
                if 16 <= len(account) <= 19:
                    print(f"匹配到账号: {account}，使用模式: {pattern}")
                    return account
        
        # 2. 直接匹配19位数字（建设银行标准账号长度）
        numbers = re.findall(r'\d{19}', text)
        if numbers:
            print(f"匹配到19位账号: {numbers[0]}")
            return numbers[0]
            
        # 3. 匹配18位数字（部分老账号）
        numbers = re.findall(r'\d{18}', text)
        if numbers:
            print(f"匹配到18位账号: {numbers[0]}")
            return numbers[0]
            
        # 4. 通过关键词匹配
        patterns = [
            r'账[号户][：:]\s*(\d{16,19})',
            r'账[号户]\s*[为是]?\s*(\d{16,19})',
            r'卡号[：:]\s*(\d{16,19})',
            r'账号/卡号[：:]\s*(\d{16,19})',
            # 支持横杠分隔的格式
            r'账号[：:]\s*(\d{4}-\d{4}-\d{4}-\d{4}-\d{3})',
            r'卡号[：:]\s*(\d{4}-\d{4}-\d{4}-\d{4}-\d{3})',
            # 支持空格分隔的格式
            r'账号[：:]\s*(\d{4}\s+\d{4}\s+\d{4}\s+\d{4}\s+\d{3})',
            r'卡号[：:]\s*(\d{4}\s+\d{4}\s+\d{4}\s+\d{4}\s+\d{3})',
            # 支持账号前缀
            r'账号[：:]\s*[A-Z]*(\d{16,19})',
            r'卡号[：:]\s*[A-Z]*(\d{16,19})',
            # 支持账户名称后的账号
            r'户名[：:][^：:]*[：:]\s*(\d{16,19})',
            # 支持账号后面带币种的情况
            r'(\d{16,19})\s*[/\s]*人民币',
            # 支持账号在文本中间的情况
            r'.*?(\d{16,19}).*',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # 移除横杠和空格
                account = match.group(1).replace('-', '').replace(' ', '')
                # 验证长度
                if 16 <= len(account) <= 19:
                    print(f"匹配到账号: {account}，使用模式: {pattern}")
                    return account
                    
        # 5. 尝试提取文本中的所有数字序列
        numbers = re.findall(r'\d+', text)
        for number in numbers:
            if 16 <= len(number) <= 19:
                print(f"从数字序列中提取到账号: {number}")
                return number
                    
        print("未能提取到账号")
        return None
