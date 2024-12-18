from typing import Dict, Type
from .base import BankStatementParser
from .beijing_bank import BeijingBankParser
from .ceb_v1 import CEBV1Parser
from .ceb_v2 import CEBV2Parser
from .ccb_v1 import CCBV1Parser
from .ccb_v2 import CCBV2Parser
from .ccb_v3 import CCBV3Parser

class BankParserFactory:
    """银行流水解析器工厂"""
    
    # 注册解析器映射
    _parsers: Dict[str, Type[BankStatementParser]] = {
        'beijing_bank': BeijingBankParser,
        'ceb_v1': CEBV1Parser,      # 光大银行版式1
        'ceb_v2': CEBV2Parser,      # 光大银行版式2
        'ccb_v1': CCBV1Parser,      # 建设银行版式1
        'ccb_v2': CCBV2Parser,      # 建设银行版式2
        'ccb_v3': CCBV3Parser       # 建设银行版式3
    }
    
    @classmethod
    def register_parser(cls, bank_type: str, parser_class: Type[BankStatementParser]):
        """注册新的解析器
        
        Args:
            bank_type: 银行类型标识
            parser_class: 解析器类
        """
        cls._parsers[bank_type] = parser_class
    
    @classmethod
    def get_parser(cls, bank_type: str) -> BankStatementParser:
        """获取指定银行类型的解析器实例
        
        Args:
            bank_type: 银行类型标识
            
        Returns:
            解析器实例
            
        Raises:
            ValueError: 不支持的银行类型
        """
        parser_class = cls._parsers.get(bank_type)
        if not parser_class:
            raise ValueError(f"Unsupported bank type: {bank_type}")
        return parser_class() 