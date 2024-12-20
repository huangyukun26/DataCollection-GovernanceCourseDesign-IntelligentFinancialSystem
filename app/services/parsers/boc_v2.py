from typing import Dict, Any, List
from datetime import datetime
import re

from .boc_base import BOCBaseParser

class BOCV2Parser(BOCBaseParser):
    """交通银行版式2解析器"""
    
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
        
        # 处理表格主体
        row_cells = {}
        header_rows = set()  # 记录表头行
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
                    
                    # 标记表头行
                    if any(header in cell_text for header in ["Serial", "Trans Date", "Trading Type", "Dc Flg", "Trans Amt", "Balance"]):
                        header_rows.add(row_idx)
                    
        # 处理每一行
        for row_idx in sorted(row_cells.keys()):
            # 跳过表头行
            if row_idx in header_rows:
                print(f"跳过表头行 {row_idx}")
                continue
                
            transaction = statement_data.copy()
            print(f"\n处理第{row_idx}行:")
            
            # 提取所有单元格文本
            cell_texts = row_cells[row_idx]
            print("  单元格文本:", cell_texts)
            
            try:
                # 1. 处理交易日期和时间（第1、2列）
                if 1 in cell_texts:
                    transaction["transaction_date"] = self._convert_date(cell_texts[1])
                    if not transaction["transaction_date"]:
                        print(f"  日期转换失败: {cell_texts[1]}")
                        continue
                
                # 2. 处理交易类型（第3列）作为描述的一部分
                trading_type = None
                if 3 in cell_texts:
                    trading_type = cell_texts[3].strip()
                    transaction["description"] = trading_type
                
                # 3. 处理借贷标志和金额（第4、5列）
                if 4 in cell_texts and 5 in cell_texts:
                    dc_flag = cell_texts[4].strip()
                    amount = self._convert_amount(cell_texts[5])
                    
                    if amount is not None:
                        transaction["amount"] = amount
                        # 根据借贷标志判断交易类型
                        if dc_flag in ["Cr", "贷"]:
                            transaction["transaction_type"] = "收入"
                        elif dc_flag in ["Dr", "借"]:
                            transaction["transaction_type"] = "支出"
                        else:
                            # 尝试从交易类型判断
                            for type_name, keywords in self.transaction_type_keywords.items():
                                if trading_type and any(keyword in trading_type for keyword in keywords):
                                    transaction["transaction_type"] = type_name
                                    break
                            if not transaction["transaction_type"]:
                                transaction["transaction_type"] = "其他"
                
                # 4. 处理余额（第6列）
                if 6 in cell_texts:
                    balance = self._convert_amount(cell_texts[6])
                    if balance is not None:
                        transaction["balance"] = balance
                
                # 5. 处理对手方信息（第7、8列）
                counterparty_parts = []
                if 7 in cell_texts:  # Payment Receipt Account
                    account = cell_texts[7].strip()
                    if account:
                        counterparty_parts.append(account)
                if 8 in cell_texts:  # Payment Receipt Account Name
                    name = cell_texts[8].strip()
                    if name:
                        counterparty_parts.append(name)
                if counterparty_parts:
                    transaction["counterparty"] = " - ".join(counterparty_parts)
                
                # 6. 处理交易地点和摘要（第9、11列）
                description_parts = []
                if trading_type:
                    description_parts.append(trading_type)
                if 9 in cell_texts:  # Trading Place
                    place = cell_texts[9].strip()
                    if place:
                        description_parts.append(place)
                if 11 in cell_texts:  # Abstract
                    abstract = cell_texts[11].strip()
                    if abstract:
                        description_parts.append(abstract)
                if description_parts:
                    transaction["description"] = " - ".join(description_parts)
                
                # 7. 处理流水号（第10列）
                if 10 in cell_texts:  # Acounting Fluid Number
                    fluid_number = cell_texts[10].strip()
                    if fluid_number:
                        transaction["transaction_id"] = fluid_number
                
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