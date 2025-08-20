from __future__ import annotations
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import NullPool

Base = declarative_base()

def _get_db_url():
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    return "sqlite:///data.db"

DB_URL = _get_db_url()
engine = create_engine(DB_URL, poolclass=NullPool, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    plan = Column(String, default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    payments = relationship("Payment", back_populates="user", cascade="all, delete")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    status = Column(String, default="created")
    amount = Column(Integer, default=0)
    currency = Column(String, default="BRL")
    provider = Column(String, default="stripe")
    checkout_session_id = Column(String, index=True)
    payment_intent_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="payments")

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    return SessionLocal()
