"""
Tests for API Key Service

Tests the complete API key service including validation, creation,
revocation, and usage tracking.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.connection import Base
from database.models import Organization, APIKey
from security.api_key_service import APIKeyService
from security.api_key_generator import APIKeyGenerator
from security.api_key_exceptions import (
    InvalidAPIKeyError,
    ExpiredAPIKeyError,
    RevokedAPIKeyError,
    OrganizationInactiveError,
    APIKeyLimitExceededError,
    MonthlyQuotaExceededError,
    InsufficientScopeError
)


@pytest.fixture
def db_session():
    """Create in-memory database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def api_key_service(db_session):
    """Create API key service instance."""
    return APIKeyService(db_session)


@pytest.fixture
def test_organization(db_session):
    """Create test organization."""
    org = Organization(
        name="Test Organization",
        slug="test-org",
        email="test@example.com",
        plan="free",
        is_active=True,
        monthly_request_limit=1000,
        rate_limit_per_minute=10,
        max_api_keys=2
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


class TestAPIKeyServiceValidation:
    """Test API key validation."""
    
    def test_validate_key_success(self, api_key_service, test_organization):
        """Test successful key validation."""
        # Create a key
        key_data = api_key_service.create_key(
            org_id=test_organization.id,
            name="Test Key",
            environment="test"
        )
        
        # Validate the key
        context = api_key_service.validate_key(key_data["full_key"])
        
        assert context["organization_id"] == test_organization.id
        assert context["environment"] == "test"
        assert context["scopes"] == ["*"]
        assert context["rate_limit"] == 10
    
    def test_validate_key_invalid_format(self, api_key_service):
        """Test validation with invalid key format."""
        with pytest.raises(InvalidAPIKeyError, match="Invalid API key format"):
            api_key_service.validate_key("invalid_key")
    
    def test_validate_key_not_found(self, api_key_service):
        """Test validation with non-existent key."""
        # Generate a valid format key that doesn't exist in database
        fake_key = APIKeyGenerator.generate_key("test")["full_key"]
        
        with pytest.raises(InvalidAPIKeyError, match="Invalid API key"):
            api_key_service.validate_key(fake_key)
    
    def test_validate_key_inactive_organization(self, api_key_service, test_organization, db_session):
        """Test validation with inactive organization."""
        # Create a key
        key_data = api_key_service.create_key(
            org_id=test_organization.id,
            name="Test Key",
            environment="test"
        )
        
        # Deactivate organization
        test_organization.is_active = False
        db_session.commit()
        
        # Try to validate
        with pytest.raises(OrganizationInactiveError):
            api_key_service.validate_key(key_data["full_key"])
    
    def test_validate_key_revoked(self, api_key_service, test_organization):
        """Test validation with revoked key."""
        # Create and revoke a key
        key_data = api_key_service.create_key(
            org_id=test_organization.id,
            name="Test Key",
            environment="test"
        )
        
        api_key_service.revoke_key(
            key_id=key_data["id"],
            reason="Testing revocation"
        )
        
        # Try to validate
        with pytest.raises(RevokedAPIKeyError):
            api_key_service.validate_key(key_data["full_key"])


class TestAPIKeyServiceCreation:
    """Test API key creation."""
    
    def test_create_key_success(self, api_key_service, test_organization):
        """Test successful key creation."""
        key_data = api_key_service.create_key(
            org_id=test_organization.id,
            name="Test Key",
            environment="live",
            description="Test description",
            scopes=["chat", "agents"]
        )
        
        assert "full_key" in key_data
        assert key_data["full_key"].startswith("pk_live_")
        assert key_data["name"] == "Test Key"
        assert key_data["environment"] == "live"
        assert key_data["scopes"] == ["chat", "agents"]
    
    def test_create_key_with_expiration(self, api_key_service, test_organization):
        """Test key creation with expiration."""
        key_data = api_key_service.create_key(
            org_id=test_organization.id,
            name="Expiring Key",
            environment="test",
            expires_in_days=30
        )
        
        assert key_data["expires_at"] is not None
    
    def test_create_key_limit_exceeded(self, api_key_service, test_organization):
        """Test key creation when limit is exceeded."""
        # Create max number of keys
        for i in range(test_organization.max_api_keys):
            api_key_service.create_key(
                org_id=test_organization.id,
                name=f"Key {i}",
                environment="test"
            )
        
        # Try to create one more
        with pytest.raises(APIKeyLimitExceededError):
            api_key_service.create_key(
                org_id=test_organization.id,
                name="Extra Key",
                environment="test"
            )
    
    def test_create_key_inactive_organization(self, api_key_service, test_organization, db_session):
        """Test key creation for inactive organization."""
        test_organization.is_active = False
        db_session.commit()
        
        with pytest.raises(OrganizationInactiveError):
            api_key_service.create_key(
                org_id=test_organization.id,
                name="Test Key",
                environment="test"
            )


class TestAPIKeyServiceRevocation:
    """Test API key revocation."""
    
    def test_revoke_key_success(self, api_key_service, test_organization):
        """Test successful key revocation."""
        # Create a key
        key_data = api_key_service.create_key(
            org_id=test_organization.id,
            name="Test Key",
            environment="test"
        )
        
        # Revoke it
        success = api_key_service.revoke_key(
            key_id=key_data["id"],
            reason="Testing"
        )
        
        assert success is True
        
        # Verify it's revoked
        with pytest.raises(RevokedAPIKeyError):
            api_key_service.validate_key(key_data["full_key"])
    
    def test_revoke_key_not_found(self, api_key_service):
        """Test revoking non-existent key."""
        with pytest.raises(InvalidAPIKeyError):
            api_key_service.revoke_key(
                key_id=uuid4(),
                reason="Testing"
            )


class TestAPIKeyServiceListing:
    """Test API key listing."""
    
    def test_list_keys(self, api_key_service, test_organization):
        """Test listing organization keys."""
        # Create multiple keys
        key1 = api_key_service.create_key(
            org_id=test_organization.id,
            name="Key 1",
            environment="test"
        )
        
        key2 = api_key_service.create_key(
            org_id=test_organization.id,
            name="Key 2",
            environment="live"
        )
        
        # List keys
        keys = api_key_service.list_keys(test_organization.id)
        
        assert len(keys) == 2
        assert all("full_key" not in key for key in keys)  # Full keys not exposed
        assert all("key_hint" in key for key in keys)


class TestAPIKeyServiceUsageTracking:
    """Test usage tracking."""
    
    def test_track_usage(self, api_key_service, test_organization):
        """Test tracking API usage."""
        # Create a key
        key_data = api_key_service.create_key(
            org_id=test_organization.id,
            name="Test Key",
            environment="test"
        )
        
        # Track usage
        api_key_service.track_usage(
            key_id=key_data["id"],
            org_id=test_organization.id,
            endpoint="/api/chat",
            method="POST",
            status_code=200,
            response_time_ms=150,
            tokens_used=100,
            cost_usd=0.002
        )
        
        # Get usage stats
        now = datetime.utcnow()
        stats = api_key_service.get_usage_stats(
            org_id=test_organization.id,
            year=now.year,
            month=now.month
        )
        
        assert stats["total_requests"] == 1
        assert stats["total_tokens"] == 100
        assert stats["total_cost_usd"] == 0.002


class TestAPIKeyServiceQuota:
    """Test quota checking."""
    
    def test_check_monthly_quota_within_limit(self, api_key_service, test_organization):
        """Test quota check when within limit."""
        quota_info = api_key_service.check_monthly_quota(test_organization.id)
        
        assert quota_info["current_usage"] == 0
        assert quota_info["quota"] == 1000
        assert quota_info["remaining"] == 1000


class TestAPIKeyServiceScopes:
    """Test scope checking."""
    
    def test_check_scope_wildcard(self, api_key_service):
        """Test scope check with wildcard."""
        result = api_key_service.check_scope(["*"], "any_scope")
        assert result is True
    
    def test_check_scope_specific(self, api_key_service):
        """Test scope check with specific scope."""
        result = api_key_service.check_scope(["chat", "agents"], "chat")
        assert result is True
    
    def test_check_scope_insufficient(self, api_key_service):
        """Test scope check with insufficient scope."""
        with pytest.raises(InsufficientScopeError):
            api_key_service.check_scope(["chat"], "admin")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
