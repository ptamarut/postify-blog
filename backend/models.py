from sqlalchemy import Column, Integer, String, DateTime, Text, func
from .database import Base

# Tablica za postove
class Post(Base):
    __tablename__ = "posts"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    image_filename = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Tablica za korisnike (admin)
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
