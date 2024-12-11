from minio import Minio
from minio.error import S3Error
from ..core.config import settings
import io

class MinioStorage:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_URL,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False  # 本地开发环境使用http
        )
        self.bucket_name = "invoices"
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保bucket存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise Exception(f"MinIO错误: {str(e)}")
    
    def upload_file(self, file_data: bytes, object_name: str, content_type: str = "application/octet-stream"):
        """上传文件到MinIO"""
        try:
            self.client.put_object(
                self.bucket_name,
                object_name,
                io.BytesIO(file_data),
                len(file_data),
                content_type
            )
            return f"{self.bucket_name}/{object_name}"
        except S3Error as e:
            raise Exception(f"文件上传失败: {str(e)}")
    
    def get_file(self, object_name: str) -> bytes:
        """从MinIO获取文件"""
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            return response.read()
        except S3Error as e:
            raise Exception(f"文件获取失败: {str(e)}")
        finally:
            response.close()
            response.release_conn()
    
    def delete_file(self, object_name: str):
        """删除MinIO中的文件"""
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error as e:
            raise Exception(f"文件删除失败: {str(e)}") 