import pytesseract
from PIL import Image
from .base import OCREngine

class TesseractOCREngine(OCREngine):
    async def recognize(self, image_path: str) -> str:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        return text
    
    async def preprocess_image(self, image_path: str):
        # 图像预处理逻辑将在后续实现
        pass 