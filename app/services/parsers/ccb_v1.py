from typing import Dict, Any, List
from datetime import datetime
import re

from .ccb_base import CCBBaseParser

class CCBV1Parser(CCBBaseParser):
    """建设银行版式1解析器"""
    
    def __init__(self):
        super().__init__()
        # 交易类型关键词映射
        self.transaction_type_keywords = {
            "收入": ["贷记", "存入", "转入", "收到", "退款", "利息"],
            "支出": ["借记", "支取", "转出", "支付", "手续费", "年费"],
            "转账": ["转账", "汇款", "代付", "代发"],
            "其他": ["冲正", "撤销", "退回"]
        }
    
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
                    if any(header in cell_text for header in ["日期", "凭证种类", "凭证号码", "借方", "贷方"]):
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
                # 1. 处理交易日期（第0列）
                if 0 in cell_texts:
                    transaction["transaction_date"] = self._convert_date(cell_texts[0])
                    if not transaction["transaction_date"]:
                        print(f"  日期转换失败: {cell_texts[0]}")
                        continue
                
                # 2. 处理凭证号码（第2列）
                if 2 in cell_texts:
                    transaction["transaction_id"] = cell_texts[2].strip() or None
                
                # 3. 处理摘要（第3列）
                transaction_type = None
                if 3 in cell_texts:
                    description = cell_texts[3].strip()
                    description = re.sub(r'\s+', ' ', description)  # 合并多个空格
                    description = description.rstrip(',')  # 移除末尾逗号
                    transaction["description"] = description
                    
                    # 根据摘要判断交易类型
                    for type_name, keywords in self.transaction_type_keywords.items():
                        if any(keyword in description for keyword in keywords):
                            transaction_type = type_name
                            break
                
                # 4. 处理对手方（第4列）
                if 4 in cell_texts:
                    counterparty = cell_texts[4].strip()
                    if counterparty:  # 只在非空时设置
                        transaction["counterparty"] = counterparty
                
                # 5. 处理借贷金额（第5、6列）
                debit_amount = 0.0  # 借方金额（支出）
                credit_amount = 0.0  # 贷方金额（收入）
                
                # 借方金额（第5列）
                if 5 in cell_texts and cell_texts[5].strip():
                    debit_amount = self._convert_amount(cell_texts[5])
                
                # 贷方金额（第6列）
                if 6 in cell_texts and cell_texts[6].strip():
                    credit_amount = self._convert_amount(cell_texts[6])
                
                # 6. 设置交易类型和金额
                if debit_amount > 0:
                    transaction["transaction_type"] = transaction_type or "支出"
                    transaction["amount"] = debit_amount
                elif credit_amount > 0:
                    transaction["transaction_type"] = transaction_type or "收入"
                    transaction["amount"] = credit_amount
                else:
                    # 处理金额为0的情况
                    transaction["amount"] = 0.0
                    transaction["transaction_type"] = transaction_type or "其他"
                
                # 7. 处理余额（第9列）
                if 9 in cell_texts:
                    balance = self._convert_amount(cell_texts[9])
                    if balance is not None:
                        transaction["balance"] = balance
                
                # 8. 处理交易流水号（第10列）
                if 10 in cell_texts:
                    flow_no = cell_texts[10].strip()
                    if flow_no:  # 只在非空时设置
                        transaction["transaction_id"] = flow_no
                
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
