from abc import ABC, abstractmethod

class OCREngine(ABC):
    @abstractmethod
    async def recognize(self, image_path: str) -> str:
        pass

    @abstractmethod
    async def preprocess_image(self, image_path: str):
        pass 