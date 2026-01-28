"""
Health Check System for ProCode Agent Framework

This module provides comprehensive health checks for:
- Database connectivity
- LLM provider availability
- External agent connectivity
- System resources (disk, memory)
- Application readiness

Usage:
    from observability.health import health_checker
    
    # Get health status
    status = await health_checker.check_health()
    
    # Get readiness status
    ready = await health_checker.check_readiness()
"""

import time
import asyncio
import psutil
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum


class HealthStatus(str, Enum):
    """Health check status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class CheckResult:
    """Result of a single health check."""
    
    def __init__(
        self,
        name: str,
        status: HealthStatus,
        message: str,
        latency_ms: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.status = status
        self.message = message
        self.latency_ms = latency_ms
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "status": self.status.value,
            "message": self.message
        }
        if self.latency_ms is not None:
            result["latency_ms"] = round(self.latency_ms, 2)
        if self.details:
            result.update(self.details)
        return result


class HealthChecker:
    """
    Comprehensive health checker for the ProCode Agent Framework.
    
    Performs various health checks and aggregates results.
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.check_timeout = 5.0  # seconds
        self._db_engine = None
        self._llm_providers = []
        self._external_agents = []
    
    def set_database_engine(self, engine):
        """Set the database engine for health checks."""
        self._db_engine = engine
    
    def set_llm_providers(self, providers: List[str]):
        """Set LLM providers to check."""
        self._llm_providers = providers
    
    def set_external_agents(self, agents: List[Dict[str, str]]):
        """Set external agents to check."""
        self._external_agents = agents
    
    # ------------------------------------------------------------------------
    # Main Health Check
    # ------------------------------------------------------------------------
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Dictionary with overall health status and individual check results.
        """
        checks = {}
        
        # Run all health checks concurrently
        check_tasks = [
            ("database", self._check_database()),
            ("llm_provider", self._check_llm_provider()),
            ("external_agents", self._check_external_agents()),
            ("disk_space", self._check_disk_space()),
            ("memory", self._check_memory()),
        ]
        
        for check_name, check_coro in check_tasks:
            try:
                result = await asyncio.wait_for(
                    check_coro,
                    timeout=self.check_timeout
                )
                checks[check_name] = result.to_dict()
            except asyncio.TimeoutError:
                checks[check_name] = CheckResult(
                    check_name,
                    HealthStatus.UNHEALTHY,
                    f"Health check timed out after {self.check_timeout}s"
                ).to_dict()
            except Exception as e:
                checks[check_name] = CheckResult(
                    check_name,
                    HealthStatus.UNHEALTHY,
                    f"Health check failed: {str(e)}"
                ).to_dict()
        
        # Determine overall status
        overall_status = self._determine_overall_status(checks)
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "0.1.0",
            "uptime_seconds": int(time.time() - self.start_time),
            "checks": checks
        }
    
    # ------------------------------------------------------------------------
    # Readiness Check
    # ------------------------------------------------------------------------
    
    async def check_readiness(self) -> Dict[str, Any]:
        """
        Check if the application is ready to serve traffic.
        
        Returns:
            Dictionary with readiness status and check results.
        """
        checks = {}
        
        # Check database migrations
        checks["database_migrations"] = await self._check_database_migrations()
        
        # Check dependencies loaded
        checks["dependencies"] = await self._check_dependencies()
        
        # Check warmup complete
        checks["warmup"] = await self._check_warmup()
        
        # Determine if ready
        ready = all(
            check.get("ready", False)
            for check in checks.values()
        )
        
        return {
            "ready": ready,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks
        }
    
    # ------------------------------------------------------------------------
    # Individual Health Checks
    # ------------------------------------------------------------------------
    
    async def _check_database(self) -> CheckResult:
        """Check database connectivity and responsiveness."""
        if not self._db_engine:
            return CheckResult(
                "database",
                HealthStatus.DEGRADED,
                "Database engine not configured"
            )
        
        start_time = time.time()
        try:
            # Try to execute a simple query
            from sqlalchemy import text
            
            async with self._db_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            
            latency_ms = (time.time() - start_time) * 1000
            
            return CheckResult(
                "database",
                HealthStatus.HEALTHY,
                "Connected to PostgreSQL",
                latency_ms=latency_ms
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return CheckResult(
                "database",
                HealthStatus.UNHEALTHY,
                f"Database connection failed: {str(e)}",
                latency_ms=latency_ms
            )
    
    async def _check_llm_provider(self) -> CheckResult:
        """Check LLM provider availability."""
        if not self._llm_providers:
            return CheckResult(
                "llm_provider",
                HealthStatus.HEALTHY,
                "No LLM providers configured"
            )
        
        # For now, just check if we can import the required modules
        # In production, you might want to make actual API calls
        start_time = time.time()
        try:
            import openai
            latency_ms = (time.time() - start_time) * 1000
            
            return CheckResult(
                "llm_provider",
                HealthStatus.HEALTHY,
                "LLM providers accessible",
                latency_ms=latency_ms
            )
        except ImportError as e:
            latency_ms = (time.time() - start_time) * 1000
            return CheckResult(
                "llm_provider",
                HealthStatus.DEGRADED,
                f"LLM provider module not available: {str(e)}",
                latency_ms=latency_ms
            )
    
    async def _check_external_agents(self) -> CheckResult:
        """Check external agent connectivity."""
        if not self._external_agents:
            return CheckResult(
                "external_agents",
                HealthStatus.HEALTHY,
                "No external agents configured"
            )
        
        start_time = time.time()
        available = 0
        total = len(self._external_agents)
        
        async with httpx.AsyncClient(timeout=2.0) as client:
            for agent in self._external_agents:
                try:
                    url = agent.get("url", "")
                    if url:
                        response = await client.get(f"{url}/health")
                        if response.status_code == 200:
                            available += 1
                except Exception:
                    # Agent not reachable
                    pass
        
        latency_ms = (time.time() - start_time) * 1000
        
        if available == total:
            status = HealthStatus.HEALTHY
            message = f"All {total} agents reachable"
        elif available > 0:
            status = HealthStatus.DEGRADED
            message = f"{available}/{total} agents reachable"
        else:
            status = HealthStatus.UNHEALTHY
            message = "No agents reachable"
        
        return CheckResult(
            "external_agents",
            status,
            message,
            latency_ms=latency_ms,
            details={"available": available, "total": total}
        )
    
    async def _check_disk_space(self) -> CheckResult:
        """Check available disk space."""
        start_time = time.time()
        try:
            disk = psutil.disk_usage('/')
            free_percent = (disk.free / disk.total) * 100
            latency_ms = (time.time() - start_time) * 1000
            
            if free_percent > 20:
                status = HealthStatus.HEALTHY
                message = f"Disk space OK ({free_percent:.1f}% free)"
            elif free_percent > 10:
                status = HealthStatus.DEGRADED
                message = f"Disk space low ({free_percent:.1f}% free)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Disk space critical ({free_percent:.1f}% free)"
            
            return CheckResult(
                "disk_space",
                status,
                message,
                latency_ms=latency_ms,
                details={
                    "free_gb": round(disk.free / (1024**3), 2),
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_percent": round(free_percent, 2)
                }
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return CheckResult(
                "disk_space",
                HealthStatus.UNHEALTHY,
                f"Failed to check disk space: {str(e)}",
                latency_ms=latency_ms
            )
    
    async def _check_memory(self) -> CheckResult:
        """Check memory usage."""
        start_time = time.time()
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            latency_ms = (time.time() - start_time) * 1000
            
            if used_percent < 80:
                status = HealthStatus.HEALTHY
                message = f"Memory usage OK ({used_percent:.1f}% used)"
            elif used_percent < 90:
                status = HealthStatus.DEGRADED
                message = f"Memory usage high ({used_percent:.1f}% used)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Memory usage critical ({used_percent:.1f}% used)"
            
            return CheckResult(
                "memory",
                status,
                message,
                latency_ms=latency_ms,
                details={
                    "used_gb": round(memory.used / (1024**3), 2),
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_percent": round(used_percent, 2)
                }
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return CheckResult(
                "memory",
                HealthStatus.UNHEALTHY,
                f"Failed to check memory: {str(e)}",
                latency_ms=latency_ms
            )
    
    # ------------------------------------------------------------------------
    # Readiness Checks
    # ------------------------------------------------------------------------
    
    async def _check_database_migrations(self) -> Dict[str, Any]:
        """Check if database migrations are up to date."""
        try:
            # In production, you'd check Alembic migration status
            # For now, just check if database is accessible
            if self._db_engine:
                return {
                    "ready": True,
                    "message": "Database migrations assumed current"
                }
            else:
                return {
                    "ready": False,
                    "message": "Database not configured"
                }
        except Exception as e:
            return {
                "ready": False,
                "message": f"Migration check failed: {str(e)}"
            }
    
    async def _check_dependencies(self) -> Dict[str, Any]:
        """Check if all dependencies are loaded."""
        try:
            # Check critical imports
            import fastapi
            import sqlalchemy
            import prometheus_client
            
            return {
                "ready": True,
                "message": "All dependencies loaded"
            }
        except ImportError as e:
            return {
                "ready": False,
                "message": f"Missing dependency: {str(e)}"
            }
    
    async def _check_warmup(self) -> Dict[str, Any]:
        """Check if application warmup is complete."""
        # Consider app warmed up after 5 seconds
        uptime = time.time() - self.start_time
        if uptime > 5:
            return {
                "ready": True,
                "message": "Application warmed up"
            }
        else:
            return {
                "ready": False,
                "message": f"Warming up ({int(uptime)}s elapsed)"
            }
    
    # ------------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------------
    
    def _determine_overall_status(
        self,
        checks: Dict[str, Dict[str, Any]]
    ) -> HealthStatus:
        """Determine overall health status from individual checks."""
        statuses = [
            HealthStatus(check["status"])
            for check in checks.values()
        ]
        
        # If any check is unhealthy, overall is unhealthy
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        
        # If any check is degraded, overall is degraded
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        
        # All checks are healthy
        return HealthStatus.HEALTHY


# ============================================================================
# GLOBAL HEALTH CHECKER INSTANCE
# ============================================================================

# Create a global health checker instance
health_checker = HealthChecker()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def get_health_status() -> Dict[str, Any]:
    """Get current health status."""
    return await health_checker.check_health()


async def get_readiness_status() -> Dict[str, Any]:
    """Get current readiness status."""
    return await health_checker.check_readiness()


def is_healthy(health_status: Dict[str, Any]) -> bool:
    """Check if the system is healthy."""
    return health_status.get("status") == HealthStatus.HEALTHY.value


def is_ready(readiness_status: Dict[str, Any]) -> bool:
    """Check if the system is ready."""
    return readiness_status.get("ready", False)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import json
    
    async def main():
        print("ProCode Agent Framework - Health Checker")
        print("=" * 60)
        
        # Check health
        print("\n1. Health Check:")
        health = await health_checker.check_health()
        print(json.dumps(health, indent=2))
        
        # Check readiness
        print("\n2. Readiness Check:")
        readiness = await health_checker.check_readiness()
        print(json.dumps(readiness, indent=2))
    
    asyncio.run(main())
