"""
Message Repository

Data access layer for message operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import Message


class MessageRepository:
    """Repository for message operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_message(self, message_id: int) -> Optional[Message]:
        """Get message by ID."""
        return self.db.query(Message).filter(Message.id == message_id).first()
    
    def get_message_by_external_id(self, message_id: str) -> Optional[Message]:
        """Get message by external message ID."""
        return self.db.query(Message).filter(Message.message_id == message_id).first()
