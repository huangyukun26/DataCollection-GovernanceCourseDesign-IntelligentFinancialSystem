from typing import Dict, Any, List
from datetime import datetime
import re

from .boc_base import BOCBaseParser

class BOCV1Parser(BOCBaseParser):
    """交通银行版式1解析器"""
    
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
            "description": None,
            "transaction_id": None
        }
        
        # 获取账号（从raw_data中获取）
        account_number = raw_data.get("account_number")
        if account_number:
            print(f"从raw_data获取到账号: {account_number}")
            statement_data["account_number"] = account_number
        else:
            # 尝试从表格内容中提取账号
            if "body" in raw_data:
                for cell in raw_data["body"]:
                    if isinstance(cell, dict) and "words" in cell:
                        text = cell["words"]
                        # 匹配账号格式
                        account_match = re.search(r'Account No\.|账号.*?[:：]\s*(\d{16,19})', text)
                        if account_match:
                            statement_data["account_number"] = account_match.group(1)
                            print(f"从表格内容提取到账号: {account_match.group(1)}")
                            break
        
        # 处理表格主体
        row_cells = {}
        data_header_row = None  # 记录交易数据表头行
        header_keywords = ["序号", "交易日期", "交易地点", "交易方式", "收支标志", "交易金额", "余额"]
        
        if "body" in raw_data:
            for cell in raw_data["body"]:
                if isinstance(cell, dict) and "row_start" in cell and "words" in cell:
                    row_idx = cell.get("row_start")
                    col_idx = cell.get("col_start", 0)
                    if row_idx not in row_cells:
                        row_cells[row_idx] = {}
                    # 清理单元格文本
                    cell_text = cell["words"].strip()
                    cell_text = re.sub(r'\s+', ' ', cell_text)  # 合并多个空格
                    row_cells[row_idx][col_idx] = cell_text
                    
                    # 标记交易数据表头行
                    if any(keyword in cell_text for keyword in header_keywords):
                        data_header_row = row_idx
                        print(f"找到交易数据表头行: {row_idx}, 关键字: {cell_text}")
        
        if data_header_row is None:
            raise Exception("未找到交易数据表头")
            
        # 处理每一行
        for row_idx in sorted(row_cells.keys()):
            # 跳过表头行及之前的行
            if row_idx <= data_header_row:
                print(f"跳过非数据行 {row_idx}")
                continue
                
            transaction = statement_data.copy()
            print(f"\n处理第{row_idx}行:")
            
            # 提取所有单元格文本
            cell_texts = row_cells[row_idx]
            print("  单元格文本:", cell_texts)
            
            try:
                # 0. 检查是否是结束行
                first_cell = str(cell_texts.get(0, ""))
                if any(end_text in first_cell for end_text in ["End Of Page", "打印时间", "币种", "付方/收方额汇总"]):
                    print(f"  跳过结束行: {first_cell}")
                    continue
                
                # 1. 处理序号和交易日期
                if 0 in cell_texts and cell_texts[0].isdigit():  # 确认是数据行
                    transaction["transaction_id"] = cell_texts[0]
                    
                    if 1 in cell_texts:
                        date_text = cell_texts[1]
                        # 处理可能的年月日格式
                        if len(date_text) == 8:  # 如 20200921
                            transaction["transaction_date"] = datetime.strptime(date_text, '%Y%m%d')
                        else:
                            transaction["transaction_date"] = self._convert_date(date_text)
                        
                        if not transaction["transaction_date"]:
                            print(f"  日期转换失败: {date_text}")
                            continue
                    
                    # 2. 处理交易地点（第2列）作为描述的一部分
                    location = cell_texts.get(2, "").strip()
                    
                    # 3. 处理交易方式（第3列）作为描述的一部分
                    trading_type = cell_texts.get(3, "").strip()
                    
                    # 合并交易地点和方式作为描述
                    description_parts = []
                    if trading_type:
                        description_parts.append(trading_type)
                    if location:
                        description_parts.append(location)
                    if description_parts:
                        transaction["description"] = " - ".join(description_parts)
                        # 如果是网上支付，将交易地点作为交易对手
                        if "网上支付" in location or "网上转账" in location:
                            transaction["counterparty"] = location
                    
                    # 4. 处理收支标志和金额（第4、5列）
                    dc_flag = cell_texts.get(4, "").strip()
                    amount_text = cell_texts.get(5, "")
                    amount = self._convert_amount(amount_text)
                    
                    if amount is not None:
                        transaction["amount"] = amount
                        # 根据收支标志判断交易类型
                        if dc_flag in ["收(Cr)", "Cr", "贷", "收"]:
                            transaction["transaction_type"] = "收入"
                        elif dc_flag in ["付(Dr)", "Dr", "借", "付"]:
                            transaction["transaction_type"] = "支出"
                            # 支出时金额取负值
                            transaction["amount"] = -amount
                        else:
                            # 尝试从交易方式判断类型
                            for type_name, keywords in self.transaction_type_keywords.items():
                                if trading_type and any(keyword in trading_type for keyword in keywords):
                                    transaction["transaction_type"] = type_name
                                    break
                            if not transaction["transaction_type"]:
                                transaction["transaction_type"] = "其他"
                    
                    # 5. 处理余额（第6列）
                    balance = self._convert_amount(cell_texts.get(6, ""))
                    if balance is not None:
                        transaction["balance"] = balance
                    
                    print("  处理后的交易数据:", transaction)
                    
                    # 验证必要字段
                    if (transaction["transaction_date"] is not None and 
                        transaction["amount"] is not None and
                        transaction["transaction_type"] is not None):
                        transactions.append(transaction)
                        
            except Exception as e:
                print(f"  处理行数据失败: {str(e)}")
                continue
        
        if not transactions:
            raise Exception("未能提取到有效的交易记录")
            
        print(f"成功提取到{len(transactions)}条交易记录")
        return transactions
    
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