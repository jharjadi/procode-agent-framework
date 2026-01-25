"""
Circuit Breaker Module

This module implements the circuit breaker pattern to protect against
cascading failures when external services are unavailable. It automatically
detects failures and prevents requests to failing services, allowing them
time to recover.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any, Optional, Dict
import asyncio
import threading


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"        # Normal operation, requests allowed
    OPEN = "open"            # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker for external service failures.
    
    Implements the circuit breaker pattern with three states:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Service is failing, requests are blocked
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        success_threshold: int = 2,
        name: str = "default"
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting reset
            success_threshold: Successful calls needed to close circuit from half-open
            name: Name of the circuit breaker for logging
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self.name = name
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()
        
        self._lock = threading.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result from the function
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception from the function
        """
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Service unavailable."
                    )
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure()
            raise e
    
    def call_sync(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute synchronous function with circuit breaker protection.
        
        Args:
            func: Synchronous function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result from the function
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception from the function
        """
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Service unavailable."
                    )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self._transition_to_closed()
            else:
                # Reset failure count on success in CLOSED state
                self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                # Immediately open on failure in half-open state
                self._transition_to_open()
            elif self.failure_count >= self.failure_threshold:
                self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """
        Check if enough time has passed to attempt reset.
        
        Returns:
            True if timeout has elapsed since last failure
        """
        if not self.last_failure_time:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout
    
    def _transition_to_open(self):
        """Transition to OPEN state."""
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.now()
        self.success_count = 0
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = datetime.now()
        self.success_count = 0
        self.failure_count = 0
    
    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.last_state_change = datetime.now()
        self.failure_count = 0
        self.success_count = 0
    
    def reset(self):
        """Manually reset the circuit breaker to CLOSED state."""
        with self._lock:
            self._transition_to_closed()
            self.last_failure_time = None
    
    def force_open(self):
        """Manually force the circuit breaker to OPEN state."""
        with self._lock:
            self._transition_to_open()
    
    def get_state(self) -> CircuitState:
        """
        Get current circuit breaker state.
        
        Returns:
            Current CircuitState
        """
        return self.state
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get circuit breaker statistics.
        
        Returns:
            Dictionary with current stats
        """
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "failure_threshold": self.failure_threshold,
                "success_threshold": self.success_threshold,
                "timeout": self.timeout,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "last_state_change": self.last_state_change.isoformat(),
                "time_in_current_state": (datetime.now() - self.last_state_change).total_seconds()
            }
    
    def __repr__(self) -> str:
        """String representation of circuit breaker."""
        return (
            f"CircuitBreaker(name='{self.name}', state={self.state.value}, "
            f"failures={self.failure_count}/{self.failure_threshold})"
        )


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.
    
    Provides centralized management of circuit breakers for different services.
    """
    
    def __init__(self):
        """Initialize the circuit breaker manager."""
        self.breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
    
    def get_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: int = 60,
        success_threshold: int = 2
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker.
        
        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of failures before opening
            timeout: Seconds to wait before reset attempt
            success_threshold: Successes needed to close from half-open
            
        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(
                    failure_threshold=failure_threshold,
                    timeout=timeout,
                    success_threshold=success_threshold,
                    name=name
                )
            return self.breakers[name]
    
    def reset_all(self):
        """Reset all circuit breakers to CLOSED state."""
        with self._lock:
            for breaker in self.breakers.values():
                breaker.reset()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all circuit breakers.
        
        Returns:
            Dictionary mapping breaker names to their stats
        """
        with self._lock:
            return {
                name: breaker.get_stats()
                for name, breaker in self.breakers.items()
            }
    
    def list_breakers(self) -> list[str]:
        """
        List all circuit breaker names.
        
        Returns:
            List of breaker names
        """
        with self._lock:
            return list(self.breakers.keys())


# Global circuit breaker manager
_global_circuit_breaker_manager: Optional[CircuitBreakerManager] = None


def get_global_circuit_breaker_manager() -> CircuitBreakerManager:
    """
    Get or create the global circuit breaker manager.
    
    Returns:
        Global CircuitBreakerManager instance
    """
    global _global_circuit_breaker_manager
    if _global_circuit_breaker_manager is None:
        _global_circuit_breaker_manager = CircuitBreakerManager()
    return _global_circuit_breaker_manager


def reset_global_circuit_breaker_manager():
    """Reset the global circuit breaker manager (useful for testing)."""
    global _global_circuit_breaker_manager
    _global_circuit_breaker_manager = None
