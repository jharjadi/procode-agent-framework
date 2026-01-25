"""
Database Models

SQLAlchemy ORM models for the application.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, JSON, Index, Float
)
from sqlalchemy.orm import relationship
from database.connection import Base


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Role-based access control
    role = Column(String(50), default="user", nullable=False)  # admin, user, guest
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # API key for programmatic access
    api_key = Column(String(255), unique=True, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class Conversation(Base):
    """Conversation model for storing chat sessions."""
    
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Conversation metadata
    title = Column(String(255), nullable=True)  # Auto-generated or user-set
    intent = Column(String(100), nullable=True)  # tickets, account, payments, general
    status = Column(String(50), default="active", nullable=False)  # active, archived, deleted
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_user_updated', 'user_id', 'updated_at'),
    )
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, intent='{self.intent}')>"


class Message(Base):
    """Message model for storing individual messages in conversations."""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    
    # Message content
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Message metadata
    message_id = Column(String(255), unique=True, nullable=True, index=True)  # External message ID
    intent = Column(String(100), nullable=True)  # Detected intent
    model_used = Column(String(100), nullable=True)  # deterministic, cached, haiku, sonnet
    cost = Column(Float, default=0.0, nullable=False)  # Cost of this message
    
    # Additional metadata (JSON field for flexibility)
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversation_created', 'conversation_id', 'created_at'),
        Index('idx_conversation_role', 'conversation_id', 'role'),
    )
    
    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}')>"


class AuditLog(Base):
    """Audit log model for security and compliance tracking."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for system events
    
    # Event information
    event_type = Column(String(100), nullable=False, index=True)  # login, logout, api_call, error, etc.
    event_category = Column(String(50), nullable=False, index=True)  # security, access, data, system
    severity = Column(String(20), default="info", nullable=False)  # debug, info, warning, error, critical
    
    # Event details
    description = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    
    # Additional context (JSON field)
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_event_type_created', 'event_type', 'created_at'),
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_severity_created', 'severity', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', severity='{self.severity}')>"


# Helper function to create a default admin user
def create_default_admin(session):
    """
    Create a default admin user if none exists.
    
    Args:
        session: Database session
    """
    from security.auth.password import hash_password  # Will create this in Step 11
    
    admin = session.query(User).filter_by(role="admin").first()
    
    if not admin:
        admin = User(
            email="admin@procode.local",
            username="admin",
            hashed_password=hash_password("change_me_immediately"),
            full_name="System Administrator",
            role="admin",
            is_active=True,
            is_verified=True
        )
        session.add(admin)
        session.commit()
        print("✓ Default admin user created (email: admin@procode.local, password: change_me_immediately)")
        print("⚠️  IMPORTANT: Change the admin password immediately!")
