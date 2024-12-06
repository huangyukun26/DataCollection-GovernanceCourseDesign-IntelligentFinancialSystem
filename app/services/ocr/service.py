from typing import Optional
from .factory import OCRFactory

class OCRService:
    def __init__(self):
        self.tesseract_engine = OCRFactory.create('tesseract')
    
    async def recognize(self, image_path: str, engine_type: Optional[str] = 'tesseract') -> str:
        return await self.tesseract_engine.recognize(image_path) 