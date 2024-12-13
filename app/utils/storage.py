from minio import Minio
import os
from dotenv import load_dotenv
import io
from datetime import timedelta

load_dotenv()

class MinioStorage:
    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_URL", "localhost:9000"),
            access_key=os.getenv("MINIO_ROOT_USER", "admin"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD", "admin123"),
            secure=False
        )
        self.bucket_name = os.getenv("MINIO_BUCKET", "invoices")
        
        # 确保bucket存在
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            # 设置bucket策略允许公共读取
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                    }
                ]
            }
            self.client.set_bucket_policy(self.bucket_name, policy)
    
    async def upload_file(self, file_path: str, file_data: bytes):
        """上传文件到MinIO"""
        try:
            # 将字节数据转换为BytesIO对象
            file_data_io = io.BytesIO(file_data)
            
            # 使用put_object上传文件
            result = self.client.put_object(
                self.bucket_name,
                file_path,
                file_data_io,
                length=len(file_data),
                content_type='image/jpeg'  # 设置内容类型为图片
            )
            return result
        except Exception as e:
            print(f"上传文件到MinIO失败: {str(e)}")
            raise e

    async def delete_file(self, file_path: str):
        """从MinIO删除文件"""
        try:
            self.client.remove_object(self.bucket_name, file_path)
        except Exception as e:
            print(f"从MinIO删除文件失败: {str(e)}")
            raise e

    async def get_file_url(self, file_path: str) -> str:
        """获取文件的URL"""
        try:
            # 生成一个临时的URL，有效期为7天
            expires = timedelta(days=7)  # 使用timedelta对象
            url = self.client.presigned_get_object(
                self.bucket_name,
                file_path,
                expires=expires
            )
            return url
        except Exception as e:
            print(f"获取文件URL失败: {str(e)}")
            raise e 