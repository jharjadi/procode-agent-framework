"""
API Key Repository

Handles database operations for API keys.
"""

from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database.models import APIKey


class APIKeyRepository:
    """Repository for API key database operations."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def get_by_id(self, key_id: UUID) -> Optional[APIKey]:
        """
        Get API key by ID.
        
        Args:
            key_id: API key UUID
            
        Returns:
            APIKey if found, None otherwise
        """
        return self.session.query(APIKey).filter(
            APIKey.id == key_id
        ).first()
    
    def get_by_hash(self, key_hash: str) -> Optional[APIKey]:
        """
        Get API key by hash.
        
        Args:
            key_hash: SHA-256 hash of the API key
            
        Returns:
            APIKey if found, None otherwise
        """
        return self.session.query(APIKey).filter(
            APIKey.key_hash == key_hash
        ).first()
    
    def get_by_organization(
        self,
        org_id: UUID,
        is_active: Optional[bool] = None,
        environment: Optional[str] = None
    ) -> List[APIKey]:
        """
        Get all API keys for an organization.
        
        Args:
            org_id: Organization UUID
            is_active: Filter by active status (None = all)
            environment: Filter by environment (None = all)
            
        Returns:
            List of API keys
        """
        query = self.session.query(APIKey).filter(
            APIKey.organization_id == org_id
        )
        
        if is_active is not None:
            query = query.filter(APIKey.is_active == is_active)
        
        if environment is not None:
            query = query.filter(APIKey.environment == environment)
        
        return query.order_by(APIKey.created_at.desc()).all()
    
    def create(
        self,
        org_id: UUID,
        key_hash: str,
        key_prefix: str,
        key_hint: str,
        name: str,
        environment: str,
        description: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        custom_rate_limit: Optional[int] = None,
        expires_in_days: Optional[int] = None
    ) -> APIKey:
        """
        Create a new API key.
        
        Args:
            org_id: Organization UUID
            key_hash: SHA-256 hash of the key
            key_prefix: Key prefix (pk_live_ or pk_test_)
            key_hint: Last 4 characters for display
            name: User-friendly name
            environment: "live" or "test"
            description: Optional description
            scopes: List of scopes (default: ["*"])
            custom_rate_limit: Custom rate limit override
            expires_in_days: Number of days until expiration
            
        Returns:
            Created API key
        """
        if scopes is None:
            scopes = ["*"]
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        api_key = APIKey(
            organization_id=org_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            key_hint=key_hint,
            name=name,
            environment=environment,
            description=description,
            scopes=scopes,
            custom_rate_limit=custom_rate_limit,
            expires_at=expires_at,
            is_active=True
        )
        
        self.session.add(api_key)
        self.session.commit()
        self.session.refresh(api_key)
        
        return api_key
    
    def update_last_used(self, key_id: UUID) -> None:
        """
        Update last_used_at timestamp.
        
        Args:
            key_id: API key UUID
        """
        api_key = self.get_by_id(key_id)
        
        if api_key:
            api_key.last_used_at = datetime.utcnow()
            api_key.last_request_at = datetime.utcnow()
            self.session.commit()
    
    def increment_request_count(self, key_id: UUID) -> None:
        """
        Increment total request count.
        
        Args:
            key_id: API key UUID
        """
        api_key = self.get_by_id(key_id)
        
        if api_key:
            api_key.total_requests += 1
            api_key.last_request_at = datetime.utcnow()
            self.session.commit()
    
    def revoke(
        self,
        key_id: UUID,
        reason: str,
        revoked_by: Optional[UUID] = None
    ) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: API key UUID
            reason: Reason for revocation
            revoked_by: UUID of user/admin who revoked the key
            
        Returns:
            True if revoked, False if not found
        """
        api_key = self.get_by_id(key_id)
        
        if not api_key:
            return False
        
        api_key.is_active = False
        api_key.revoked_at = datetime.utcnow()
        api_key.revoked_by = revoked_by
        api_key.revoked_reason = reason
        
        self.session.commit()
        
        return True
    
    def delete_expired(self) -> int:
        """
        Delete expired API keys.
        
        Returns:
            Number of keys deleted
        """
        now = datetime.utcnow()
        
        expired_keys = self.session.query(APIKey).filter(
            and_(
                APIKey.expires_at.isnot(None),
                APIKey.expires_at < now
            )
        ).all()
        
        count = len(expired_keys)
        
        for key in expired_keys:
            self.session.delete(key)
        
        self.session.commit()
        
        return count
    
    def is_valid(self, key_id: UUID) -> bool:
        """
        Check if API key is valid (active, not expired, not revoked).
        
        Args:
            key_id: API key UUID
            
        Returns:
            True if valid, False otherwise
        """
        api_key = self.get_by_id(key_id)
        
        if not api_key:
            return False
        
        # Check if active
        if not api_key.is_active:
            return False
        
        # Check if revoked
        if api_key.revoked_at is not None:
            return False
        
        # Check if expired
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return False
        
        return True
    
    def get_active_count(self, org_id: UUID) -> int:
        """
        Get count of active API keys for an organization.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Number of active keys
        """
        return self.session.query(APIKey).filter(
            and_(
                APIKey.organization_id == org_id,
                APIKey.is_active == True,
                APIKey.revoked_at.is_(None)
            )
        ).count()
    
    def update(
        self,
        key_id: UUID,
        **kwargs
    ) -> Optional[APIKey]:
        """
        Update API key fields.
        
        Args:
            key_id: API key UUID
            **kwargs: Fields to update
            
        Returns:
            Updated API key if found, None otherwise
        """
        api_key = self.get_by_id(key_id)
        
        if not api_key:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'name', 'description', 'scopes', 'custom_rate_limit',
            'is_active', 'expires_at'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(api_key, field):
                setattr(api_key, field, value)
        
        self.session.commit()
        self.session.refresh(api_key)
        
        return api_key
    
    def get_expiring_soon(self, days: int = 7) -> List[APIKey]:
        """
        Get API keys expiring within specified days.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of expiring API keys
        """
        now = datetime.utcnow()
        future = now + timedelta(days=days)
        
        return self.session.query(APIKey).filter(
            and_(
                APIKey.is_active == True,
                APIKey.expires_at.isnot(None),
                APIKey.expires_at.between(now, future)
            )
        ).all()
    
    def get_unused(self, days: int = 30) -> List[APIKey]:
        """
        Get API keys not used in specified days.
        
        Args:
            days: Number of days of inactivity
            
        Returns:
            List of unused API keys
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        return self.session.query(APIKey).filter(
            and_(
                APIKey.is_active == True,
                or_(
                    APIKey.last_used_at.is_(None),
                    APIKey.last_used_at < cutoff
                )
            )
        ).all()
    
    def get_statistics(self, org_id: UUID) -> Dict:
        """
        Get API key statistics for an organization.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Dictionary with statistics
        """
        all_keys = self.get_by_organization(org_id)
        
        active_keys = [k for k in all_keys if k.is_active and not k.revoked_at]
        revoked_keys = [k for k in all_keys if k.revoked_at]
        expired_keys = [k for k in all_keys if k.expires_at and k.expires_at < datetime.utcnow()]
        
        total_requests = sum(k.total_requests for k in all_keys)
        
        return {
            "total_keys": len(all_keys),
            "active_keys": len(active_keys),
            "revoked_keys": len(revoked_keys),
            "expired_keys": len(expired_keys),
            "total_requests": total_requests,
            "live_keys": len([k for k in active_keys if k.environment == "live"]),
            "test_keys": len([k for k in active_keys if k.environment == "test"]),
        }
