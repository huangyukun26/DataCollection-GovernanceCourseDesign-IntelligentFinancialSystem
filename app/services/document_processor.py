from typing import Dict, Any
import os
from app.services.ocr.service import OCRService
from app.services.preprocessing.image import ImagePreprocessor
import cv2
import re
from datetime import datetime

class DocumentProcessor:
    def __init__(self):
        self.ocr_service = OCRService()
        self.image_preprocessor = ImagePreprocessor()

    async def process_document(self, file_path: str, doc_type: str) -> Dict[str, Any]:
        try:
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"Invalid file path: {file_path}")

            # 读取图像
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError(f"Failed to read image: {file_path}")
            
            # 图像预处理
            enhanced_image = await self.image_preprocessor.enhance_image(image)
            deskewed_image, angle = await self.image_preprocessor.deskew(enhanced_image)
            
            # 生成处理后的图像路径
            processed_path = os.path.join(
                os.path.dirname(file_path),
                f"{os.path.splitext(os.path.basename(file_path))[0]}_processed.jpg"
            )
            
            # 保存处理后的图像
            cv2.imwrite(processed_path, deskewed_image)
            
            # OCR识别
            text = await self.ocr_service.recognize(processed_path)
            
            # 根据文档类型进行特定处理
            extracted_data = await self._extract_data_by_type(text, doc_type)
            
            return {
                "status": "success",
                "ocr_text": text,
                "extracted_data": extracted_data,
                "processed_file": processed_path,
                "rotation_angle": angle
            }
            
        except Exception as e:
            print(f"Document processing error: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _extract_data_by_type(self, text: str, doc_type: str) -> Dict[str, Any]:
        if doc_type == "contract":
            return await self._extract_contract_data(text)
        elif doc_type == "invoice":
            return await self._extract_invoice_data(text)
        elif doc_type == "bank_statement":
            return await self._extract_bank_statement_data(text)
        else:
            return {}
    
    @staticmethod
    async def _extract_contract_data(text: str) -> Dict[str, Any]:
        data = {
            "contract_number": "",
            "party_a": "",
            "party_b": "",
            "amount": 0.0,
            "sign_date": None
        }
        
        # 合同编号匹配
        contract_number = re.search(r'合同编号[：:]\s*([A-Za-z0-9-]+)', text)
        if contract_number:
            data["contract_number"] = contract_number.group(1)
        
        # 甲方匹配
        party_a = re.search(r'甲方[：:]\s*(.+?)(?=\n|乙方)', text)
        if party_a:
            data["party_a"] = party_a.group(1).strip()
        
        # 乙方匹配
        party_b = re.search(r'乙方[：:]\s*(.+?)(?=\n|第)', text)
        if party_b:
            data["party_b"] = party_b.group(1).strip()
        
        # 金额匹配
        amount = re.search(r'金额[：:]\s*(?:人民币)?(\d+(?:\.\d{2})?)', text)
        if amount:
            data["amount"] = float(amount.group(1))
        
        # 日期匹配
        date = re.search(r'签订日期[：:]\s*(\d{4})[年-](\d{1,2})[月-](\d{1,2})', text)
        if date:
            data["sign_date"] = datetime(
                int(date.group(1)),
                int(date.group(2)),
                int(date.group(3))
            ).date()
        
        return data
    
    @staticmethod
    async def _extract_invoice_data(text: str) -> Dict[str, Any]:
        print("\nStarting invoice data extraction")
        print(f"Input text:\n{text}")
        
        data = {
            "invoice_number": "",
            "invoice_date": None,
            "amount": 0.0,
            "tax_amount": 0.0,
            "seller": "",
            "buyer": ""
        }
        
        # 发票号码匹配
        invoice_number = re.search(r'发票号码[：:]\s*(\d+)', text)
        if invoice_number:
            data["invoice_number"] = invoice_number.group(1)
            print(f"Found invoice number: {data['invoice_number']}")
        else:
            print("Invoice number not found")
        
        # 开票日期匹配
        date = re.search(r'开票日期[：:]\s*(\d{4})[年-](\d{1,2})[月-](\d{1,2})', text)
        if date:
            data["invoice_date"] = datetime(
                int(date.group(1)),
                int(date.group(2)),
                int(date.group(3))
            ).date()
            print(f"Found invoice date: {data['invoice_date']}")
        else:
            print("Invoice date not found")
        
        # 金额匹配 - 支持更多格式
        amount = re.search(r'金额[：:]\s*[¥￥]?\s*(\d+(?:[,.]\d{2})?)', text)
        if amount:
            data["amount"] = float(amount.group(1).replace(',', ''))
            print(f"Found amount: {data['amount']}")
        else:
            print("Amount not found")
        
        # 税额匹配 - 支持更多格式
        tax = re.search(r'税额[：:]\s*[¥￥]?\s*(\d+(?:[,.]\d{2})?)', text)
        if tax:
            data["tax_amount"] = float(tax.group(1).replace(',', ''))
            print(f"Found tax amount: {data['tax_amount']}")
        else:
            print("Tax amount not found")
        
        # 销售方匹配 - 更宽松的匹配
        seller = re.search(r'销售方[：:名称]*[：:]\s*(.+?)(?=\n|地址|$)', text)
        if seller:
            data["seller"] = seller.group(1).strip()
            print(f"Found seller: {data['seller']}")
        else:
            print("Seller not found")
        
        # 购买方匹配 - 更宽松的匹配
        buyer = re.search(r'购买方[：:名称]*[：:]\s*(.+?)(?=\n|地址|$)', text)
        if buyer:
            data["buyer"] = buyer.group(1).strip()
            print(f"Found buyer: {data['buyer']}")
        else:
            print("Buyer not found")
        
        print("\nExtracted data:", data)
        return data
    
    @staticmethod
    async def _extract_bank_statement_data(text: str) -> Dict[str, Any]:
        data = {
            "account": "",
            "period": "",
            "transactions": []
        }
        
        # 账号匹配
        account = re.search(r'账号[：:]\s*(\d+)', text)
        if account:
            data["account"] = account.group(1)
        
        # 交易记录匹配
        transactions = re.finditer(
            r'(\d{4}-\d{2}-\d{2})\s+([+-]?\d+(?:\.\d{2})?)\s+([+-]?\d+(?:\.\d{2})?)\s+(.+?)(?=\n\d|$)',
            text
        )
        
        for trans in transactions:
            data["transactions"].append({
                "date": trans.group(1),
                "amount": float(trans.group(2)),
                "balance": float(trans.group(3)),
                "description": trans.group(4).strip()
            })
        
        return data 