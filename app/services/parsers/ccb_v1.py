from typing import Dict, Any, List
from datetime import datetime
import re

from .ccb_base import CCBBaseParser

class CCBV1Parser(CCBBaseParser):
    """建设银行版式1解析器"""
    
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
            for text in ' '.join(header_texts):
                # 先尝试直接匹配18-19位数字
                numbers = re.findall(r'\d{18,19}', text)
                if numbers:
                    account_number = numbers[0]
                    break
                    
                # 如果没找到，尝试其他模式
                patterns = [
                    r'账号[:：]?\s*(\d+)',
                    r'账[号户][:：]?\s*(\d+)',
                    r'账[号户]\s*[为是]?\s*(\d+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        account_number = match.group(1)
                        break
                if account_number:
                    break
                        
            if account_number:
                statement_data["account_number"] = account_number
                print(f"提取到账号: {account_number}")
            else:
                print("未能从表头提取到账号")
                
        # 处理表格主体
        row_cells = {}
        if "body" in raw_data:
            for cell in raw_data["body"]:
                if isinstance(cell, dict) and "row_start" in cell and "words" in cell:
                    row_idx = cell.get("row_start")
                    col_idx = cell.get("col_start", 0)
                    if row_idx not in row_cells:
                        row_cells[row_idx] = {}
                    row_cells[row_idx][col_idx] = cell["words"].strip()
                    
                    # 尝试从每个单元格中提取账号
                    if not account_number:
                        numbers = re.findall(r'\d{18,19}', cell["words"])
                        if numbers:
                            account_number = numbers[0]
                            statement_data["account_number"] = account_number
                            print(f"从单元格提取到账号: {account_number}")
                            
        # 处理每一行
        for row_idx in sorted(row_cells.keys()):
            transaction = statement_data.copy()
            print(f"\n处理第{row_idx}行:")
            
            # 提取所有单元格文本
            cell_texts = row_cells[row_idx]
            print("  单元格文本:", cell_texts)
            
            try:
                # 跳过表头行
                if row_idx == 0 or any(header in str(cell_texts.get(0, "")) for header in ["日期", "凭证种类", "凭证号码"]):
                    print("  跳过表头行")
                    continue
                
                # 1. 处理交易日期（第0列）
                if 0 in cell_texts:
                    transaction["transaction_date"] = self._convert_date(cell_texts[0])
                
                # 2. 处理借贷金额（第5、6列）
                debit_amount = 0.0  # 借方金额（支出）
                credit_amount = 0.0  # 贷方金额（收入）
                
                # 借方金额（第5列）
                if 5 in cell_texts and cell_texts[5].strip():
                    debit_amount = self._convert_amount(cell_texts[5])
                
                # 贷方金额（第6列）
                if 6 in cell_texts and cell_texts[6].strip():
                    credit_amount = self._convert_amount(cell_texts[6])
                
                # 设置交易类型和金额
                if debit_amount > 0:
                    transaction["transaction_type"] = "支出"
                    transaction["amount"] = debit_amount
                elif credit_amount > 0:
                    transaction["transaction_type"] = "收入"
                    transaction["amount"] = credit_amount
                
                # 3. 处理余额（第9列）
                if 9 in cell_texts:
                    transaction["balance"] = self._convert_amount(cell_texts[9])
                
                # 4. 处理摘要（第3列）和对方户名（第4列）
                description_parts = []
                if 3 in cell_texts and cell_texts[3].strip():
                    description_parts.append(cell_texts[3].strip().replace('\n', ''))
                transaction["description"] = ''.join(description_parts)
                
                if 4 in cell_texts:
                    transaction["counterparty"] = cell_texts[4].strip()
                
                # 设置账号
                if account_number:
                    transaction["account_number"] = account_number
                
                print("  处理后的交易数据:", transaction)
                # 只要有日期和金额就认为是有效记录
                if transaction["transaction_date"] is not None and transaction["amount"] is not None and transaction["amount"] > 0:
                    transactions.append(transaction)
                    
            except Exception as e:
                print(f"  处理行数据失败: {str(e)}")
        
        if not transactions:
            raise Exception("未能提取到有效的交易记录")
            
        print(f"成功提取到{len(transactions)}条交易记录")
        return transactions
