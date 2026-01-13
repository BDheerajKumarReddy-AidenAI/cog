from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.database import Base
from datetime import datetime


class LLMCache(Base):
    """Cache table for LLM responses - not part of the analytics schema."""
    __tablename__ = "llm_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(64), unique=True, nullable=False, index=True)
    model = Column(String(100), nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
