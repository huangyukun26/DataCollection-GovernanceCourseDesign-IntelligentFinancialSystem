from typing import Dict, Any, List
from datetime import datetime
import re

from .ceb_base import CEBBaseParser

class CEBV1Parser(CEBBaseParser):
    """光大银行版式1解析器"""
    
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
                # 查找主卡号
                card_matches = [
                    r'主卡号[：:]\s*(\d{16,19})',
                    r'卡\s*号[：:]\s*(\d{16,19})',
                    r'[主副]卡号[：:]\s*(\d{16,19})',
                    r'(\d{16})',  # 光大银行卡号固定16位
                ]
                for pattern in card_matches:
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
                if row_idx == 0 or any(header in str(cell_texts.get(0, "")) for header in ["卡号", "账号", "交易日期"]):
                    print("  跳过表头行")
                    continue
                
                # 1. 处理账号（第0列）
                if 0 in cell_texts:
                    card_match = re.search(r'(\d{16})', cell_texts[0])
                    if card_match:
                        transaction["account_number"] = card_match.group(1)
                    elif account_number:  # 如果当前行没有账号，使用表头提取的账号
                        transaction["account_number"] = account_number
                
                # 2. 处理交易日期（第1列）
                if 1 in cell_texts:
                    date_text = cell_texts[1]
                    date_text = re.sub(r'[^\d]', '', date_text)  # 只保留数字
                    try:
                        transaction["transaction_date"] = datetime.strptime(date_text, "%Y%m%d")
                    except:
                        print(f"  解析日期失败: {date_text}")
                
                # 3. 处理存入金额和支出金额（第3、4列）
                deposit_amount = 0.0
                withdraw_amount = 0.0
                
                # 存入金额列
                if 3 in cell_texts:
                    try:
                        amount_text = cell_texts[3].replace(',', '')
                        amount_text = re.sub(r'[^\d.]', '', amount_text)
                        if amount_text:
                            deposit_amount = float(amount_text)
                    except:
                        print(f"  解析存入金额失败: {cell_texts[3]}")
                
                # 支出金额列
                if 4 in cell_texts:
                    try:
                        amount_text = cell_texts[4].replace(',', '')
                        amount_text = re.sub(r'[^\d.]', '', amount_text)
                        if amount_text:
                            withdraw_amount = float(amount_text)
                    except:
                        print(f"  解析支出金额失败: {cell_texts[4]}")
                
                # 设置交易类型和金额
                if deposit_amount > 0:
                    transaction["transaction_type"] = "收入"
                    transaction["amount"] = deposit_amount
                elif withdraw_amount > 0:
                    transaction["transaction_type"] = "支出"
                    transaction["amount"] = withdraw_amount
                
                # 4. 处理账户余额（第5列）
                if 5 in cell_texts:
                    try:
                        balance_text = cell_texts[5].replace(',', '')
                        balance_text = re.sub(r'[^\d.]', '', balance_text)
                        if balance_text:
                            transaction["balance"] = float(balance_text)
                    except:
                        print(f"  解析余额失败: {cell_texts[5]}")
                
                # 5. 处理交易地点（第2列）和交易摘要（第6列）
                if 2 in cell_texts:
                    transaction["counterparty"] = cell_texts[2].strip()
                if 6 in cell_texts:
                    # 合并交易地点和摘要
                    desc_parts = []
                    if transaction["counterparty"]:
                        desc_parts.append(transaction["counterparty"])
                    if cell_texts[6].strip():
                        desc_parts.append(cell_texts[6].strip())
                    transaction["description"] = " ".join(desc_parts)
                
                print("  处理后的交易数据:", transaction)
                # 只要有日期和金额就认为是有效记录
                if transaction["transaction_date"] is not None and (deposit_amount > 0 or withdraw_amount > 0):
                    transactions.append(transaction)
                    
            except Exception as e:
                print(f"  处理行数据失败: {str(e)}")
        
        if not transactions:
            raise Exception("未能提取到有效的交易记录")
            
        print(f"成功提取到{len(transactions)}条交易记录")
        return transactions 