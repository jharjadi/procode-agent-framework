"""
Usage Repository

Handles database operations for API key usage tracking.
"""

from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract

from database.models import APIKeyUsage


class UsageRepository:
    """Repository for API key usage tracking operations."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create(
        self,
        api_key_id: UUID,
        organization_id: UUID,
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
    ) -> APIKeyUsage:
        """
        Create a new usage record.
        
        Args:
            api_key_id: API key UUID
            organization_id: Organization UUID
            endpoint: API endpoint called
            method: HTTP method (GET, POST, etc.)
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            tokens_used: Number of tokens used
            cost_usd: Cost in USD
            ip_address: Client IP address
            user_agent: Client user agent
            error_message: Error message if any
            error_code: Error code if any
            
        Returns:
            Created usage record
        """
        usage = APIKeyUsage(
            api_key_id=api_key_id,
            organization_id=organization_id,
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
        
        self.session.add(usage)
        self.session.commit()
        self.session.refresh(usage)
        
        return usage
    
    def get_by_key(
        self,
        key_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[APIKeyUsage]:
        """
        Get usage records for an API key.
        
        Args:
            key_id: API key UUID
            start_date: Start date filter (inclusive)
            end_date: End date filter (inclusive)
            limit: Maximum number of records
            
        Returns:
            List of usage records
        """
        query = self.session.query(APIKeyUsage).filter(
            APIKeyUsage.api_key_id == key_id
        )
        
        if start_date:
            query = query.filter(APIKeyUsage.timestamp >= start_date)
        
        if end_date:
            query = query.filter(APIKeyUsage.timestamp <= end_date)
        
        return query.order_by(APIKeyUsage.timestamp.desc()).limit(limit).all()
    
    def get_by_organization(
        self,
        org_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[APIKeyUsage]:
        """
        Get usage records for an organization.
        
        Args:
            org_id: Organization UUID
            start_date: Start date filter (inclusive)
            end_date: End date filter (inclusive)
            limit: Maximum number of records
            
        Returns:
            List of usage records
        """
        query = self.session.query(APIKeyUsage).filter(
            APIKeyUsage.organization_id == org_id
        )
        
        if start_date:
            query = query.filter(APIKeyUsage.timestamp >= start_date)
        
        if end_date:
            query = query.filter(APIKeyUsage.timestamp <= end_date)
        
        return query.order_by(APIKeyUsage.timestamp.desc()).limit(limit).all()
    
    def get_summary(
        self,
        org_id: UUID,
        year: int,
        month: int
    ) -> Dict:
        """
        Get usage summary for a specific month.
        
        Args:
            org_id: Organization UUID
            year: Year (e.g., 2026)
            month: Month (1-12)
            
        Returns:
            Dictionary with usage statistics
        """
        # Calculate date range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Query usage records
        records = self.session.query(APIKeyUsage).filter(
            and_(
                APIKeyUsage.organization_id == org_id,
                APIKeyUsage.timestamp >= start_date,
                APIKeyUsage.timestamp < end_date
            )
        ).all()
        
        # Calculate statistics
        total_requests = len(records)
        total_tokens = sum(r.tokens_used for r in records)
        total_cost = sum(r.cost_usd for r in records)
        
        successful_requests = len([r for r in records if 200 <= r.status_code < 300])
        failed_requests = len([r for r in records if r.status_code >= 400])
        
        # Calculate average response time
        response_times = [r.response_time_ms for r in records if r.response_time_ms]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Group by endpoint
        endpoint_stats = {}
        for record in records:
            if record.endpoint not in endpoint_stats:
                endpoint_stats[record.endpoint] = {
                    "count": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            endpoint_stats[record.endpoint]["count"] += 1
            endpoint_stats[record.endpoint]["tokens"] += record.tokens_used
            endpoint_stats[record.endpoint]["cost"] += record.cost_usd
        
        return {
            "period": f"{year}-{month:02d}",
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "avg_response_time_ms": round(avg_response_time, 2),
            "endpoints": endpoint_stats
        }
    
    def get_daily_stats(
        self,
        org_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Get daily usage statistics.
        
        Args:
            org_id: Organization UUID
            start_date: Start date
            end_date: End date
            
        Returns:
            List of daily statistics
        """
        # Query with grouping by date
        results = self.session.query(
            func.date(APIKeyUsage.timestamp).label('date'),
            func.count(APIKeyUsage.id).label('requests'),
            func.sum(APIKeyUsage.tokens_used).label('tokens'),
            func.sum(APIKeyUsage.cost_usd).label('cost'),
            func.avg(APIKeyUsage.response_time_ms).label('avg_response_time')
        ).filter(
            and_(
                APIKeyUsage.organization_id == org_id,
                APIKeyUsage.timestamp >= start_date,
                APIKeyUsage.timestamp <= end_date
            )
        ).group_by(
            func.date(APIKeyUsage.timestamp)
        ).order_by(
            func.date(APIKeyUsage.timestamp)
        ).all()
        
        return [
            {
                "date": str(r.date),
                "requests": r.requests,
                "tokens": r.tokens or 0,
                "cost_usd": round(r.cost or 0.0, 4),
                "avg_response_time_ms": round(r.avg_response_time or 0.0, 2)
            }
            for r in results
        ]
    
    def get_endpoint_stats(
        self,
        org_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get statistics grouped by endpoint.
        
        Args:
            org_id: Organization UUID
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of endpoint statistics
        """
        query = self.session.query(
            APIKeyUsage.endpoint,
            func.count(APIKeyUsage.id).label('requests'),
            func.sum(APIKeyUsage.tokens_used).label('tokens'),
            func.sum(APIKeyUsage.cost_usd).label('cost'),
            func.avg(APIKeyUsage.response_time_ms).label('avg_response_time')
        ).filter(
            APIKeyUsage.organization_id == org_id
        )
        
        if start_date:
            query = query.filter(APIKeyUsage.timestamp >= start_date)
        
        if end_date:
            query = query.filter(APIKeyUsage.timestamp <= end_date)
        
        results = query.group_by(APIKeyUsage.endpoint).order_by(
            func.count(APIKeyUsage.id).desc()
        ).all()
        
        return [
            {
                "endpoint": r.endpoint,
                "requests": r.requests,
                "tokens": r.tokens or 0,
                "cost_usd": round(r.cost or 0.0, 4),
                "avg_response_time_ms": round(r.avg_response_time or 0.0, 2)
            }
            for r in results
        ]
    
    def get_error_stats(
        self,
        org_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get error statistics.
        
        Args:
            org_id: Organization UUID
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of error statistics
        """
        query = self.session.query(
            APIKeyUsage.status_code,
            APIKeyUsage.error_code,
            func.count(APIKeyUsage.id).label('count')
        ).filter(
            and_(
                APIKeyUsage.organization_id == org_id,
                APIKeyUsage.status_code >= 400
            )
        )
        
        if start_date:
            query = query.filter(APIKeyUsage.timestamp >= start_date)
        
        if end_date:
            query = query.filter(APIKeyUsage.timestamp <= end_date)
        
        results = query.group_by(
            APIKeyUsage.status_code,
            APIKeyUsage.error_code
        ).order_by(
            func.count(APIKeyUsage.id).desc()
        ).all()
        
        return [
            {
                "status_code": r.status_code,
                "error_code": r.error_code,
                "count": r.count
            }
            for r in results
        ]
    
    def get_monthly_usage(self, org_id: UUID) -> int:
        """
        Get current month's request count.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Number of requests this month
        """
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        
        return self.session.query(APIKeyUsage).filter(
            and_(
                APIKeyUsage.organization_id == org_id,
                APIKeyUsage.timestamp >= start_of_month
            )
        ).count()
    
    def delete_old_records(self, days: int = 90) -> int:
        """
        Delete usage records older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of records deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        old_records = self.session.query(APIKeyUsage).filter(
            APIKeyUsage.timestamp < cutoff
        ).all()
        
        count = len(old_records)
        
        for record in old_records:
            self.session.delete(record)
        
        self.session.commit()
        
        return count
    
    def get_top_consumers(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get top API key consumers by request count.
        
        Args:
            limit: Number of top consumers to return
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of top consumers with statistics
        """
        query = self.session.query(
            APIKeyUsage.api_key_id,
            APIKeyUsage.organization_id,
            func.count(APIKeyUsage.id).label('requests'),
            func.sum(APIKeyUsage.tokens_used).label('tokens'),
            func.sum(APIKeyUsage.cost_usd).label('cost')
        )
        
        if start_date:
            query = query.filter(APIKeyUsage.timestamp >= start_date)
        
        if end_date:
            query = query.filter(APIKeyUsage.timestamp <= end_date)
        
        results = query.group_by(
            APIKeyUsage.api_key_id,
            APIKeyUsage.organization_id
        ).order_by(
            func.count(APIKeyUsage.id).desc()
        ).limit(limit).all()
        
        return [
            {
                "api_key_id": str(r.api_key_id),
                "organization_id": str(r.organization_id),
                "requests": r.requests,
                "tokens": r.tokens or 0,
                "cost_usd": round(r.cost or 0.0, 4)
            }
            for r in results
        ]
