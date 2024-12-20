from typing import Dict, Any, List
from datetime import datetime
import re

from .ccb_base import CCBBaseParser

class CCBV2Parser(CCBBaseParser):
    """建设银行版式2解析器"""
    
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
                    if any(header in cell_text for header in ["日期", "凭证种类", "凭证号码", "借方", "贷方", "余额"]):
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
                    date_text = cell_texts[0].split()[0]  # 取空格前的日期部分
                    transaction["transaction_date"] = self._convert_date(date_text)
                    if not transaction["transaction_date"]:
                        print(f"  日期转换失败: {date_text}")
                        continue
                
                # 2. 处理凭证号码（第1列）
                if 1 in cell_texts:
                    transaction["transaction_id"] = cell_texts[1].strip() or None
                
                # 3. 处理摘要和凭证号（第2列）
                if 2 in cell_texts:
                    description = cell_texts[2].strip()
                    if description:
                        transaction["description"] = description
                
                # 4. 处理对手方（第3列）
                if 3 in cell_texts:
                    counterparty = cell_texts[3].strip()
                    if counterparty:  # 只在非空时设置
                        transaction["counterparty"] = counterparty
                
                # 5. 处理金额和交易类型（第4、5、6列）
                debit_amount = 0.0  # 借方金额（支出）
                credit_amount = 0.0  # 贷方金额（收入）
                
                # 借方金额（第4列）
                if 4 in cell_texts and cell_texts[4].strip():
                    debit_amount = self._convert_amount(cell_texts[4])
                
                # 贷方金额（第5列）
                if 5 in cell_texts and cell_texts[5].strip():
                    credit_amount = self._convert_amount(cell_texts[5])
                
                # 借贷标记（第6列）
                transaction_type = None
                if 6 in cell_texts:
                    debit_credit_flag = cell_texts[6].strip()
                    if debit_credit_flag == '借':
                        transaction_type = "支出"
                        transaction["amount"] = debit_amount
                    elif debit_credit_flag == '贷':
                        transaction_type = "收入"
                        transaction["amount"] = credit_amount
                
                if not transaction_type:
                    # 如果没有借贷标记，根据金额判断
                    if debit_amount > 0:
                        transaction_type = "支出"
                        transaction["amount"] = debit_amount
                    elif credit_amount > 0:
                        transaction_type = "收入"
                        transaction["amount"] = credit_amount
                    else:
                        transaction_type = "其他"
                        transaction["amount"] = 0.0
                
                transaction["transaction_type"] = transaction_type
                
                # 6. 处理余额（第7列）
                if 7 in cell_texts:
                    balance_text = cell_texts[7].strip()
                    # 如果包含多个数字，取最后一个
                    balance_parts = re.findall(r'[\d,]+\.?\d*', balance_text)
                    if balance_parts:
                        balance = self._convert_amount(balance_parts[-1])
                        if balance is not None:
                            transaction["balance"] = balance
                
                # 7. 处理交易流水号（第8列）
                if 8 in cell_texts:
                    flow_no = cell_texts[8].strip()
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
