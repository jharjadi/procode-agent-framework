"""
Conversation Repository

Data access layer for conversations and messages.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from database.models import Conversation, Message


class ConversationRepository:
    """Repository for conversation operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_conversation(
        self,
        user_id: int,
        conversation_id: Optional[str] = None,
        title: Optional[str] = None,
        intent: Optional[str] = None
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            user_id: User ID
            conversation_id: Optional conversation ID (UUID string)
            title: Conversation title
            intent: Detected intent
            
        Returns:
            Created conversation
        """
        conversation = Conversation(
            id=conversation_id,  # Use provided ID if given
            user_id=user_id,
            title=title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            intent=intent,
            status="active"
        )
        self.db.add(conversation)
        self.db.flush()  # Get the ID without committing
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get conversation by ID.
        
        Args:
            conversation_id: Conversation ID (UUID string)
            
        Returns:
            Conversation or None
        """
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
    
    def get_user_conversations(
        self,
        user_id: int,
        status: str = "active",
        limit: int = 50
    ) -> List[Conversation]:
        """
        Get user's conversations.
        
        Args:
            user_id: User ID
            status: Conversation status filter
            limit: Maximum number of conversations
            
        Returns:
            List of conversations
        """
        query = self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        )
        
        if status:
            query = query.filter(Conversation.status == status)
        
        return query.order_by(desc(Conversation.updated_at)).limit(limit).all()
    
    def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        intent: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        Update conversation.
        
        Args:
            conversation_id: Conversation ID (UUID string)
            title: New title
            intent: New intent
            status: New status
            
        Returns:
            Updated conversation or None
        """
        conversation = self.get_conversation(conversation_id)
        
        if conversation:
            if title is not None:
                conversation.title = title
            if intent is not None:
                conversation.intent = intent
            if status is not None:
                conversation.status = status
            
            conversation.updated_at = datetime.utcnow()
            self.db.flush()
        
        return conversation
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete conversation (soft delete by setting status).
        
        Args:
            conversation_id: Conversation ID (UUID string)
            
        Returns:
            True if deleted, False otherwise
        """
        conversation = self.get_conversation(conversation_id)
        
        if conversation:
            conversation.status = "deleted"
            conversation.updated_at = datetime.utcnow()
            self.db.flush()
            return True
        
        return False
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_id: Optional[str] = None,
        intent: Optional[str] = None,
        model_used: Optional[str] = None,
        cost: float = 0.0,
        extra_metadata: Optional[dict] = None
    ) -> Message:
        """
        Add message to conversation.
        
        Args:
            conversation_id: Conversation ID (UUID string)
            role: Message role (user, assistant, system)
            content: Message content
            message_id: External message ID
            intent: Detected intent
            model_used: Model used for response
            cost: Cost of message
            extra_metadata: Additional metadata
            
        Returns:
            Created message
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_id=message_id,
            intent=intent,
            model_used=model_used,
            cost=cost,
            extra_metadata=extra_metadata
        )
        self.db.add(message)
        
        # Update conversation's updated_at
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.updated_at = datetime.utcnow()
        
        self.db.flush()
        return message
    
    def get_conversation_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages for a conversation.
        
        Args:
            conversation_id: Conversation ID (UUID string)
            limit: Maximum number of messages (most recent)
            
        Returns:
            List of messages
        """
        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at)
        
        if limit:
            # Get the most recent N messages
            query = query.order_by(desc(Message.created_at)).limit(limit)
            messages = query.all()
            messages.reverse()  # Return in chronological order
            return messages
        
        return query.all()
    
    def get_conversation_cost(self, conversation_id: str) -> float:
        """
        Calculate total cost for a conversation.
        
        Args:
            conversation_id: Conversation ID (UUID string)
            
        Returns:
            Total cost
        """
        result = self.db.query(
            func.sum(Message.cost)
        ).filter(
            Message.conversation_id == conversation_id
        ).scalar()
        
        return result or 0.0
    
    def search_conversations(
        self,
        user_id: int,
        search_term: str,
        limit: int = 20
    ) -> List[Conversation]:
        """
        Search user's conversations by title or content.
        
        Args:
            user_id: User ID
            search_term: Search term
            limit: Maximum results
            
        Returns:
            List of matching conversations
        """
        # Search in conversation titles and message content
        conversations = self.db.query(Conversation).join(Message).filter(
            Conversation.user_id == user_id,
            Conversation.status == "active",
            (Conversation.title.ilike(f"%{search_term}%") |
             Message.content.ilike(f"%{search_term}%"))
        ).distinct().order_by(desc(Conversation.updated_at)).limit(limit).all()
        
        return conversations
