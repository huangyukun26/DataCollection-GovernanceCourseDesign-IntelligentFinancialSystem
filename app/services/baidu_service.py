import os
from typing import Dict, Any, List
import json
import requests
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class BaiduService:
    def __init__(self):
        self.api_key = os.getenv("BAIDU_API_KEY")
        self.secret_key = os.getenv("BAIDU_SECRET_KEY")
        self.access_token = None
        self.token_expire_time = None
        
    def get_access_token(self) -> str:
        """获取百度API access token"""
        if self.access_token and self.token_expire_time and datetime.now() < self.token_expire_time:
            return self.access_token
            
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        response = requests.post(url, params=params)
        result = response.json()
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            # token有效期30天，这里设置29天后过期
            self.token_expire_time = datetime.now() + timedelta(days=29)
            return self.access_token
        else:
            raise Exception("获取百度API access token失败")

class BaiduOCRService(BaiduService):
    def __init__(self):
        super().__init__()
        
    def recognize_table(self, image_data: bytes) -> Dict[str, Any]:
        """表格文字识别"""
        try:
            url = "https://aip.baidubce.com/rest/2.0/ocr/v1/table"
            
            params = {
                "access_token": self.get_access_token()
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "image": base64.b64encode(image_data).decode()
            }
            
            response = requests.post(url, params=params, headers=headers, data=data)
            result = response.json()
            
            # 检查错误响应
            if "error_code" in result:
                raise Exception(f"百度OCR API错误: {result.get('error_msg', '未知错误')}")
                
            return result
        except Exception as e:
            raise Exception(f"表格识别失败: {str(e)}")
        
    def recognize_handwriting(self, image_data: bytes) -> Dict[str, Any]:
        """手写文字识别"""
        try:
            url = "https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting"
            
            params = {
                "access_token": self.get_access_token()
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "image": base64.b64encode(image_data).decode()
            }
            
            response = requests.post(url, params=params, headers=headers, data=data)
            result = response.json()
            
            # 检查错误响应
            if "error_code" in result:
                raise Exception(f"百度OCR API错误: {result.get('error_msg', '未知错误')}")
                
            return result
        except Exception as e:
            raise Exception(f"手写识别失败: {str(e)}")

class BaiduNLPService(BaiduService):
    def __init__(self):
        super().__init__()
        
    def entity_recognize(self, text: str) -> List[Dict[str, Any]]:
        """实体识别"""
        try:
            url = "https://aip.baidubce.com/rpc/2.0/nlp/v1/lexer"
            
            params = {
                "access_token": self.get_access_token()
            }
            
            payload = {
                "text": text
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, params=params, headers=headers, json=payload)
            result = response.json()
            
            # 检查错误响应
            if "error_code" in result:
                raise Exception(f"百度NLP API错误: {result.get('error_msg', '未知错误')}")
                
            return result.get("items", [])
        except Exception as e:
            print(f"实体识别失败: {str(e)}")
            return []
        
    def text_correct(self, text: str) -> str:
        """文本纠错"""
        try:
            if not text or not isinstance(text, str):
                return ""
                
            url = "https://aip.baidubce.com/rpc/2.0/nlp/v1/ecnet"
            
            params = {
                "access_token": self.get_access_token()
            }
            
            payload = {
                "text": text
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, params=params, headers=headers, json=payload)
            result = response.json()
            
            # 检查错误响应
            if "error_code" in result:
                print(f"文本纠错API错误: {result.get('error_msg', '未知错误')}")
                return text
                
            corrected = result.get("item", {}).get("correct_query")
            return corrected if corrected else text
        except Exception as e:
            print(f"文本纠错失败: {str(e)}")
            return text