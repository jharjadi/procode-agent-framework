"""
Organization Repository

Handles database operations for organizations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.models import Organization


class OrganizationRepository:
    """Repository for organization database operations."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def get_by_id(self, org_id: UUID) -> Optional[Organization]:
        """
        Get organization by ID.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Organization if found, None otherwise
        """
        return self.session.query(Organization).filter(
            Organization.id == org_id
        ).first()
    
    def get_by_slug(self, slug: str) -> Optional[Organization]:
        """
        Get organization by slug.
        
        Args:
            slug: Organization slug (unique identifier)
            
        Returns:
            Organization if found, None otherwise
        """
        return self.session.query(Organization).filter(
            Organization.slug == slug
        ).first()
    
    def get_by_email(self, email: str) -> Optional[Organization]:
        """
        Get organization by email.
        
        Args:
            email: Organization email
            
        Returns:
            Organization if found, None otherwise
        """
        return self.session.query(Organization).filter(
            Organization.email == email
        ).first()
    
    def create(
        self,
        name: str,
        slug: str,
        email: str,
        plan: str = "free",
        monthly_request_limit: int = 1000,
        rate_limit_per_minute: int = 10,
        max_api_keys: int = 2,
        is_active: bool = True
    ) -> Organization:
        """
        Create a new organization.
        
        Args:
            name: Organization name
            slug: Unique slug identifier
            email: Organization email
            plan: Subscription plan (free, pro, enterprise)
            monthly_request_limit: Monthly API request limit
            rate_limit_per_minute: Rate limit per minute
            max_api_keys: Maximum number of API keys allowed
            is_active: Whether organization is active
            
        Returns:
            Created organization
            
        Raises:
            IntegrityError: If slug or email already exists
        """
        org = Organization(
            name=name,
            slug=slug,
            email=email,
            plan=plan,
            monthly_request_limit=monthly_request_limit,
            rate_limit_per_minute=rate_limit_per_minute,
            max_api_keys=max_api_keys,
            is_active=is_active
        )
        
        self.session.add(org)
        self.session.commit()
        self.session.refresh(org)
        
        return org
    
    def update(
        self,
        org_id: UUID,
        **kwargs
    ) -> Optional[Organization]:
        """
        Update organization fields.
        
        Args:
            org_id: Organization UUID
            **kwargs: Fields to update (name, email, plan, limits, etc.)
            
        Returns:
            Updated organization if found, None otherwise
        """
        org = self.get_by_id(org_id)
        
        if not org:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'name', 'email', 'plan', 'is_active',
            'monthly_request_limit', 'rate_limit_per_minute', 'max_api_keys'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(org, field):
                setattr(org, field, value)
        
        org.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(org)
        
        return org
    
    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[bool] = None
    ) -> List[Organization]:
        """
        Get all organizations with pagination.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            is_active: Filter by active status (None = all)
            
        Returns:
            List of organizations
        """
        query = self.session.query(Organization)
        
        if is_active is not None:
            query = query.filter(Organization.is_active == is_active)
        
        return query.order_by(Organization.created_at.desc()).limit(limit).offset(offset).all()
    
    def count(self, is_active: Optional[bool] = None) -> int:
        """
        Count organizations.
        
        Args:
            is_active: Filter by active status (None = all)
            
        Returns:
            Number of organizations
        """
        query = self.session.query(Organization)
        
        if is_active is not None:
            query = query.filter(Organization.is_active == is_active)
        
        return query.count()
    
    def deactivate(self, org_id: UUID) -> bool:
        """
        Deactivate an organization.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            True if deactivated, False if not found
        """
        org = self.get_by_id(org_id)
        
        if not org:
            return False
        
        org.is_active = False
        org.updated_at = datetime.utcnow()
        self.session.commit()
        
        return True
    
    def activate(self, org_id: UUID) -> bool:
        """
        Activate an organization.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            True if activated, False if not found
        """
        org = self.get_by_id(org_id)
        
        if not org:
            return False
        
        org.is_active = True
        org.updated_at = datetime.utcnow()
        self.session.commit()
        
        return True
    
    def delete(self, org_id: UUID) -> bool:
        """
        Delete an organization (hard delete).
        
        Args:
            org_id: Organization UUID
            
        Returns:
            True if deleted, False if not found
            
        Note:
            This will cascade delete all API keys and usage records.
            Use with caution!
        """
        org = self.get_by_id(org_id)
        
        if not org:
            return False
        
        self.session.delete(org)
        self.session.commit()
        
        return True
    
    def get_api_key_count(self, org_id: UUID) -> int:
        """
        Get number of API keys for an organization.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Number of API keys
        """
        org = self.get_by_id(org_id)
        
        if not org:
            return 0
        
        return len(org.api_keys)
    
    def can_create_api_key(self, org_id: UUID) -> bool:
        """
        Check if organization can create more API keys.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            True if can create more keys, False otherwise
        """
        org = self.get_by_id(org_id)
        
        if not org or not org.is_active:
            return False
        
        current_count = self.get_api_key_count(org_id)
        return current_count < org.max_api_keys
