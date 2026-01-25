"""
Database Package

Provides database connectivity, models, and repositories for persistent storage.
Supports both SQLite (development) and PostgreSQL (production).
"""

from database.connection import get_db, init_db, close_db
from database.models import User, Conversation, Message, AuditLog

__all__ = [
    "get_db",
    "init_db", 
    "close_db",
    "User",
    "Conversation",
    "Message",
    "AuditLog",
]
