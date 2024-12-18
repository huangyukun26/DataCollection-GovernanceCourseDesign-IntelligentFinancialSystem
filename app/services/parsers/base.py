from abc import ABC, abstractmethod
from typing import Dict, Any

class BankStatementParser(ABC):
    """银行流水解析器基类"""
    
    @abstractmethod
    def parse(self, image_data: bytes) -> Dict[str, Any]:
        """解析银行流水图片
        
        Args:
            image_data: 图片二进制数据
            
        Returns:
            解析后的数据字典
        """
        pass
    
    @abstractmethod
    def clean_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗数据
        
        Args:
            raw_data: OCR识别的原始数据
            
        Returns:
            清洗后的标准数据
        """
        pass
    
    @abstractmethod
    def validate_data(self, cleaned_data: Dict[str, Any]) -> bool:
        """验证数据有效性
        
        Args:
            cleaned_data: 清洗后的数据
            
        Returns:
            数据是否有效
        """
        pass 