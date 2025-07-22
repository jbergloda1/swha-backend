import boto3
import logging
import os
import time
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import settings

logger = logging.getLogger(__name__)

class S3Service:
    """Service for AWS S3 operations including file upload and presigned URL generation."""
    
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        self.presigned_url_expiry = settings.S3_PRESIGNED_URL_EXPIRY
        self._s3_client = None
        
    @property
    def s3_client(self):
        """Lazy loading of S3 client."""
        if self._s3_client is None:
            try:
                self._s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=self.region
                )
                logger.info("S3 client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {str(e)}")
                raise e
        return self._s3_client
    
    def check_bucket_exists(self) -> bool:
        """Check if the S3 bucket exists and is accessible."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket '{self.bucket_name}' is accessible")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket '{self.bucket_name}' does not exist")
            else:
                logger.error(f"Error accessing S3 bucket: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking S3 bucket: {str(e)}")
            return False
    
    def upload_audio_file(
        self, 
        file_path: str, 
        s3_key: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Upload audio file to S3.
        
        Args:
            file_path: Local path to the audio file
            s3_key: S3 object key (path) for the file
            metadata: Optional metadata to attach to the file
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False
            
            # Prepare ExtraArgs for upload_file
            extra_args = {
                'ContentType': 'audio/wav'
            }
            
            # Add metadata if provided
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload file using correct boto3 syntax
            self.s3_client.upload_file(
                Filename=file_path,
                Bucket=self.bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Successfully uploaded {file_path} to s3://{self.bucket_name}/{s3_key}")
            return True
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return False
        except NoCredentialsError:
            logger.error("AWS credentials not available")
            return False
        except ClientError as e:
            logger.error(f"AWS S3 error uploading file: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading file: {str(e)}")
            return False
    
    def generate_presigned_url(
        self, 
        s3_key: str, 
        expiry_seconds: Optional[int] = None
    ) -> Optional[str]:
        """
        Generate presigned URL for S3 object.
        
        Args:
            s3_key: S3 object key
            expiry_seconds: URL expiry time in seconds (default from config)
            
        Returns:
            Presigned URL string or None if error
        """
        try:
            expiry = expiry_seconds or self.presigned_url_expiry
            
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiry
            )
            
            logger.debug(f"Generated presigned URL for {s3_key}, expires in {expiry} seconds")
            return presigned_url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL for {s3_key}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {str(e)}")
            return None
    
    def upload_and_get_presigned_url(
        self,
        file_path: str,
        s3_key: str,
        metadata: Optional[Dict] = None,
        expiry_seconds: Optional[int] = None
    ) -> Optional[str]:
        """
        Upload file to S3 and return presigned URL.
        
        Args:
            file_path: Local path to the audio file
            s3_key: S3 object key
            metadata: Optional metadata
            expiry_seconds: URL expiry time
            
        Returns:
            Presigned URL or None if error
        """
        # Upload file first
        if not self.upload_audio_file(file_path, s3_key, metadata):
            return None
        
        # Generate presigned URL
        return self.generate_presigned_url(s3_key, expiry_seconds)
    
    def delete_audio_file(self, s3_key: str) -> bool:
        """
        Delete audio file from S3.
        
        Args:
            s3_key: S3 object key to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Successfully deleted s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting S3 object {s3_key}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting S3 object: {str(e)}")
            return False
    
    def list_audio_files(self, prefix: str = "") -> List[str]:
        """
        List audio files in S3 bucket.
        
        Args:
            prefix: S3 key prefix to filter objects
            
        Returns:
            List of S3 object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            objects = response.get('Contents', [])
            return [obj['Key'] for obj in objects]
            
        except ClientError as e:
            logger.error(f"Error listing S3 objects: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing S3 objects: {str(e)}")
            return []
    
    def cleanup_old_files(self, prefix: str, days_old: int = 7) -> int:
        """
        Delete audio files older than specified days.
        
        Args:
            prefix: S3 key prefix to filter objects
            days_old: Delete files older than this many days
            
        Returns:
            Number of files deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            deleted_count = 0
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            objects = response.get('Contents', [])
            
            for obj in objects:
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=obj['Key'])
                    deleted_count += 1
                    logger.info(f"Deleted old file: {obj['Key']}")
            
            logger.info(f"Cleaned up {deleted_count} old audio files from S3")
            return deleted_count
            
        except ClientError as e:
            logger.error(f"Error during S3 cleanup: {str(e)}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error during cleanup: {str(e)}")
            return 0
    
    def get_file_info(self, s3_key: str) -> Optional[Dict]:
        """
        Get metadata and info about S3 object.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Dictionary with file info or None if error
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                'size': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {}),
                'etag': response.get('ETag', '').strip('"')
            }
            
        except ClientError as e:
            logger.error(f"Error getting S3 object info for {s3_key}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting object info: {str(e)}")
            return None


# Singleton instance
_s3_service = None

def get_s3_service() -> Optional[S3Service]:
    """Get singleton instance of S3 service if S3 is enabled."""
    global _s3_service
    
    if not settings.s3_enabled:
        logger.warning("S3 service requested but S3 is not enabled or configured")
        return None
    
    if _s3_service is None:
        try:
            _s3_service = S3Service()
            # Test connection
            if not _s3_service.check_bucket_exists():
                logger.error("S3 bucket is not accessible")
                _s3_service = None
        except Exception as e:
            logger.error(f"Failed to initialize S3 service: {str(e)}")
            _s3_service = None
    
    return _s3_service 