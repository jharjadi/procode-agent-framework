"""
Rate Limiter Module

This module provides rate limiting functionality to prevent abuse and ensure
fair usage of the agent system. It implements sliding window rate limiting
with multiple time windows (minute, hour, day).
"""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional
import threading


class RateLimiter:
    """
    Rate limiting for abuse prevention using sliding window algorithm.
    
    Tracks requests per user across multiple time windows and enforces
    configurable limits to prevent abuse.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 10,
        requests_per_hour: int = 100,
        requests_per_day: int = 1000
    ):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute
            requests_per_hour: Maximum requests allowed per hour
            requests_per_day: Maximum requests allowed per day
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        
        # Track requests: user_id -> list of timestamps
        self.request_history: Dict[str, List[datetime]] = defaultdict(list)
        
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
    
    def check_rate(self, user_id: str) -> bool:
        """
        Check if user is within rate limits and record the request.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        with self._lock:
            now = datetime.now()
            
            # Clean old entries
            self._cleanup_old_entries(user_id, now)
            
            # Get request counts
            minute_count = self._count_requests(user_id, now, timedelta(minutes=1))
            hour_count = self._count_requests(user_id, now, timedelta(hours=1))
            day_count = self._count_requests(user_id, now, timedelta(days=1))
            
            # Check limits
            if minute_count >= self.requests_per_minute:
                return False
            if hour_count >= self.requests_per_hour:
                return False
            if day_count >= self.requests_per_day:
                return False
            
            # Record request
            self.request_history[user_id].append(now)
            return True
    
    def _cleanup_old_entries(self, user_id: str, now: datetime):
        """
        Remove entries older than 24 hours to prevent memory growth.
        
        Args:
            user_id: User identifier
            now: Current timestamp
        """
        cutoff = now - timedelta(days=1)
        self.request_history[user_id] = [
            ts for ts in self.request_history[user_id]
            if ts > cutoff
        ]
        
        # Remove user entry if no recent requests
        if not self.request_history[user_id]:
            del self.request_history[user_id]
    
    def _count_requests(
        self,
        user_id: str,
        now: datetime,
        window: timedelta
    ) -> int:
        """
        Count requests within a time window.
        
        Args:
            user_id: User identifier
            now: Current timestamp
            window: Time window to count within
            
        Returns:
            Number of requests in the window
        """
        cutoff = now - window
        return sum(1 for ts in self.request_history[user_id] if ts > cutoff)
    
    def get_remaining_quota(self, user_id: str) -> Dict[str, int]:
        """
        Get remaining quota for user across all time windows.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with remaining requests for each time window
        """
        with self._lock:
            now = datetime.now()
            return {
                "minute": max(0, self.requests_per_minute - self._count_requests(
                    user_id, now, timedelta(minutes=1)
                )),
                "hour": max(0, self.requests_per_hour - self._count_requests(
                    user_id, now, timedelta(hours=1)
                )),
                "day": max(0, self.requests_per_day - self._count_requests(
                    user_id, now, timedelta(days=1)
                )),
            }
    
    def get_reset_time(self, user_id: str) -> Dict[str, Optional[datetime]]:
        """
        Get the time when each quota will reset for the user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with reset times for each window
        """
        with self._lock:
            if user_id not in self.request_history or not self.request_history[user_id]:
                return {
                    "minute": None,
                    "hour": None,
                    "day": None
                }
            
            oldest_request = min(self.request_history[user_id])
            
            return {
                "minute": oldest_request + timedelta(minutes=1),
                "hour": oldest_request + timedelta(hours=1),
                "day": oldest_request + timedelta(days=1)
            }
    
    def reset_user(self, user_id: str):
        """
        Reset rate limit for a specific user (admin function).
        
        Args:
            user_id: User identifier to reset
        """
        with self._lock:
            if user_id in self.request_history:
                del self.request_history[user_id]
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get statistics about rate limiter usage.
        
        Returns:
            Dictionary with usage statistics
        """
        with self._lock:
            total_users = len(self.request_history)
            total_requests = sum(len(reqs) for reqs in self.request_history.values())
            
            return {
                "total_users": total_users,
                "total_requests_tracked": total_requests,
                "limits": {
                    "per_minute": self.requests_per_minute,
                    "per_hour": self.requests_per_hour,
                    "per_day": self.requests_per_day
                }
            }
    
    def __repr__(self) -> str:
        """String representation of rate limiter."""
        return (
            f"RateLimiter(minute={self.requests_per_minute}, "
            f"hour={self.requests_per_hour}, day={self.requests_per_day})"
        )


# Global rate limiter instance
_global_rate_limiter: Optional[RateLimiter] = None


def get_global_rate_limiter() -> RateLimiter:
    """
    Get or create the global rate limiter instance.
    
    Returns:
        Global RateLimiter instance
    """
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter()
    return _global_rate_limiter


def reset_global_rate_limiter():
    """Reset the global rate limiter (useful for testing)."""
    global _global_rate_limiter
    _global_rate_limiter = None
