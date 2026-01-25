"""
Audit Repository

Data access layer for audit log operations.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database.models import AuditLog


class AuditRepository:
    """Repository for audit log operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_audit_log(
        self,
        event_type: str,
        event_category: str,
        description: str,
        user_id: Optional[int] = None,
        severity: str = "info",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        extra_metadata: Optional[dict] = None
    ) -> AuditLog:
        """
        Create an audit log entry.
        
        Args:
            event_type: Type of event
            event_category: Category of event
            description: Event description
            user_id: User ID (optional for system events)
            severity: Severity level
            ip_address: IP address
            user_agent: User agent string
            extra_metadata: Additional metadata
            
        Returns:
            Created audit log
        """
        audit_log = AuditLog(
            user_id=user_id,
            event_type=event_type,
            event_category=event_category,
            severity=severity,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_metadata=extra_metadata
        )
        self.db.add(audit_log)
        self.db.flush()
        return audit_log
    
    def get_user_audit_logs(
        self,
        user_id: int,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit logs for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of logs
            
        Returns:
            List of audit logs
        """
        return self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(desc(AuditLog.created_at)).limit(limit).all()
    
    def get_logs_by_type(
        self,
        event_type: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit logs by event type.
        
        Args:
            event_type: Event type
            limit: Maximum number of logs
            
        Returns:
            List of audit logs
        """
        return self.db.query(AuditLog).filter(
            AuditLog.event_type == event_type
        ).order_by(desc(AuditLog.created_at)).limit(limit).all()
