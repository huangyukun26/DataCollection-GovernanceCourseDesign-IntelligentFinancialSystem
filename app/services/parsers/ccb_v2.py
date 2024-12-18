from typing import Dict, Any, List
from datetime import datetime
import re

from .ccb_base import CCBBaseParser

class CCBV2Parser(CCBBaseParser):
    """建设银行版式2解析器"""
    
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
        account_number = None
        if "header" in raw_data and isinstance(raw_data["header"], list):
            header_texts = []
            for item in raw_data["header"]:
                if isinstance(item, dict) and "words" in item:
                    header_texts.append(item["words"])
            
            print("表头文本:", header_texts)
            
            # 尝试从表头中提取账号
            for text in header_texts:
                # 查找账号
                account_matches = [
                    r'账号[：:]\s*(\d+)',
                    r'账户[：:]\s*(\d+)',
                    r'卡号[：:]\s*(\d+)',
                    r'(\d{19})'  # 建设银行账号一般为19位
                ]
                for pattern in account_matches:
                    match = re.search(pattern, text)
                    if match:
                        account_number = match.group(1)
                        statement_data["account_number"] = account_number
                        break
                if account_number:
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
                if row_idx == 0 or any(header in str(cell_texts.get(0, "")) for header in ["日期", "凭证种类", "凭证号码"]):
                    print("  跳过表头行")
                    continue
                
                # 1. 处理交易日期（第0列）
                if 0 in cell_texts:
                    transaction["transaction_date"] = self._convert_date(cell_texts[0])
                
                # 2. 处理借贷金额（第6、7列）
                debit_amount = 0.0  # 借方金额（支出）
                credit_amount = 0.0  # 贷方金额（收入）
                
                # 借方金额
                if 6 in cell_texts and cell_texts[6].strip():
                    debit_amount = self._convert_amount(cell_texts[6])
                
                # 贷方金额
                if 7 in cell_texts and cell_texts[7].strip():
                    credit_amount = self._convert_amount(cell_texts[7])
                
                # 设置交易类型和金额
                if credit_amount > 0:
                    transaction["transaction_type"] = "收入"
                    transaction["amount"] = credit_amount
                elif debit_amount > 0:
                    transaction["transaction_type"] = "支出"
                    transaction["amount"] = debit_amount
                
                # 3. 处理余额（第8列）
                if 8 in cell_texts:
                    transaction["balance"] = self._convert_amount(cell_texts[8])
                
                # 4. 处理摘要（第3列）
                if 3 in cell_texts:
                    transaction["description"] = cell_texts[3].strip()
                
                # 5. 处理对方户名（第4列）
                if 4 in cell_texts:
                    transaction["counterparty"] = cell_texts[4].strip()
                
                # 设置账号
                if account_number:
                    transaction["account_number"] = account_number
                
                print("  处理后的交易数据:", transaction)
                # 只要有日期和金额就认为是有效记录
                if transaction["transaction_date"] is not None and (debit_amount > 0 or credit_amount > 0):
                    transactions.append(transaction)
                    
            except Exception as e:
                print(f"  处理行数据失败: {str(e)}")
        
        if not transactions:
            raise Exception("未能提取到有效的交易记录")
            
        print(f"成功提取到{len(transactions)}条交易记录")
        return transactions
