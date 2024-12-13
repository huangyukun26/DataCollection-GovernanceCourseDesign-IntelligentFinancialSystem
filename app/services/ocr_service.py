from paddleocr import PaddleOCR
import os
from typing import Dict, List, Optional
import numpy as np
from PIL import Image
import io
import logging
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="ch",
            show_log=True,
            use_gpu=False,
            enable_mkldnn=True
        )
        
    async def process_invoice(self, image_bytes: bytes) -> Dict:
        """处理发票图片并提取信息"""
        try:
            # 将字节流转换为PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # 转换为numpy数组
            if image.mode != 'RGB':
                image = image.convert('RGB')
            img_array = np.array(image)
            
            # OCR识别
            logger.info("开始OCR识别...")
            result = self.ocr.ocr(img_array, cls=True)
            
            # 打印原始识别结果
            logger.info("OCR原始识别结果:")
            for idx, line in enumerate(result[0]):
                logger.info(f"第{idx+1}行: 位置={line[0]}, 文本='{line[1][0]}', 置信度={line[1][1]}")
            
            # 提取发票信息
            invoice_info = self._extract_invoice_info(result)
            logger.info(f"提取的发票信息: {invoice_info}")
            
            return {
                "status": "success",
                "data": invoice_info
            }
            
        except Exception as e:
            logger.error(f"OCR处理错误: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _extract_invoice_info(self, ocr_result: List) -> Dict:
        """从OCR结果中提取发票信息"""
        invoice_info = {
            "invoice_code": "",      # 发票代码
            "invoice_number": "",    # 发票号码
            "invoice_date": "",      # 开票日期
            "total_amount": "",      # 金额（不含税）
            "tax_amount": "",        # 税额
            "seller": "",           # 销售方
            "buyer": "",            # 购买方
            "items": []             # 商品明细
        }
        
        try:
            if not ocr_result or not ocr_result[0]:
                logger.warning("OCR结果为空")
                return invoice_info

            # 将所有识别出的文本转换为列表，保留位置信息
            texts_with_pos = [(line[1][0].strip(), line[1][1], line[0]) for line in ocr_result[0]]
            logger.info(f"识别出的所有文本: {texts_with_pos}")

            # 存储所有可能的数字值
            numbers = []
            for text, confidence, pos in texts_with_pos:
                # 提取数字（包括小数点）
                matches = re.finditer(r'(\d+\.\d{2})', text)
                for match in matches:
                    number = float(match.group(1))
                    numbers.append((number, text, pos))
                    logger.info(f"找到数字: {number}, 在文本: {text}")

            # 遍历所有文本进行信息提取
            for text, confidence, pos in texts_with_pos:
                # 发票代码
                if text.startswith("4400") and len(text) >= 10:
                    invoice_info["invoice_code"] = text
                    logger.info(f"找到发票代码: {text}")
                
                # 发票号码
                elif text.startswith("No") or text.startswith("№"):
                    next_idx = texts_with_pos.index((text, confidence, pos)) + 1
                    if next_idx < len(texts_with_pos):
                        invoice_info["invoice_number"] = texts_with_pos[next_idx][0]
                        logger.info(f"找到发票号码: {texts_with_pos[next_idx][0]}")
                
                # 开票日期
                elif "年" in text and "月" in text and "日" in text:
                    invoice_info["invoice_date"] = text
                    logger.info(f"找到开票日期: {text}")
                elif "2020" in text:
                    invoice_info["invoice_date"] = text
                    logger.info(f"找到开票日期: {text}")
                
                # 销售方
                elif any(keyword in text for keyword in ["销售方", "名称", "*"]):
                    seller = text.split("：")[-1] if "：" in text else text.split(":")[-1] if ":" in text else text
                    if seller and len(seller) > 2:
                        invoice_info["seller"] = seller.strip()
                        logger.info(f"找到销售方: {seller}")
                
                # 购买方
                elif "购买方" in text:
                    buyer = text.split("：")[-1] if "：" in text else text.split(":")[-1] if ":" in text else text
                    if buyer and len(buyer) > 2:
                        invoice_info["buyer"] = buyer.strip()
                        logger.info(f"找到购买方: {buyer}")

            # 处理金额和税额
            # 按数值大小排序
            numbers.sort(key=lambda x: x[0])
            logger.info(f"排序后的所有数字: {numbers}")

            if len(numbers) >= 3:
                # 找到最大的数（通常是价税合计）
                total_with_tax = numbers[-1][0]
                logger.info(f"找到最大数（价税合计）: {total_with_tax}")

                # 在剩余的数字中找金额和税额
                for i in range(len(numbers)-1):
                    amount = numbers[i][0]
                    tax = numbers[i+1][0]
                    if abs(amount + tax - total_with_tax) < 0.1:  # 允许0.1的误差
                        # 金额通常大于税额
                        if amount > tax:
                            invoice_info["total_amount"] = f"{amount:.2f}"
                            invoice_info["tax_amount"] = f"{tax:.2f}"
                        else:
                            invoice_info["total_amount"] = f"{tax:.2f}"
                            invoice_info["tax_amount"] = f"{amount:.2f}"
                        logger.info(f"找到金额: {invoice_info['total_amount']} 和税额: {invoice_info['tax_amount']}")
                        break

        except Exception as e:
            logger.error(f"提取发票信息时出错: {str(e)}")
            logger.exception(e)
            
        return invoice_info