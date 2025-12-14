"""
API Configuration using Pydantic Settings
"""
import os
from functools import lru_cache
from typing import Optional


class Settings:
    """Application settings loaded from environment"""
    
    def __init__(self):
        # Database settings
        self.use_mock_db: bool = os.environ.get("USE_MOCK_DB", "false").lower() == "true"
        self.dynamodb_table_name: str = os.environ.get("DYNAMODB_TABLE_NAME", 
                                                        os.environ.get("TABLE_NAME", "TrustModelRegistry"))
        self.dynamodb_endpoint_url: Optional[str] = os.environ.get("DYNAMODB_ENDPOINT_URL")
        self.aws_region: str = os.environ.get("AWS_REGION", "us-east-1")
        
        # Auth settings
        self.jwt_secret_key: str = os.environ.get("JWT_SECRET_KEY", "your-secret-key-here")
        self.jwt_algorithm: str = "HS256"
        self.jwt_expiration_hours: int = 24
        
        # API tokens
        self.hf_token: str = os.environ.get("HF_TOKEN", "")
        self.github_token: str = os.environ.get("GITHUB_TOKEN", "")
        
        # Valid credentials
        self.valid_credentials = {
            ("ece461", "password"),
            ("ece30861defaultadminuser", "correcthorsebatterystaple123(!__+@**(A;DROP TABLE packages")
        }
        
        # Rating threshold for ingest
        self.ingest_threshold: float = 0.5


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
