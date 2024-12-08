from paddleocr import PaddleOCR
from .base import OCREngine
import cv2

class PaddleOCREngine(OCREngine):
    def __init__(self):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="ch",
            use_gpu=False,
            enable_mkldnn=True,
            cpu_threads=4,
            det_db_thresh=0.3,
            det_db_box_thresh=0.5,
            det_db_unclip_ratio=1.6,
            rec_char_dict_path='ppocr/utils/dict/chinese_cht_dict.txt'
        )
    
    async def recognize(self, image_path: str) -> str:
        try:
            print(f"\nStarting OCR recognition for: {image_path}")
            
            # 图像预处理
            processed_path = await self.preprocess_image(image_path)
            print(f"Preprocessed image saved to: {processed_path}")
            
            # OCR识别
            result = self.ocr.ocr(processed_path, cls=True)
            print(f"Raw OCR result: {result}")
            
            if not result:
                print("No text detected!")
                return ""
            
            # 提取文本，按位置排序
            texts = []
            for line in result[0]:
                box = line[0]  # 文本框坐标
                text = line[1][0]  # 识别的文本
                confidence = line[1][1]  # 置信度
                print(f"Detected text: '{text}' (confidence: {confidence:.2f})")
                if confidence > 0.8:  # 只保留置信度高的结果
                    texts.append(text)
            
            final_text = "\n".join(texts)
            print(f"\nFinal extracted text:\n{final_text}")
            return final_text
            
        except Exception as e:
            print(f"OCR Error: {str(e)}")
            return ""
    
    async def preprocess_image(self, image_path: str):
        try:
            image = cv2.imread(image_path)
            # 图像增强
            image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
            # 对比度调整
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            cl = clahe.apply(l)
            processed = cv2.merge((cl,a,b))
            processed = cv2.cvtColor(processed, cv2.COLOR_LAB2BGR)
            
            # 保存处理后的图像
            processed_path = image_path.replace('.', '_processed.')
            cv2.imwrite(processed_path, processed)
            return processed_path
        except Exception as e:
            print(f"Image preprocessing error: {str(e)}")
            return image_path