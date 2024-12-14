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
            
            # 存储所有可能的数字值和税率
            numbers = []
            tax_rates = []
            items_started = False
            found_seller = False
            found_buyer = False
            current_item = None
            
            # 定义需要排除的关键词
            exclude_keywords = {
                '地址', '电话', '开户', '账号', '行号', '纳税人', '识别号', 
                '规格', '型号', '合计', '小计', '税额', '价税',
                '传真', '邮编', '名称', '代码', '日期', '号码',
                '备注', '复核', '收款人', '开票人'
            }
            
            # 定义商品区域的开始标记
            item_start_keywords = {'货物名称', '项目名称', '服务名称', '商品名称', '*', '单位'}
            
            # 定义商品区域的结束标记
            item_end_keywords = {'合计', '小计', '价税合计', '税额', '金额', '价税', '复核', '收款人'}

            # 获取发票的大致区域范围
            y_coordinates = [pos[0][1] for text, conf, pos in texts_with_pos]
            min_y = min(y_coordinates)
            max_y = max(y_coordinates)
            mid_y = (min_y + max_y) / 2

            # 销售方/购买方识别优化
            buyer_section_y = None
            seller_section_y = None
            
            # 第一遍：寻找标记位置
            for text, confidence, pos in texts_with_pos:
                text = text.strip()
                text_y = pos[0][1]
                
                # 寻找购买方和销售方的标记位置
                if "名称" in text or "方" in text:
                    if any(keyword in text for keyword in ["购买方", "购方", "购"]):
                        buyer_section_y = text_y
                        logger.info(f"找到购买方标记位置: {text_y}")
                    elif any(keyword in text for keyword in ["销售方", "销"]):
                        seller_section_y = text_y
                        logger.info(f"找到销售方标记位置: {text_y}")

            # 第二遍：根据标记位置识别公司名称
            for text, confidence, pos in texts_with_pos:
                text = text.strip()
                text_y = pos[0][1]
                
                if len(text.strip()) > 4 and any(keyword in text for keyword in ["公司", "有限", "企业", "厂"]):
                    if not any(keyword in text for keyword in ["识别号", "地址", "电话", "开户", "账号"]):
                        # 根据与标记位置的距离判断
                        if buyer_section_y and abs(text_y - buyer_section_y) < 50 and not invoice_info["buyer"]:
                            invoice_info["buyer"] = text.strip()
                            logger.info(f"根据位置找到购买方: {text}")
                        elif seller_section_y and abs(text_y - seller_section_y) < 50 and not invoice_info["seller"]:
                            invoice_info["seller"] = text.strip()
                            logger.info(f"根据位置找到销售方: {text}")

            # 如果还没找到，使用上下半部分判断
            if not invoice_info["seller"] or not invoice_info["buyer"]:
                for text, confidence, pos in texts_with_pos:
                    text = text.strip()
                    text_y = pos[0][1]
                    
                    if len(text.strip()) > 4 and any(keyword in text for keyword in ["公司", "有限", "企业", "厂"]):
                        if not any(keyword in text for keyword in ["识别号", "地址", "电话", "开户", "账号"]):
                            if text_y < mid_y and not invoice_info["buyer"]:
                                invoice_info["buyer"] = text.strip()
                                logger.info(f"根据位置找到购买方: {text}")
                            elif text_y > mid_y and not invoice_info["seller"]:
                                invoice_info["seller"] = text.strip()
                                logger.info(f"根据位置找到销售方: {text}")

            # 第一遍扫描: 提取数字、金额和税率
            for text, confidence, pos in texts_with_pos:
                # 清理文本
                text = text.replace('¥', '').replace('￥', '').replace(',', '')
                
                # 提取税率
                tax_rate_match = re.search(r'(\d{1,2})%', text)
                if tax_rate_match:
                    try:
                        rate = float(tax_rate_match.group(1))
                        if 0 < rate < 100:
                            tax_rates.append(rate)
                            logger.info(f"找到税率: {rate}%")
                    except ValueError:
                        continue
                
                # 提取金额（放宽位置限制）
                # 1. 处理科学计数法格式
                sci_matches = re.finditer(r'(\d+\.?\d*)[Ee][-+]?\d+', text)
                for match in sci_matches:
                    try:
                        number = float(match.group())
                        if number > 1.0:
                            numbers.append((number, text, pos))
                            logger.info(f"找到科学计数法数字: {number}")
                    except ValueError:
                        continue
                
                # 2. 处理普通数字格式
                matches = re.finditer(r'(\d+\.\d{2})', text)
                for match in matches:
                    try:
                        number = float(match.group(1))
                        if number > 1.0:
                            numbers.append((number, text, pos))
                            logger.info(f"找到数字: {number}")
                    except ValueError:
                        continue

            # 金额识别优化（移到最前面处理）
            amount_lines = set()  # 记录包含金额的行的y坐标
            
            # 先找到所有可能的金额行
            for text, confidence, pos in texts_with_pos:
                if "¥" in text or "￥" in text:
                    amount_lines.add(pos[0][1])
                    logger.info(f"找到金额行: {text} at y={pos[0][1]}")
                elif any(keyword in text for keyword in ["金额", "税额", "合计", "小计"]):
                    amount_lines.add(pos[0][1])
                    logger.info(f"找到金额相关行: {text} at y={pos[0][1]}")

            # 处理金额
            if numbers:
                # 收集所有金额行的数字
                amount_numbers = []
                for num, text, pos in numbers:
                    # 检查是否在金额行
                    if any(abs(pos[0][1] - amount_y) < 15 for amount_y in amount_lines):
                        amount_numbers.append((num, pos))
                        logger.info(f"找到金额行数字: {num}")
                
                if amount_numbers:
                    # 按数值大小排序
                    amount_numbers.sort(key=lambda x: x[0])
                    # 找到最大的两个数
                    if len(amount_numbers) >= 2:
                        amount = amount_numbers[-2][0]
                        tax = amount_numbers[-1][0]
                        # 验证税率是否合理（5%-17%）
                        if 0.05 <= tax/amount <= 0.17:
                            invoice_info["total_amount"] = f"{amount:.2f}"
                            invoice_info["tax_amount"] = f"{tax:.2f}"
                            logger.info(f"识别到金额: {amount} 和税额: {tax}")

            # 商品明细处理优化
            items_started = False
            current_item = None
            
            # 更新商品区域标记关键词
            item_start_keywords = {'货物名称', '项目名称', '服务名称', '商品名称', '规格型号'}
            item_end_keywords = {'合计', '小计', '价税合计', '税额', '金额', '价税', '复核', '收款人', '备注'}
            
            # 更新无效字符和关键词
            invalid_chars = {'/', '[', ']', '¥', '￥', '*', '+', ':', '：', '(', ')', '（', '）'}
            invalid_keywords = {
                '发票', '联', '东港', '安', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖', '拾',
                '佰', '仟', '万', '亿', '圆', '整', '金额', '税额', '价税', '合计', '小计', '规格',
                '型号', '单位', '数量', '单价', '金额', '税率', '税额', '价税合计', '大写', '小写',
                '公司', '有限', '名称', '纳税人', '识别号', '地址', '电话', '开户', '账号'
            }

            # 商品明细提取
            for idx, (text, confidence, pos) in enumerate(texts_with_pos):
                text = text.strip()
                text_y = pos[0][1]
                
                # 跳过金额行
                if any(abs(text_y - amount_y) < 15 for amount_y in amount_lines):
                    continue
                
                # 跳过无效内容
                if (len(text) < 3 or
                    any(char in text for char in invalid_chars) or
                    any(keyword in text for keyword in invalid_keywords)):
                    continue
                
                # 商品区域识别
                if any(keyword in text for keyword in item_start_keywords):
                    items_started = True
                    continue
                
                if items_started and any(keyword in text for keyword in item_end_keywords):
                    items_started = False
                    continue
                
                # 商品信息提取
                if items_started and len(text.strip()) > 2:
                    item_info = self._extract_item_info(text, texts_with_pos, idx)
                    if item_info and item_info.get("item_name"):
                        # 额外的有效性检查
                        item_name = item_info["item_name"]
                        if (len(item_name) > 2 and 
                            not any(char in item_name for char in invalid_chars) and
                            not any(keyword in item_name for keyword in invalid_keywords)):
                            invoice_info["items"].append(item_info)

            # 第二遍扫描: 处理其他信息
            for idx, (text, confidence, pos) in enumerate(texts_with_pos):
                text = text.strip()
                
                # 发票代码（支持不同格式）
                if not invoice_info["invoice_code"]:
                    code_match = re.search(r'(\d{10,12})', text)
                    if code_match:
                        code = code_match.group(1)
                        if code.startswith('4400') or code.startswith('4200'):
                            invoice_info["invoice_code"] = code
                            logger.info(f"找到发票代码: {code}")
                
                # 发票号码（支持不同格式）
                if not invoice_info["invoice_number"]:
                    # 1. 直接匹配8位数字
                    num_match = re.search(r'(?<!\d)(\d{8})(?!\d)', text)
                    if num_match:
                        invoice_info["invoice_number"] = num_match.group(1)
                        logger.info(f"找到发票号码: {num_match.group(1)}")
                    # 2. 处理带No的情况
                    elif 'No' in text or '№' in text:
                        num_match = re.search(r'[No№]\s*(\d{8})', text)
                        if num_match:
                            invoice_info["invoice_number"] = num_match.group(1)
                            logger.info(f"找到发票号码: {num_match.group(1)}")
                
                # 开票日期（支持多种格式）
                if not invoice_info["invoice_date"]:
                    # 1. 标准格式：2020年06月27日
                    date_match = re.search(r'20\d{2}年\d{1,2}月\d{1,2}日', text)
                    if date_match:
                        invoice_info["invoice_date"] = date_match.group()
                        logger.info(f"找到开票日期: {date_match.group()}")
                    # 2. 其他格式：2020-06-27等
                    else:
                        date_match = re.search(r'20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}', text)
                        if date_match:
                            date_str = date_match.group()
                            # 统一转换为标准格式
                            date_str = re.sub(r'[-/.]', lambda x: '年' if x.start() == 4 else '月' if x.start() > 4 else x.group(), date_str)
                            if not date_str.endswith('日'):
                                date_str += '日'
                            invoice_info["invoice_date"] = date_str
                            logger.info(f"找到开票日期: {date_str}")
                
                # 商品明细区域识别优化
                if any(keyword in text for keyword in item_start_keywords):
                    items_started = True
                    continue
                
                if items_started and any(keyword in text for keyword in item_end_keywords):
                    items_started = False
                    continue
                
                # 商品明细提取优化
                if items_started and len(text.strip()) > 2:
                    # 清理文本
                    text = text.strip('*: ：')
                    
                    # 排除不需要的行
                    if (any(keyword in text for keyword in exclude_keywords) or
                        re.match(r'^[\d.,]+$', text) or  # 纯数字
                        re.match(r'^[*\s]+$', text) or   # 纯符号
                        len(text) < 3):                  # 过短的文本
                        continue
                    
                    # 提取商品信息
                    item_info = self._extract_item_info(text, texts_with_pos, idx)
                    if item_info:
                        invoice_info["items"].append(item_info)
                        continue

            # 金额识别优化
            if numbers:
                # 先查找带¥符号的数字
                amounts_with_symbol = []
                for num, text, pos in numbers:
                    # 检查原始文本中是否包含¥符号
                    original_text = next((t[0] for t in texts_with_pos if abs(t[2][0][1] - pos[0][1]) < 10), "")
                    if "¥" in original_text:
                        amounts_with_symbol.append((num, text, pos))
                        logger.info(f"找到带¥符号的金额: {num}")

                # 如果找到了带¥符号的数字，优先使用它们
                if len(amounts_with_symbol) >= 2:
                    # 按数值大小排序
                    amounts_with_symbol.sort(key=lambda x: x[0])
                    # 取最大的两个数
                    amount = amounts_with_symbol[-2][0]
                    tax = amounts_with_symbol[-1][0]
                    if 0.05 <= tax/amount <= 0.17:  # 验证税率是否合理
                        invoice_info["total_amount"] = f"{amount:.2f}"
                        invoice_info["tax_amount"] = f"{tax:.2f}"
                        logger.info(f"基于¥符号找到金额: {amount} 和税额: {tax}")
                
                # 如果没有找到带¥符号的数字，使用原来的逻辑
                if not invoice_info["total_amount"]:
                    # 按y坐标排序，找到最下面的数字（通常是合计金额）
                    bottom_numbers = sorted(numbers, key=lambda x: x[2][0][1], reverse=True)
                    logger.info(f"按位置排序的数字: {bottom_numbers}")
                    
                    # 提取最下面的几个数字，特别关注合计行
                    potential_amounts = []
                    last_y = None
                    
                    # 先查找是否有合计行
                    total_line_y = None
                    for text, confidence, pos in texts_with_pos:
                        if "合计" in text:
                            total_line_y = pos[0][1]
                            logger.info(f"找到合计行位置: {total_line_y}")
                            break
                    
                    # 收集潜在金额
                    for num, text, pos in bottom_numbers:
                        current_y = pos[0][1]
                        
                        # 如果找到了合计行，优先处理合计行附近的数字
                        if total_line_y and abs(current_y - total_line_y) < 30:  # 合计行30像素范围内
                            potential_amounts.append((num, text, pos))
                            continue
                        
                        # 处理其他数字
                        if last_y is None or abs(current_y - last_y) < 20:  # 同一行的阈值为20
                            potential_amounts.append((num, text, pos))
                            last_y = current_y
                        elif len(potential_amounts) >= 2:
                            break
                    
                    if potential_amounts:
                        # 按数值大小排序
                        potential_amounts.sort(key=lambda x: x[0])
                        logger.info(f"潜在金额: {potential_amounts}")
                        
                        # 如果找到了税率，优先使用税率判断
                        if tax_rates:
                            tax_rate = tax_rates[0] / 100
                            logger.info(f"使用税率: {tax_rate}")
                            
                            best_match = None
                            min_diff = float('inf')
                            
                            for i in range(len(potential_amounts)):
                                amount = potential_amounts[i][0]
                                expected_tax = round(amount * tax_rate, 2)
                                
                                for j in range(len(potential_amounts)):
                                    if i != j:
                                        tax = potential_amounts[j][0]
                                        diff = abs(tax - expected_tax)
                                        if diff < min_diff and diff < 1.0:
                                            min_diff = diff
                                            best_match = (amount, tax)
                            
                            if best_match:
                                invoice_info["total_amount"] = f"{best_match[0]:.2f}"
                                invoice_info["tax_amount"] = f"{best_match[1]:.2f}"
                                logger.info(f"基于税率找到金额: {invoice_info['total_amount']} 和税额: {invoice_info['tax_amount']}")
                        
                        # 如果没有找到税率或税率方法失败，使用数值关系判断
                        if not invoice_info["total_amount"] and len(potential_amounts) >= 2:
                            amount = potential_amounts[-2][0]
                            tax = potential_amounts[-1][0]
                            if 0.05 <= tax/amount <= 0.17:
                                invoice_info["total_amount"] = f"{amount:.2f}"
                                invoice_info["tax_amount"] = f"{tax:.2f}"
                                logger.info(f"基于比例找到金额: {amount} 和税额: {tax}")

            # 清理重复的商品明细
            if invoice_info["items"]:
                items = []
                seen = set()
                for item in invoice_info["items"]:
                    item_key = item["item_name"]
                    if item_key not in seen:
                        items.append(item)
                        seen.add(item_key)
                invoice_info["items"] = items

        except Exception as e:
            logger.error(f"提取发票信息时出错: {str(e)}")
            logger.exception(e)
            
        return invoice_info

    def _extract_item_info(self, text: str, texts_with_pos: List, current_idx: int) -> Optional[Dict]:
        """提取商品信息"""
        try:
            # 处理商品名称中的特殊字符
            item_name = text
            for char in ['*', '+', ':', '：']:
                if char in item_name:
                    parts = item_name.split(char)
                    item_name = char.join(part.strip() for part in parts if len(part.strip()) > 0)
            
            # 提取数量和单位
            quantity_match = None
            unit = ""
            
            # 1. 尝试匹配标准格式（数字+单位）
            quantity_pattern = r'(\d+\.?\d*)\s*([个件套包箱本份条块张]|ml|g|kg|台|箱|瓶|片|粒)?'
            match = re.search(quantity_pattern, text)
            if match:
                quantity_match = match
                unit = match.group(2) if match.group(2) else ""
            
            # 2. 尝试匹配复合单位（如 5ml:1g）
            if not quantity_match:
                compound_pattern = r'(\d+\.?\d*)\s*(ml|g|kg|台|箱|瓶|片|粒)[:：](\d+\.?\d*)\s*(ml|g|kg|台|箱|瓶|片|粒)'
                match = re.search(compound_pattern, text)
                if match:
                    quantity_match = match
                    unit = f"{match.group(2)}:{match.group(4)}"
            
            if quantity_match:
                quantity = float(quantity_match.group(1))
                item_name = text[:quantity_match.start()].strip()
                
                # 查找单价和金额
                unit_price = None
                amount = None
                
                # 在后续几行中查找价格信息
                for i in range(1, 4):  # 查找后面3行
                    if current_idx + i < len(texts_with_pos):
                        next_text = texts_with_pos[current_idx + i][0].strip()
                        # 尝试提取数字
                        price_matches = re.finditer(r'(\d+\.?\d*)', next_text)
                        for price_match in price_matches:
                            price = float(price_match.group(1))
                            if price > 0:
                                if not unit_price:
                                    unit_price = price
                                elif not amount:
                                    amount = price
                                    break
                
                # 如果找到了单价，计算金额
                if unit_price and not amount:
                    amount = quantity * unit_price
                
                # 构建商品信息
                item_info = {
                    "item_name": item_name,
                    "quantity": quantity,
                    "unit": unit
                }
                
                if unit_price:
                    item_info["unit_price"] = unit_price
                if amount:
                    item_info["amount"] = amount
                
                return item_info
            
            # 如果没有找到数量信息，但是商品名称有效
            if self._is_valid_item_name(item_name):
                return {"item_name": item_name}
            
        except Exception as e:
            logger.error(f"提取商品信息时出错: {str(e)}")
        
        return None

    def _is_valid_item_name(self, name: str) -> bool:
        """验证商品名称是否有效"""
        if not name:
            return False
            
        # 清理特殊字符
        name = name.strip('*+: ：')
        
        # 排除过短的名称
        if len(name) < 2:
            return False
            
        # 排除纯数字、符号和特殊字符
        if re.match(r'^[\d\s,.*/<>+\-¥]+$', name):
            return False
            
        # 排除常见的非商品文本
        invalid_keywords = {
            '地址', '电话', '开户', '账号', '行号', '纳税人', '识别号', 
            '合计', '小计', '税额', '价税', '传真', '邮编', '备注',
            '复核', '收款人', '开票人', '名称', '代码', '日期', '号码',
            '(小写)', '(大写)', '￥', '¥', '元', '(', ')', '小写', '大写'
        }
        
        if any(keyword in name for keyword in invalid_keywords):
            return False
            
        # 排除可能是金额的行
        if re.search(r'\d+\.\d{2}$', name):
            return False
            
        return True