import boto3
import os
from io import BytesIO
from datetime import datetime

class S3Manager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-2')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')

    def upload_file(self, file_obj, folder, filename=None):
        """
        Upload file to S3
        
        Args:
            file_obj: File object or BytesIO
            folder: Folder path in S3
            filename: Optional filename, if not provided will generate one
            
        Returns:
            S3 URL of uploaded file
        """
        if filename is None:
            filename = f"{datetime.now().timestamp()}-{getattr(file_obj, 'filename', 'file')}"
        
        key = f"{folder}/{filename}"
        
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                key,
                ExtraArgs={'ContentType': 'image/png'}
            )
            
            url = f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION', 'us-east-2')}.amazonaws.com/{key}"
            return url
        except Exception as e:
            raise Exception(f"S3 upload failed: {str(e)}")

    def upload_bytes(self, image_bytes, folder, filename):
        """
        Upload bytes to S3
        
        Args:
            image_bytes: Image bytes
            folder: Folder path in S3
            filename: Filename
            
        Returns:
            S3 URL of uploaded file
        """
        key = f"{folder}/{filename}"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=image_bytes,
                ContentType='image/png'
            )
            
            url = f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION', 'us-east-2')}.amazonaws.com/{key}"
            return url
        except Exception as e:
            raise Exception(f"S3 upload failed: {str(e)}")

    def download_file(self, url):
        """
        Download file from S3 or any URL
        
        Args:
            url: File URL
            
        Returns:
            BytesIO object
        """
        import requests
        try:
            response = requests.get(url)
            response.raise_for_status()
            return BytesIO(response.content)
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

# Global S3 manager instance
s3_manager = None

def get_s3_manager():
    global s3_manager
    if s3_manager is None:
        s3_manager = S3Manager()
    return s3_manager

def upload_to_s3(image_bytes, filename):
    """
    Upload image bytes to S3
    
    Args:
        image_bytes: Image bytes
        filename: Filename
        
    Returns:
        S3 URL of uploaded file
    """
    manager = get_s3_manager()
    return manager.upload_bytes(image_bytes, 'composited-images', filename)
