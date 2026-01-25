"""
Enhanced Guardrails Module

This module provides comprehensive safety checks, content filtering, and
security validation for the agent system. It integrates rate limiting,
audit logging, and compliance features to ensure safe operation.
"""

from typing import Optional, List, Dict, Any, Tuple
import re
from rate_limiter import RateLimiter, get_global_rate_limiter
from audit_logger import AuditLogger, get_global_audit_logger
from compliance import ComplianceManager, get_global_compliance_manager


class EnhancedGuardrails:
    """
    Enhanced guardrails with comprehensive safety checks.
    
    Provides:
    - Input validation and sanitization
    - Content filtering (blocked patterns, PII detection)
    - Rate limiting
    - Injection attack detection
    - Output sanitization
    - Audit logging
    - Compliance checks
    """
    
    def __init__(
        self,
        max_message_length: int = 10000,
        max_tokens: int = 4000,
        rate_limiter: Optional[RateLimiter] = None,
        audit_logger: Optional[AuditLogger] = None,
        compliance_manager: Optional[ComplianceManager] = None
    ):
        """
        Initialize enhanced guardrails.
        
        Args:
            max_message_length: Maximum message length in characters
            max_tokens: Maximum tokens (approximate)
            rate_limiter: Optional rate limiter instance
            audit_logger: Optional audit logger instance
            compliance_manager: Optional compliance manager instance
        """
        self.max_message_length = max_message_length
        self.max_tokens = max_tokens
        
        # Use provided instances or get global ones
        self.rate_limiter = rate_limiter or get_global_rate_limiter()
        self.audit_logger = audit_logger or get_global_audit_logger()
        self.compliance_manager = compliance_manager or get_global_compliance_manager()
        
        # Load patterns
        self.blocked_patterns = self._load_blocked_patterns()
        self.pii_patterns = self._load_pii_patterns()
    
    def validate_input(
        self,
        text: str,
        user_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive input validation.
        
        Args:
            text: Input text to validate
            user_id: Optional user identifier
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Length check
        if len(text) > self.max_message_length:
            return False, f"Message too long (max {self.max_message_length} chars)"
        
        # Empty check
        if not text.strip():
            return False, "Empty message"
        
        # Rate limiting
        if user_id and not self.rate_limiter.check_rate(user_id):
            self.audit_logger.log_rate_limit_exceeded(user_id, "general")
            return False, "Rate limit exceeded. Please try again later."
        
        # Content filtering
        if self._contains_blocked_content(text):
            self.audit_logger.log_blocked_content(text, user_id)
            return False, "Message contains prohibited content"
        
        # PII detection (warning, but allow)
        pii_found = self._detect_pii(text)
        if pii_found:
            self.audit_logger.log_pii_detection(pii_found, user_id)
            # Could return False here for strict PII blocking
        
        # Injection attack detection
        if self._detect_injection_attack(text):
            self.audit_logger.log_security_event("injection_attempt", text, user_id)
            return False, "Potential security threat detected"
        
        # Prompt injection detection
        if self._detect_prompt_injection(text):
            self.audit_logger.log_security_event("prompt_injection", text, user_id)
            return False, "Invalid request format detected"
        
        return True, None
    
    def _load_blocked_patterns(self) -> List[re.Pattern]:
        """
        Load patterns for blocked content.
        
        Returns:
            List of compiled regex patterns
        """
        patterns = [
            # System manipulation attempts
            r"(?i)(hack|exploit|vulnerability)\s+(the|this)\s+system",
            r"(?i)ignore\s+(previous|all|prior)\s+(instructions|prompts|rules)",
            r"(?i)you\s+are\s+now\s+(a\s+different|no\s+longer)",
            r"(?i)disregard\s+(safety|security|guardrails|rules)",
            r"(?i)forget\s+(everything|all|your)\s+(you|instructions)",
            
            # Jailbreak attempts
            r"(?i)pretend\s+(you|to\s+be)\s+(are|a)",
            r"(?i)act\s+as\s+(if|a|an)",
            r"(?i)roleplay\s+as",
            
            # Harmful content
            r"(?i)(create|generate|write)\s+(malware|virus|exploit)",
            r"(?i)(how\s+to|guide\s+to)\s+(hack|break\s+into|exploit)",
        ]
        return [re.compile(p) for p in patterns]
    
    def _load_pii_patterns(self) -> Dict[str, re.Pattern]:
        """
        Load patterns for PII detection.
        
        Returns:
            Dictionary mapping PII types to regex patterns
        """
        return {
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "credit_card": re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
            "phone": re.compile(r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'),
            "api_key": re.compile(r'(?i)(api[_-]?key|token|secret|password)["\s:=]+[a-zA-Z0-9_-]{20,}'),
            "ip_address": re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
        }
    
    def _contains_blocked_content(self, text: str) -> bool:
        """
        Check for blocked content patterns.
        
        Args:
            text: Text to check
            
        Returns:
            True if blocked content is found
        """
        return any(pattern.search(text) for pattern in self.blocked_patterns)
    
    def _detect_pii(self, text: str) -> List[str]:
        """
        Detect PII in text.
        
        Args:
            text: Text to check
            
        Returns:
            List of detected PII types
        """
        found = []
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(text):
                found.append(pii_type)
        return found
    
    def _detect_injection_attack(self, text: str) -> bool:
        """
        Detect potential injection attacks.
        
        Args:
            text: Text to check
            
        Returns:
            True if injection attack is detected
        """
        injection_patterns = [
            r"<script[^>]*>.*?</script>",  # XSS
            r"javascript:",  # JavaScript injection
            r"on\w+\s*=",  # Event handler injection
            r"(?i)(union|select|insert|update|delete|drop)\s+(all\s+)?from",  # SQL injection
            r"(?i);\s*(drop|delete|update|insert)",  # SQL command injection
        ]
        return any(re.search(p, text, re.IGNORECASE | re.DOTALL) for p in injection_patterns)
    
    def _detect_prompt_injection(self, text: str) -> bool:
        """
        Detect prompt injection attempts.
        
        Args:
            text: Text to check
            
        Returns:
            True if prompt injection is detected
        """
        prompt_injection_patterns = [
            r"(?i)system\s*:\s*you\s+are",
            r"(?i)###\s*instruction",
            r"(?i)\[SYSTEM\]",
            r"(?i)assistant\s*:\s*i\s+will",
        ]
        return any(re.search(p, text) for p in prompt_injection_patterns)
    
    def sanitize_output(self, text: str, redact_pii: bool = True) -> str:
        """
        Sanitize output to remove sensitive information.
        
        Args:
            text: Text to sanitize
            redact_pii: Whether to redact PII
            
        Returns:
            Sanitized text
        """
        sanitized = text
        
        # Redact PII if requested
        if redact_pii:
            for pii_type, pattern in self.pii_patterns.items():
                sanitized = pattern.sub(f"[REDACTED_{pii_type.upper()}]", sanitized)
        
        # Remove potential code execution
        sanitized = re.sub(r"<script[^>]*>.*?</script>", "", sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)
        
        # Remove event handlers
        sanitized = re.sub(r"on\w+\s*=\s*[\"'][^\"']*[\"']", "", sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def validate_output(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate output before sending to user.
        
        Args:
            text: Output text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for leaked sensitive information
        pii_found = self._detect_pii(text)
        if pii_found:
            return False, f"Output contains PII: {', '.join(pii_found)}"
        
        # Check for injection attempts in output
        if self._detect_injection_attack(text):
            return False, "Output contains potentially harmful content"
        
        return True, None
    
    def check_compliance(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check compliance requirements for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Tuple of (is_compliant, error_message)
        """
        if not self.compliance_manager.check_consent(user_id):
            return False, "User consent required"
        
        return True, None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about guardrails usage.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "rate_limiter": self.rate_limiter.get_stats(),
            "audit_logger": self.audit_logger.get_stats(),
            "compliance": self.compliance_manager.get_retention_policy(),
            "config": {
                "max_message_length": self.max_message_length,
                "max_tokens": self.max_tokens,
                "blocked_patterns_count": len(self.blocked_patterns),
                "pii_patterns_count": len(self.pii_patterns)
            }
        }


# Global enhanced guardrails instance
_global_enhanced_guardrails: Optional[EnhancedGuardrails] = None


def get_global_enhanced_guardrails() -> EnhancedGuardrails:
    """
    Get or create the global enhanced guardrails instance.
    
    Returns:
        Global EnhancedGuardrails instance
    """
    global _global_enhanced_guardrails
    if _global_enhanced_guardrails is None:
        _global_enhanced_guardrails = EnhancedGuardrails()
    return _global_enhanced_guardrails


def reset_global_enhanced_guardrails():
    """Reset the global enhanced guardrails (useful for testing)."""
    global _global_enhanced_guardrails
    _global_enhanced_guardrails = None
