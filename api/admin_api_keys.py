"""
Admin API for API Key Management

Admin endpoints for managing organizations, API keys, and viewing usage statistics.
Requires admin scope for all endpoints.
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND
)

from security.api_key_service import APIKeyService
from security.api_key_exceptions import APIKeyError
from core.api_key_decorators import require_admin
from core.api_key_middleware import get_auth_context
from database.connection import get_db_session


# Pydantic models for request/response validation
class CreateOrganizationRequest(BaseModel):
    """Request model for creating an organization."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    email: str = Field(..., min_length=1, max_length=255)
    plan: str = Field(default="free", pattern=r'^(free|pro|enterprise)$')
    monthly_request_limit: int = Field(default=1000, ge=0)
    rate_limit_per_minute: int = Field(default=10, ge=1)
    max_api_keys: int = Field(default=2, ge=1)


class UpdateOrganizationRequest(BaseModel):
    """Request model for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, min_length=1, max_length=255)
    plan: Optional[str] = Field(None, pattern=r'^(free|pro|enterprise)$')
    is_active: Optional[bool] = None
    monthly_request_limit: Optional[int] = Field(None, ge=0)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1)
    max_api_keys: Optional[int] = Field(None, ge=1)


class CreateAPIKeyRequest(BaseModel):
    """Request model for creating an API key."""
    name: str = Field(..., min_length=1, max_length=255)
    environment: str = Field(default="test", pattern=r'^(live|test)$')
    description: Optional[str] = Field(None, max_length=1000)
    scopes: List[str] = Field(default=["*"])
    custom_rate_limit: Optional[int] = Field(None, ge=1)
    expires_in_days: Optional[int] = Field(None, ge=1)


# Admin endpoint handlers
@require_admin
async def create_organization(request: Request):
    """
    Create a new organization.
    
    POST /admin/organizations
    
    Request body:
    {
        "name": "Acme Corp",
        "slug": "acme",
        "email": "admin@acme.com",
        "plan": "pro",
        "monthly_request_limit": 100000,
        "rate_limit_per_minute": 60,
        "max_api_keys": 10
    }
    """
    try:
        # Parse request body
        body = await request.json()
        data = CreateOrganizationRequest(**body)
        
        # Get database session
        db_session = next(get_db_session())
        
        try:
            # Create API key service
            api_key_service = APIKeyService(session=db_session)
            
            # Create organization using repository
            from database.repositories.organization_repository import OrganizationRepository
            org_repo = OrganizationRepository(db_session)
            
            organization = org_repo.create(
                name=data.name,
                slug=data.slug,
                email=data.email,
                plan=data.plan,
                monthly_request_limit=data.monthly_request_limit,
                rate_limit_per_minute=data.rate_limit_per_minute,
                max_api_keys=data.max_api_keys
            )
            
            return JSONResponse(
                status_code=HTTP_201_CREATED,
                content={
                    "id": str(organization.id),
                    "name": organization.name,
                    "slug": organization.slug,
                    "email": organization.email,
                    "plan": organization.plan,
                    "is_active": organization.is_active,
                    "monthly_request_limit": organization.monthly_request_limit,
                    "rate_limit_per_minute": organization.rate_limit_per_minute,
                    "max_api_keys": organization.max_api_keys,
                    "created_at": organization.created_at.isoformat()
                }
            )
        finally:
            db_session.close()
    
    except APIKeyError as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.to_dict()
        )
    except Exception as e:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": "bad_request", "message": str(e)}
        )


@require_admin
async def list_organizations(request: Request):
    """
    List all organizations.
    
    GET /admin/organizations?limit=100&offset=0&is_active=true
    """
    try:
        # Get query parameters
        limit = int(request.query_params.get("limit", 100))
        offset = int(request.query_params.get("offset", 0))
        is_active = request.query_params.get("is_active")
        
        if is_active is not None:
            is_active = is_active.lower() == "true"
        
        # Get database session
        db_session = next(get_db_session())
        
        try:
            from database.repositories.organization_repository import OrganizationRepository
            org_repo = OrganizationRepository(db_session)
            
            organizations = org_repo.get_all(
                limit=limit,
                offset=offset,
                is_active=is_active
            )
            
            total = org_repo.count(is_active=is_active)
            
            return JSONResponse(
                status_code=HTTP_200_OK,
                content={
                    "organizations": [
                        {
                            "id": str(org.id),
                            "name": org.name,
                            "slug": org.slug,
                            "email": org.email,
                            "plan": org.plan,
                            "is_active": org.is_active,
                            "created_at": org.created_at.isoformat()
                        }
                        for org in organizations
                    ],
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
            )
        finally:
            db_session.close()
    
    except Exception as e:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": "bad_request", "message": str(e)}
        )


@require_admin
async def get_organization(request: Request):
    """
    Get organization by ID.
    
    GET /admin/organizations/{org_id}
    """
    try:
        org_id = UUID(request.path_params["org_id"])
        
        db_session = next(get_db_session())
        
        try:
            from database.repositories.organization_repository import OrganizationRepository
            org_repo = OrganizationRepository(db_session)
            
            organization = org_repo.get_by_id(org_id)
            
            if not organization:
                return JSONResponse(
                    status_code=HTTP_404_NOT_FOUND,
                    content={"error": "not_found", "message": "Organization not found"}
                )
            
            # Get API key count
            key_count = org_repo.get_api_key_count(org_id)
            
            return JSONResponse(
                status_code=HTTP_200_OK,
                content={
                    "id": str(organization.id),
                    "name": organization.name,
                    "slug": organization.slug,
                    "email": organization.email,
                    "plan": organization.plan,
                    "is_active": organization.is_active,
                    "monthly_request_limit": organization.monthly_request_limit,
                    "rate_limit_per_minute": organization.rate_limit_per_minute,
                    "max_api_keys": organization.max_api_keys,
                    "current_api_keys": key_count,
                    "created_at": organization.created_at.isoformat(),
                    "updated_at": organization.updated_at.isoformat()
                }
            )
        finally:
            db_session.close()
    
    except Exception as e:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": "bad_request", "message": str(e)}
        )


@require_admin
async def create_api_key(request: Request):
    """
    Create API key for an organization.
    
    POST /admin/organizations/{org_id}/keys
    """
    try:
        org_id = UUID(request.path_params["org_id"])
        
        # Parse request body
        body = await request.json()
        data = CreateAPIKeyRequest(**body)
        
        db_session = next(get_db_session())
        
        try:
            api_key_service = APIKeyService(session=db_session)
            
            key_data = api_key_service.create_key(
                org_id=org_id,
                name=data.name,
                environment=data.environment,
                description=data.description,
                scopes=data.scopes,
                custom_rate_limit=data.custom_rate_limit,
                expires_in_days=data.expires_in_days
            )
            
            return JSONResponse(
                status_code=HTTP_201_CREATED,
                content=key_data
            )
        finally:
            db_session.close()
    
    except APIKeyError as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.to_dict()
        )
    except Exception as e:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": "bad_request", "message": str(e)}
        )


@require_admin
async def list_api_keys(request: Request):
    """
    List API keys for an organization.
    
    GET /admin/organizations/{org_id}/keys
    """
    try:
        org_id = UUID(request.path_params["org_id"])
        
        db_session = next(get_db_session())
        
        try:
            api_key_service = APIKeyService(session=db_session)
            keys = api_key_service.list_keys(org_id)
            
            return JSONResponse(
                status_code=HTTP_200_OK,
                content={"keys": keys}
            )
        finally:
            db_session.close()
    
    except Exception as e:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": "bad_request", "message": str(e)}
        )


@require_admin
async def revoke_api_key(request: Request):
    """
    Revoke an API key.
    
    DELETE /admin/organizations/{org_id}/keys/{key_id}
    """
    try:
        org_id = UUID(request.path_params["org_id"])
        key_id = UUID(request.path_params["key_id"])
        
        # Get reason from request body
        body = await request.json()
        reason = body.get("reason", "Revoked by admin")
        
        db_session = next(get_db_session())
        
        try:
            api_key_service = APIKeyService(session=db_session)
            
            # Get admin user ID from auth context
            auth_context = get_auth_context(request)
            revoked_by = auth_context.get("key_id") if auth_context else None
            
            api_key_service.revoke_key(
                key_id=key_id,
                reason=reason,
                revoked_by=revoked_by
            )
            
            return JSONResponse(
                status_code=HTTP_200_OK,
                content={"message": "API key revoked successfully"}
            )
        finally:
            db_session.close()
    
    except APIKeyError as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.to_dict()
        )
    except Exception as e:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": "bad_request", "message": str(e)}
        )


@require_admin
async def get_usage_stats(request: Request):
    """
    Get usage statistics for an organization.
    
    GET /admin/organizations/{org_id}/usage?year=2026&month=1
    """
    try:
        org_id = UUID(request.path_params["org_id"])
        
        # Get query parameters
        year = int(request.query_params.get("year", datetime.utcnow().year))
        month = int(request.query_params.get("month", datetime.utcnow().month))
        
        db_session = next(get_db_session())
        
        try:
            api_key_service = APIKeyService(session=db_session)
            stats = api_key_service.get_usage_stats(org_id, year, month)
            
            return JSONResponse(
                status_code=HTTP_200_OK,
                content=stats
            )
        finally:
            db_session.close()
    
    except Exception as e:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": "bad_request", "message": str(e)}
        )


# Define admin routes
admin_routes = [
    Route("/admin/organizations", create_organization, methods=["POST"]),
    Route("/admin/organizations", list_organizations, methods=["GET"]),
    Route("/admin/organizations/{org_id}", get_organization, methods=["GET"]),
    Route("/admin/organizations/{org_id}/keys", create_api_key, methods=["POST"]),
    Route("/admin/organizations/{org_id}/keys", list_api_keys, methods=["GET"]),
    Route("/admin/organizations/{org_id}/keys/{key_id}", revoke_api_key, methods=["DELETE"]),
    Route("/admin/organizations/{org_id}/usage", get_usage_stats, methods=["GET"]),
]
