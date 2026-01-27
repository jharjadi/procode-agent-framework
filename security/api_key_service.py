"""
API Key Service

Orchestrates all API key authentication components including:
- Key generation and validation
- Organization management
- Usage tracking
- Rate limiting
- Audit logging

This is the main service layer that brings together all Phase 2 components.
"""

from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from security.api_key_generator import APIKeyGenerator
from security.api_key_hasher import APIKeyHasher
from security.api_key_exceptions import (
    InvalidAPIKeyError,
    ExpiredAPIKeyError,
    RevokedAPIKeyError,
    OrganizationInactiveError,
    APIKeyLimitExceededError,
    MonthlyQuotaExceededError,
    InsufficientScopeError,
    APIKeyGenerationError,
    APIKeyStorageError
)
from database.repositories.organization_repository import OrganizationRepository
from database.repositories.api_key_repository import APIKeyRepository
from database.repositories.usage_repository import UsageRepository
from security.audit_logger import AuditLogger


class APIKeyService:
    """
    Service for API key authentication and management.
    
    Orchestrates all API key operations including validation, creation,
    revocation, and usage tracking.
    """
    
    def __init__(
        self,
        session: Session,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize API key service.
        
        Args:
            session: Database session
            audit_logger: Optional audit logger for security events
        """
        self.session = session
        self.org_repo = OrganizationRepository(session)
        self.key_repo = APIKeyRepository(session)
        self.usage_repo = UsageRepository(session)
        self.audit_logger = audit_logger
    
    def validate_key(self, api_key: str) -> Dict:
        """
        Validate an API key and return authentication context.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Dictionary with authentication context:
            {
                "key_id": UUID,
                "organization_id": UUID,
                "organization": Organization object,
                "api_key": APIKey object,
                "scopes": list of scopes,
                "rate_limit": int,
                "environment": "live" or "test"
            }
            
        Raises:
            InvalidAPIKeyError: If key format is invalid or not found
            ExpiredAPIKeyError: If key has expired
            RevokedAPIKeyError: If key has been revoked
            OrganizationInactiveError: If organization is inactive
            
        Example:
            >>> context = service.validate_key("pk_live_abc123...")
            >>> context["organization_id"]
            UUID('...')
        """
        # Validate key format
        if not APIKeyGenerator.validate_key_format(api_key):
            if self.audit_logger:
                self.audit_logger.log_security_event(
                    "api_key_invalid_format",
                    "Invalid API key format",
                    severity="warning"
                )
            raise InvalidAPIKeyError("Invalid API key format")
        
        # Hash the key
        key_hash = APIKeyHasher.hash_key(api_key)
        
        # Get key from database
        api_key_obj = self.key_repo.get_by_hash(key_hash)
        
        if not api_key_obj:
            if self.audit_logger:
                self.audit_logger.log_security_event(
                    "api_key_not_found",
                    "API key not found in database",
                    severity="warning"
                )
            raise InvalidAPIKeyError("Invalid API key")
        
        # Check if key is active
        if not api_key_obj.is_active:
            if self.audit_logger:
                self.audit_logger.log_security_event(
                    "api_key_inactive",
                    f"Inactive API key used: {api_key_obj.id}",
                    severity="warning"
                )
            raise InvalidAPIKeyError("API key is inactive")
        
        # Check if key is revoked
        if api_key_obj.revoked_at:
            if self.audit_logger:
                self.audit_logger.log_security_event(
                    "api_key_revoked",
                    f"Revoked API key used: {api_key_obj.id}",
                    severity="warning"
                )
            raise RevokedAPIKeyError(
                revoked_at=api_key_obj.revoked_at.isoformat(),
                reason=api_key_obj.revoked_reason
            )
        
        # Check if key has expired
        if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
            if self.audit_logger:
                self.audit_logger.log_security_event(
                    "api_key_expired",
                    f"Expired API key used: {api_key_obj.id}",
                    severity="warning"
                )
            raise ExpiredAPIKeyError(
                expires_at=api_key_obj.expires_at.isoformat()
            )
        
        # Get organization
        organization = self.org_repo.get_by_id(api_key_obj.organization_id)
        
        if not organization:
            raise InvalidAPIKeyError("Organization not found")
        
        # Check if organization is active
        if not organization.is_active:
            if self.audit_logger:
                self.audit_logger.log_security_event(
                    "organization_inactive",
                    f"Inactive organization: {organization.id}",
                    severity="warning"
                )
            raise OrganizationInactiveError()
        
        # Update last used timestamp (async in production)
        self.key_repo.update_last_used(api_key_obj.id)
        
        # Log successful authentication
        if self.audit_logger:
            self.audit_logger.log_security_event(
                "api_key_authenticated",
                f"API key authenticated: {api_key_obj.id}",
                severity="info"
            )
        
        # Return authentication context
        return {
            "key_id": api_key_obj.id,
            "organization_id": organization.id,
            "organization": organization,
            "api_key": api_key_obj,
            "scopes": api_key_obj.scopes,
            "rate_limit": api_key_obj.custom_rate_limit or organization.rate_limit_per_minute,
            "environment": api_key_obj.environment,
            "monthly_limit": organization.monthly_request_limit
        }
    
    def create_key(
        self,
        org_id: UUID,
        name: str,
        environment: str = "test",
        description: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        custom_rate_limit: Optional[int] = None,
        expires_in_days: Optional[int] = None
    ) -> Dict:
        """
        Create a new API key for an organization.
        
        Args:
            org_id: Organization UUID
            name: User-friendly name for the key
            environment: "live" or "test"
            description: Optional description
            scopes: List of scopes (default: ["*"])
            custom_rate_limit: Custom rate limit override
            expires_in_days: Number of days until expiration
            
        Returns:
            Dictionary with key data including full_key (show once!)
            
        Raises:
            InvalidAPIKeyError: If organization not found
            OrganizationInactiveError: If organization is inactive
            APIKeyLimitExceededError: If organization has reached key limit
            APIKeyGenerationError: If key generation fails
            APIKeyStorageError: If key storage fails
        """
        # Get organization
        organization = self.org_repo.get_by_id(org_id)
        
        if not organization:
            raise InvalidAPIKeyError("Organization not found")
        
        if not organization.is_active:
            raise OrganizationInactiveError()
        
        # Check if organization can create more keys
        if not self.org_repo.can_create_api_key(org_id):
            current_count = self.org_repo.get_api_key_count(org_id)
            raise APIKeyLimitExceededError(
                current_count=current_count,
                max_keys=organization.max_api_keys
            )
        
        # Generate key
        try:
            key_data = APIKeyGenerator.generate_key(environment)
        except Exception as e:
            if self.audit_logger:
                self.audit_logger.log_security_event(
                    "api_key_generation_failed",
                    f"Failed to generate API key: {str(e)}",
                    severity="error"
                )
            raise APIKeyGenerationError(f"Failed to generate key: {str(e)}")
        
        # Store key in database
        try:
            api_key = self.key_repo.create(
                org_id=org_id,
                key_hash=key_data["key_hash"],
                key_prefix=key_data["key_prefix"],
                key_hint=key_data["key_hint"],
                name=name,
                environment=environment,
                description=description,
                scopes=scopes,
                custom_rate_limit=custom_rate_limit,
                expires_in_days=expires_in_days
            )
        except Exception as e:
            if self.audit_logger:
                self.audit_logger.log_security_event(
                    "api_key_storage_failed",
                    f"Failed to store API key: {str(e)}",
                    severity="error"
                )
            raise APIKeyStorageError(f"Failed to store key: {str(e)}")
        
        # Log key creation
        if self.audit_logger:
            self.audit_logger.log_security_event(
                "api_key_created",
                f"API key created: {api_key.id} for org: {org_id}",
                severity="info"
            )
        
        # Return key data (including full key - show once!)
        return {
            "id": api_key.id,
            "full_key": key_data["full_key"],  # SHOW ONCE!
            "key_hint": key_data["key_hint"],
            "key_prefix": key_data["key_prefix"],
            "name": name,
            "environment": environment,
            "scopes": api_key.scopes,
            "created_at": api_key.created_at.isoformat(),
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None
        }
    
    def revoke_key(
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
            True if revoked successfully
            
        Raises:
            InvalidAPIKeyError: If key not found
        """
        success = self.key_repo.revoke(key_id, reason, revoked_by)
        
        if not success:
            raise InvalidAPIKeyError("API key not found")
        
        # Log revocation
        if self.audit_logger:
            self.audit_logger.log_security_event(
                "api_key_revoked",
                f"API key revoked: {key_id}. Reason: {reason}",
                severity="info"
            )
        
        return True
    
    def list_keys(self, org_id: UUID) -> List[Dict]:
        """
        List all API keys for an organization.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            List of API key dictionaries (without full keys)
        """
        keys = self.key_repo.get_by_organization(org_id)
        
        return [
            {
                "id": key.id,
                "name": key.name,
                "key_hint": key.key_hint,
                "key_prefix": key.key_prefix,
                "environment": key.environment,
                "is_active": key.is_active,
                "scopes": key.scopes,
                "created_at": key.created_at.isoformat(),
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "revoked_at": key.revoked_at.isoformat() if key.revoked_at else None,
                "total_requests": key.total_requests
            }
            for key in keys
        ]
    
    def track_usage(
        self,
        key_id: UUID,
        org_id: UUID,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: Optional[int] = None,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None
    ) -> None:
        """
        Track API key usage.
        
        Args:
            key_id: API key UUID
            org_id: Organization UUID
            endpoint: API endpoint called
            method: HTTP method
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            tokens_used: Number of tokens used
            cost_usd: Cost in USD
            ip_address: Client IP address
            user_agent: Client user agent
            error_message: Error message if any
            error_code: Error code if any
        """
        self.usage_repo.create(
            api_key_id=key_id,
            organization_id=org_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message,
            error_code=error_code
        )
        
        # Increment request count
        self.key_repo.increment_request_count(key_id)
    
    def get_usage_stats(
        self,
        org_id: UUID,
        year: int,
        month: int
    ) -> Dict:
        """
        Get usage statistics for an organization.
        
        Args:
            org_id: Organization UUID
            year: Year
            month: Month (1-12)
            
        Returns:
            Dictionary with usage statistics
        """
        return self.usage_repo.get_summary(org_id, year, month)
    
    def check_monthly_quota(self, org_id: UUID) -> Dict:
        """
        Check if organization has exceeded monthly quota.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Dictionary with quota information
            
        Raises:
            MonthlyQuotaExceededError: If quota exceeded
        """
        organization = self.org_repo.get_by_id(org_id)
        
        if not organization:
            raise InvalidAPIKeyError("Organization not found")
        
        current_usage = self.usage_repo.get_monthly_usage(org_id)
        quota = organization.monthly_request_limit
        
        if current_usage >= quota:
            raise MonthlyQuotaExceededError(
                current_usage=current_usage,
                quota=quota
            )
        
        return {
            "current_usage": current_usage,
            "quota": quota,
            "remaining": quota - current_usage,
            "percentage_used": (current_usage / quota * 100) if quota > 0 else 0
        }
    
    def check_scope(self, api_key_scopes: List[str], required_scope: str) -> bool:
        """
        Check if API key has required scope.
        
        Args:
            api_key_scopes: List of scopes the key has
            required_scope: Required scope
            
        Returns:
            True if key has required scope
            
        Raises:
            InsufficientScopeError: If scope is missing
        """
        # Wildcard scope grants all access
        if "*" in api_key_scopes:
            return True
        
        # Check if required scope is in key's scopes
        if required_scope in api_key_scopes:
            return True
        
        raise InsufficientScopeError(
            required_scope=required_scope,
            available_scopes=api_key_scopes
        )
