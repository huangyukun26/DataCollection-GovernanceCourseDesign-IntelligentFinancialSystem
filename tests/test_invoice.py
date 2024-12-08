import requests
import os
import json
from pathlib import Path

def test_invoice_upload():
    # API端点
    api_url = os.getenv("API_URL", "http://localhost:8000")
    url = f"{api_url}/api/v1/documents/upload/"
    
    # 测试文件目录
    test_dir = Path(__file__).parent / "test_data" / "invoice"
    
    # 遍历测试文件目录中的所有图片
    for file_path in test_dir.glob("*.jpg"):
        print(f"\nTesting file: {file_path.name}")
        
        # 准备上传数据
        with open(file_path, 'rb') as f:
            # 使用 tuple 格式指定文件名、文件对象和 MIME 类型
            files = {
                'file': (file_path.name, f, 'image/jpeg')
            }
            # 使用 form-data 格式传递参数
            form_data = {
                'doc_type': (None, 'invoice')  # 使用 tuple 格式指定参数
            }
            
            try:
                # 发送请求
                response = requests.post(
                    url,
                    files=files,
                    data=form_data,  # 使用 form_data 而不是 data
                    timeout=30  # 添加超时设置
                )
                
                print("\nRequest details:")
                print("URL:", url)
                print("Form data:", form_data)
                print("Files:", [k for k in files.keys()])
                
                # 检查响应
                if response.status_code == 200:
                    result = response.json()
                    print("\nUpload successful!")
                    print("\nExtracted Data:")
                    print(json.dumps(result['result']['extracted_data'], indent=2, ensure_ascii=False))
                    
                    # 验证关键字段
                    extracted_data = result['result']['extracted_data']
                    validate_invoice_data(extracted_data)
                    
                else:
                    print("\nUpload failed!")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)
                    
            except Exception as e:
                print("\nError:", str(e))
                print("\nRequest details:")
                print("URL:", url)
                print("Form data:", form_data)
                print("Files:", [k for k in files.keys()])

def validate_invoice_data(data):
    """验证发票数据的完整性"""
    required_fields = ['invoice_number', 'invoice_date', 'amount', 'tax_amount', 'seller', 'buyer']
    
    print("\nValidation Results:")
    for field in required_fields:
        if field in data and data[field]:
            print(f"✓ {field}: {data[field]}")
        else:
            print(f"✗ {field} is missing or empty")

if __name__ == "__main__":
    test_invoice_upload() 