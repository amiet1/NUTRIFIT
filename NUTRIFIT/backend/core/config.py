import logging
import os
from typing import Any
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Application
    app_name: str = "NutriFit AI"
    debug: bool = False
    version: str = "1.0.0"

    # Infrastructure
    database_url: str = "sqlite+aiosqlite:///./nutrifit.db"
    app_ai_key: str = "" 
    host: str = "0.0.0.0"
    port: int = 8000

    # AWS Lambda Configuration
    is_lambda: bool = False
    lambda_function_name: str = "fastapi-backend"
    aws_region: str = "us-east-1"

    # This replaces the old 'class Config' and handles the .env loading correctly
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=False, 
        extra="ignore"
    )

    @property
    def backend_url(self) -> str:
        """Generate backend URL from host and port."""
        if self.is_lambda:
            return os.environ.get(
                "PYTHON_BACKEND_URL", f"https://{self.lambda_function_name}.execute-api.{self.aws_region}.amazonaws.com"
            )
        else:
            display_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
            return os.environ.get("PYTHON_BACKEND_URL", f"http://{display_host}:{self.port}")

# This creates the singleton instance for the rest of the app
settings = Settings()
