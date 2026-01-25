"""
User Repository

Data access layer for user operations.
Note: Full implementation will be completed in Step 11 (Authentication & Authorization)
"""

from typing import Optional
from sqlalchemy.orm import Session
from database.models import User


class UserRepository:
    """Repository for user operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key."""
        return self.db.query(User).filter(User.api_key == api_key).first()
    
    # Full implementation in Step 11
