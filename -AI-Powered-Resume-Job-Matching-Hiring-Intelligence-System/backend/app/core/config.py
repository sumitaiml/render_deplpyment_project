"""
Core configuration for the HRTech Platform
Handles database connections, settings, and environment variables
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Environment
    APP_ENV: str = "development"
    LOG_LEVEL: str = "info"
    
    # Database
    DATABASE_URL: str = "sqlite:///./hrtech_db.db"
    DATABASE_ECHO: bool = False
    
    # Redis (for caching)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Embedding & Vector DB
    VECTOR_DB_TYPE: str = "faiss"  # "faiss" or "pinecone"
    VECTOR_DB_PATH: str = "./data/embeddings"
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_INDEX_NAME: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    
    # NLP Models
    SPACY_MODEL: str = "en_core_web_sm"
    SBERT_MODEL: str = "all-MiniLM-L6-v2"
    
    # ML Models paths
    SENIORITY_MODEL_PATH: str = "./models/seniority_model.pkl"
    RANKING_MODEL_PATH: str = "./models/ranking_model.pkl"
    SKILL_GRAPH_PATH: str = "./data/skill_ontology/skill_graph.json"
    
    # File upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_RESUME_FORMATS: list = ["pdf", "docx", "txt"]
    
    # API
    API_TITLE: str = "HRTech Platform API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "AI-powered resume screening and candidate ranking"
    
    # Ranking parameters
    SKILL_WEIGHT: float = 0.4
    EXPERIENCE_WEIGHT: float = 0.35
    SENIORITY_WEIGHT: float = 0.25
    
    # Bias mitigation
    APPLY_BIAS_MITIGATION: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


class DatabaseManager:
    """Database connection manager"""
    
    _engine = None
    _session_maker = None
    
    @classmethod
    def initialize(cls):
        """Initialize database engine and session factory"""
        cls._engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
        )
        
        cls._session_maker = sessionmaker(
            bind=cls._engine,
            expire_on_commit=False
        )
    
    @classmethod
    def get_engine(cls):
        """Get database engine"""
        if cls._engine is None:
            cls.initialize()
        return cls._engine
    
    @classmethod
    def get_session_maker(cls):
        """Get session factory"""
        if cls._session_maker is None:
            cls.initialize()
        return cls._session_maker
    
    @classmethod
    def create_session(cls):
        """Create a new database session"""
        session_factory = cls.get_session_maker()
        return session_factory()
    
    @classmethod
    def create_all_tables(cls):
        """Create all database tables"""
        from app.models import Base
        engine = cls.get_engine()
        Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency injection for database session"""
    db = DatabaseManager.create_session()
    try:
        yield db
    finally:
        db.close()


