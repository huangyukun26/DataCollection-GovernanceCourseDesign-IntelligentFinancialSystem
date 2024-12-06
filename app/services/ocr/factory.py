from typing import Dict, Type
from .base import OCREngine
from .tesseract_ocr import TesseractOCREngine

class OCRFactory:
    _engines: Dict[str, Type[OCREngine]] = {
        'tesseract': TesseractOCREngine
    }
    
    @classmethod
    def create(cls, engine_type: str) -> OCREngine:
        engine_class = cls._engines.get(engine_type)
        if not engine_class:
            raise ValueError(f"Unknown OCR engine type: {engine_type}")
        return engine_class() 