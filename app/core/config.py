import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    EXTERNAL_API_BASE_URL: str = os.getenv(
        "EXTERNAL_API_BASE_URL", 
        "https://hospital-directory.onrender.com"
    )

    APP_TITLE: str = "Hospital Batch Processor"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Bulk hospital creation and management system"
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", 8000))
    
    # CSV Configuration
    CSV_REQUIRED_HEADERS: list = ["name", "address", "phone"]
    CSV_MAX_SIZE_MB: int = 10
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
