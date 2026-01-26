"""
Conversation memory module for storing and retrieving conversation history.
Supports both in-memory and database persistence.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

class ConversationMemory:
    """
    Manages conversation history for multi-turn dialogues.
    Stores messages in memory with optional database persistence.
    """
    
    def __init__(
        self,
        max_messages: int = None,
        max_age_hours: int = 24,
        use_database: bool = None,
        db_session = None
    ):
        """
        Initialize conversation memory.
        
        Args:
            max_messages: Maximum messages to keep per conversation (default: 10)
            max_age_hours: Maximum age of conversations in hours (default: 24)
            use_database: Whether to persist to database (default: from env USE_DATABASE)
            db_session: Optional database session for persistence
        """
        if max_messages is None:
            max_messages = int(os.getenv("CONVERSATION_WINDOW_SIZE", "10"))
        
        if use_database is None:
            use_database = os.getenv("USE_DATABASE", "false").lower() == "true"
        
        self.max_messages = max_messages
        self.max_age_hours = max_age_hours
        self.use_database = use_database
        self.db_session = db_session
        
        # In-memory storage (always used for caching)
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.conversation_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Lazy-load database repositories if needed
        self._conversation_repo = None
        
        if self.use_database:
            self._init_database()
    
    def _init_database(self):
        """Initialize database connection and repositories."""
        try:
            from database.connection import get_db
            from database.repositories.conversation_repository import ConversationRepository
            
            if self.db_session is None:
                # Get a database session
                self.db_session = next(get_db())
            
            self._conversation_repo = ConversationRepository(self.db_session)
            logger.info("Database persistence enabled for conversation memory")
        except Exception as e:
            logger.warning(f"Failed to initialize database for conversation memory: {e}")
            self.use_database = False
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        intent: Optional[str] = None,
        model_used: Optional[str] = None,
        cost: Optional[float] = None
    ) -> None:
        """
        Add a message to conversation history.
        
        Args:
            conversation_id: Unique conversation identifier
            role: Message role ('user' or 'agent')
            content: Message content
            metadata: Optional metadata (intent, tool_calls, etc.)
            user_id: Optional user ID for database persistence
            intent: Optional detected intent
            model_used: Optional model name used for response
            cost: Optional cost of the message
        """
        # Initialize conversation if new
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            self.conversation_metadata[conversation_id] = {
                "created_at": datetime.now(),
                "last_updated": datetime.now(),
                "message_count": 0,
                "user_id": user_id
            }
            
            # Create conversation in database if enabled
            if self.use_database and self._conversation_repo and user_id:
                try:
                    self._conversation_repo.create_conversation(
                        user_id=user_id,
                        conversation_id=conversation_id,  # Pass the UUID
                        title=f"Conversation {conversation_id[:8]}",
                        intent=intent
                    )
                except Exception as e:
                    logger.error(f"Failed to create conversation in database: {e}")
        
        # Create message object
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "intent": intent,
            "model_used": model_used,
            "cost": cost
        }
        
        # Add to in-memory storage
        self.conversations[conversation_id].append(message)
        
        # Update metadata
        self.conversation_metadata[conversation_id]["last_updated"] = datetime.now()
        self.conversation_metadata[conversation_id]["message_count"] += 1
        
        # Persist to database if enabled
        if self.use_database and self._conversation_repo:
            try:
                self._conversation_repo.add_message(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    intent=intent,
                    model_used=model_used,
                    cost=cost,
                    extra_metadata=metadata
                )
                self.db_session.commit()
            except Exception as e:
                logger.error(f"Failed to persist message to database: {e}")
                self.db_session.rollback()
        
        # Trim to max messages (keep most recent)
        if len(self.conversations[conversation_id]) > self.max_messages:
            self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_messages:]
    
    def get_history(
        self,
        conversation_id: str,
        max_messages: Optional[int] = None,
        from_database: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            conversation_id: Unique conversation identifier
            max_messages: Maximum messages to return (default: all available)
            from_database: If True, load from database instead of cache
            
        Returns:
            List of messages in chronological order
        """
        # Try to load from database if requested and available
        if from_database and self.use_database and self._conversation_repo:
            try:
                db_messages = self._conversation_repo.get_conversation_messages(conversation_id)
                # Convert database messages to dict format
                messages = []
                for msg in db_messages:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.created_at.isoformat(),
                        "metadata": msg.extra_metadata or {},
                        "intent": msg.intent,
                        "model_used": msg.model_used,
                        "cost": msg.cost
                    })
                
                # Update cache
                if messages:
                    self.conversations[conversation_id] = messages
                
                if max_messages is not None:
                    messages = messages[-max_messages:]
                
                return messages
            except Exception as e:
                logger.error(f"Failed to load conversation from database: {e}")
                # Fall back to in-memory
        
        # Return from in-memory cache
        if conversation_id not in self.conversations:
            return []
        
        messages = self.conversations[conversation_id]
        
        if max_messages is not None:
            messages = messages[-max_messages:]
        
        return messages
    
    def get_context_summary(self, conversation_id: str) -> str:
        """
        Get a text summary of the conversation context.
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            Formatted string with conversation history
        """
        history = self.get_history(conversation_id)
        
        if not history:
            return "No previous conversation history."
        
        summary_lines = ["Previous conversation:"]
        for msg in history:
            role_label = "User" if msg["role"] == "user" else "Agent"
            summary_lines.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(summary_lines)
    
    def clear_conversation(self, conversation_id: str) -> None:
        """
        Clear a specific conversation.
        
        Args:
            conversation_id: Unique conversation identifier
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
        if conversation_id in self.conversation_metadata:
            del self.conversation_metadata[conversation_id]
    
    def cleanup_old_conversations(self) -> int:
        """
        Remove conversations older than max_age_hours.
        
        Returns:
            Number of conversations removed
        """
        cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
        removed_count = 0
        
        conversation_ids = list(self.conversation_metadata.keys())
        for conv_id in conversation_ids:
            metadata = self.conversation_metadata[conv_id]
            if metadata["last_updated"] < cutoff_time:
                self.clear_conversation(conv_id)
                removed_count += 1
        
        return removed_count
    
    def get_conversation_count(self) -> int:
        """Get total number of active conversations."""
        return len(self.conversations)
    
    def get_message_count(self, conversation_id: str) -> int:
        """Get number of messages in a conversation."""
        if conversation_id not in self.conversations:
            return 0
        return len(self.conversations[conversation_id])


# Global conversation memory instance
_global_memory: Optional[ConversationMemory] = None

def get_conversation_memory() -> ConversationMemory:
    """
    Get the global conversation memory instance.
    Creates one if it doesn't exist.
    """
    global _global_memory
    if _global_memory is None:
        _global_memory = ConversationMemory()
    return _global_memory
