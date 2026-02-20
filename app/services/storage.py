import boto3
from botocore.config import Config
from datetime import datetime, timedelta, timezone
from app.config import settings

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f"https://{settings.S3_ENDPOINT}" if not settings.S3_ENDPOINT.startswith("http") else settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self.expires_in_seconds = 3600 # 1 hour

    def generate_presigned_url(self, filename: str, file_path_context: list[str], account_id: str, device_id: str) -> tuple[str, str, datetime]:
        """
        Generates a presigned URL for uploading a file.
        Returns the URL, the object key, and the expiration datetime.
        """
        now = datetime.now(timezone.utc)
        date_path = now.strftime("%Y-%m-%d")
        context_path = "/".join(file_path_context)
        sanitized_device_id = device_id.replace(":", "-")
        
        # Structure: {account_id}/{device_id}/{context}/{date}/{filename}
        # Ensure no double slashes if context is empty
        base_path = f"{account_id}/{sanitized_device_id}"
        suffix_path = f"{context_path}/{date_path}/{filename}" if context_path else f"{date_path}/{filename}"
        
        object_name = f"{base_path}/{suffix_path}"
        
        # Remove leading slash if present (S3 keys shouldn't start with / usually)
        if object_name.startswith("/"):
            object_name = object_name[1:]

        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_name,
                    # Optional: We could enforce content-length or checksum here if we wanted strictly signed headers
                },
                ExpiresIn=self.expires_in_seconds
            )
            expires_at = now + timedelta(seconds=self.expires_in_seconds)
            return url, object_name, expires_at
        except Exception as e:
            # In a real app, log this error
            print(f"Error generating presigned URL: {e}")
            raise e

storage_service = StorageService()

def get_storage_service() -> StorageService:
    return storage_service
