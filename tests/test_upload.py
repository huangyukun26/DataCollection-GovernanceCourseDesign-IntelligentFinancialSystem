import requests
import os

def test_document_upload():
    # API端点
    url = "http://localhost:8000/api/v1/documents/upload/"
    
    # 测试文件路径
    test_files = {
        'contract': 'test_data/contract_sample.jpg',
        'invoice': 'test_data/invoice_sample.jpg',
        'bank_statement': 'test_data/bank_statement_sample.jpg'
    }
    
    for doc_type, file_path in test_files.items():
        # 确保测试文件存在
        if not os.path.exists(file_path):
            print(f"Warning: Test file {file_path} not found")
            continue
            
        # 准备上传数据
        files = {
            'file': open(file_path, 'rb')
        }
        data = {
            'doc_type': doc_type
        }
        
        try:
            # 发送请求
            response = requests.post(url, files=files, data=data)
            
            # 检查响应
            if response.status_code == 200:
                print(f"Successfully uploaded {doc_type}")
                print("Response:", response.json())
            else:
                print(f"Failed to upload {doc_type}")
                print("Status code:", response.status_code)
                print("Response:", response.text)
                
        except Exception as e:
            print(f"Error uploading {doc_type}:", str(e))
        finally:
            files['file'].close()

if __name__ == "__main__":
    test_document_upload() 