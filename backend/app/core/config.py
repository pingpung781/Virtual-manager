import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "Virtual AI Manager"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./vam.db"))
    
    # Vector DB
    VECTOR_DB_PATH: str = Field(default_factory=lambda: os.getenv("VECTOR_DB_PATH", "./chroma_db"))

    # LLM
    OPENAI_API_KEY: str | None = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))

    class Config:
        case_sensitive = True

settings = Settings()
