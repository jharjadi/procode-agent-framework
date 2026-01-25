"""
Conversation memory module for storing and retrieving conversation history.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os

class ConversationMemory:
    """
    Manages conversation history for multi-turn dialogues.
    Stores messages in memory with conversation ID tracking.
    """
    
    def __init__(self, max_messages: int = None, max_age_hours: int = 24):
        """
        Initialize conversation memory.
        
        Args:
            max_messages: Maximum messages to keep per conversation (default: 10)
            max_age_hours: Maximum age of conversations in hours (default: 24)
        """
        if max_messages is None:
            max_messages = int(os.getenv("CONVERSATION_WINDOW_SIZE", "10"))
        
        self.max_messages = max_messages
        self.max_age_hours = max_age_hours
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.conversation_metadata: Dict[str, Dict[str, Any]] = {}
    
    def add_message(
        self, 
        conversation_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to conversation history.
        
        Args:
            conversation_id: Unique conversation identifier
            role: Message role ('user' or 'agent')
            content: Message content
            metadata: Optional metadata (intent, tool_calls, etc.)
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            self.conversation_metadata[conversation_id] = {
                "created_at": datetime.now(),
                "last_updated": datetime.now(),
                "message_count": 0
            }
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversations[conversation_id].append(message)
        
        # Update metadata
        self.conversation_metadata[conversation_id]["last_updated"] = datetime.now()
        self.conversation_metadata[conversation_id]["message_count"] += 1
        
        # Trim to max messages (keep most recent)
        if len(self.conversations[conversation_id]) > self.max_messages:
            self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_messages:]
    
    def get_history(
        self, 
        conversation_id: str, 
        max_messages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            conversation_id: Unique conversation identifier
            max_messages: Maximum messages to return (default: all available)
            
        Returns:
            List of messages in chronological order
        """
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
