from paddleocr import PaddleOCR
from .base import OCREngine

class PaddleOCREngine(OCREngine):
    def __init__(self):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="ch",
            use_gpu=False,
            enable_mkldnn=False,
            cpu_threads=2,
            det_db_thresh=0.3,
            det_db_box_thresh=0.5,
            det_db_unclip_ratio=1.6
        )
    
    async def recognize(self, image_path: str) -> str:
        try:
            result = self.ocr.ocr(image_path, cls=True)
            if not result:
                return ""
            
            text = "\n".join([line[1][0] for line in result[0]])
            return text
        except Exception as e:
            print(f"OCR Error: {str(e)}")
            return ""
    
    async def preprocess_image(self, image_path: str):
        # 图像预处理逻辑将在后续实现
        pass