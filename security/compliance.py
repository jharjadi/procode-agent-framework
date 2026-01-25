"""
Compliance Module

This module manages compliance requirements including GDPR, data retention
policies, user consent, and data privacy features. It provides tools for
data anonymization, export, and deletion to meet regulatory requirements.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
import json
from pathlib import Path


class ComplianceManager:
    """
    Manage compliance requirements (GDPR, data retention, etc.).
    
    Provides functionality for:
    - Data retention policy enforcement
    - User consent management
    - Data anonymization
    - Data export (right to access)
    - Data deletion (right to be forgotten)
    """
    
    def __init__(
        self,
        data_retention_days: int = 90,
        consent_required: bool = True,
        storage_path: str = "data/compliance"
    ):
        """
        Initialize the compliance manager.
        
        Args:
            data_retention_days: Number of days to retain data
            consent_required: Whether user consent is required
            storage_path: Path to store compliance data
        """
        self.data_retention_days = data_retention_days
        self.consent_required = consent_required
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory consent tracking (in production, use database)
        self.consent_records: Dict[str, Dict[str, Any]] = {}
    
    def check_data_retention(self, data_timestamp: datetime) -> bool:
        """
        Check if data is within retention period.
        
        Args:
            data_timestamp: When the data was created
            
        Returns:
            True if data should be retained, False if it should be deleted
        """
        data_age = datetime.now() - data_timestamp
        return data_age.days <= self.data_retention_days
    
    def should_delete_data(self, data_timestamp: datetime) -> bool:
        """
        Check if data should be deleted based on retention policy.
        
        Args:
            data_timestamp: When the data was created
            
        Returns:
            True if data should be deleted
        """
        return not self.check_data_retention(data_timestamp)
    
    def record_consent(
        self,
        user_id: str,
        consent_type: str,
        granted: bool,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record user consent.
        
        Args:
            user_id: User identifier
            consent_type: Type of consent (e.g., 'data_processing', 'marketing')
            granted: Whether consent was granted
            metadata: Optional additional metadata
        """
        if user_id not in self.consent_records:
            self.consent_records[user_id] = {}
        
        self.consent_records[user_id][consent_type] = {
            "granted": granted,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
    
    def check_consent(self, user_id: str, consent_type: str = "data_processing") -> bool:
        """
        Check if user has given consent.
        
        Args:
            user_id: User identifier
            consent_type: Type of consent to check
            
        Returns:
            True if consent is granted, False otherwise
        """
        if not self.consent_required:
            return True
        
        if user_id not in self.consent_records:
            return False
        
        consent = self.consent_records[user_id].get(consent_type)
        if not consent:
            return False
        
        return consent.get("granted", False)
    
    def anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize data by removing or hashing PII fields.
        
        Args:
            data: Data dictionary to anonymize
            
        Returns:
            Anonymized data dictionary
        """
        anonymized = data.copy()
        
        # Fields to completely remove
        remove_fields = ["password", "api_key", "secret", "token"]
        
        # Fields to anonymize (hash)
        hash_fields = ["email", "phone", "address", "ssn", "credit_card"]
        
        # Fields to redact
        redact_fields = ["name", "username"]
        
        for field in remove_fields:
            if field in anonymized:
                del anonymized[field]
        
        for field in hash_fields:
            if field in anonymized:
                anonymized[field] = self._hash_value(str(anonymized[field]))
        
        for field in redact_fields:
            if field in anonymized:
                anonymized[field] = "[REDACTED]"
        
        return anonymized
    
    def _hash_value(self, value: str) -> str:
        """
        Hash a value for anonymization.
        
        Args:
            value: Value to hash
            
        Returns:
            Hashed value
        """
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    def generate_data_export(
        self,
        user_id: str,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Generate data export for GDPR compliance (right to access).
        
        Args:
            user_id: User identifier
            include_metadata: Whether to include metadata
            
        Returns:
            Dictionary with user's data
        """
        export_data = {
            "user_id": user_id,
            "export_date": datetime.now().isoformat(),
            "data_retention_days": self.data_retention_days,
            "data": {}
        }
        
        if include_metadata:
            export_data["metadata"] = {
                "consent_records": self.consent_records.get(user_id, {}),
                "export_format": "JSON",
                "compliance_version": "1.0"
            }
        
        # In production, gather data from all systems
        # For now, return structure
        return export_data
    
    def delete_user_data(self, user_id: str, reason: str = "user_request") -> Dict[str, Any]:
        """
        Delete user data (right to be forgotten).
        
        Args:
            user_id: User identifier
            reason: Reason for deletion
            
        Returns:
            Dictionary with deletion details
        """
        deletion_record = {
            "user_id": user_id,
            "deletion_date": datetime.now().isoformat(),
            "reason": reason,
            "deleted_items": []
        }
        
        # Delete consent records
        if user_id in self.consent_records:
            del self.consent_records[user_id]
            deletion_record["deleted_items"].append("consent_records")
        
        # In production, delete from all systems:
        # - Database records
        # - File storage
        # - Cache
        # - Logs (or anonymize)
        # - Backups (mark for deletion)
        
        # Save deletion record for audit
        self._save_deletion_record(deletion_record)
        
        return deletion_record
    
    def _save_deletion_record(self, record: Dict[str, Any]):
        """
        Save deletion record for audit purposes.
        
        Args:
            record: Deletion record to save
        """
        try:
            deletion_log = self.storage_path / "deletions.jsonl"
            with open(deletion_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass  # Fail silently, but log in production
    
    def get_retention_policy(self) -> Dict[str, Any]:
        """
        Get current data retention policy.
        
        Returns:
            Dictionary with retention policy details
        """
        return {
            "retention_days": self.data_retention_days,
            "retention_period": f"{self.data_retention_days} days",
            "deletion_after": (
                datetime.now() + timedelta(days=self.data_retention_days)
            ).isoformat(),
            "consent_required": self.consent_required
        }
    
    def audit_data_age(self, data_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Audit data items for retention compliance.
        
        Args:
            data_items: List of data items with 'timestamp' field
            
        Returns:
            Audit report
        """
        now = datetime.now()
        expired_count = 0
        valid_count = 0
        
        for item in data_items:
            if "timestamp" not in item:
                continue
            
            try:
                timestamp = datetime.fromisoformat(item["timestamp"])
                if self.should_delete_data(timestamp):
                    expired_count += 1
                else:
                    valid_count += 1
            except (ValueError, TypeError):
                continue
        
        return {
            "audit_date": now.isoformat(),
            "total_items": len(data_items),
            "valid_items": valid_count,
            "expired_items": expired_count,
            "retention_policy_days": self.data_retention_days
        }
    
    def get_consent_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get summary of user's consent records.
        
        Args:
            user_id: User identifier
            
        Returns:
            Consent summary
        """
        if user_id not in self.consent_records:
            return {
                "user_id": user_id,
                "has_consents": False,
                "consents": {}
            }
        
        return {
            "user_id": user_id,
            "has_consents": True,
            "consents": self.consent_records[user_id]
        }
    
    def validate_compliance(self, user_id: str) -> Dict[str, Any]:
        """
        Validate compliance status for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Compliance validation report
        """
        issues = []
        
        # Check consent
        if self.consent_required and not self.check_consent(user_id):
            issues.append("Missing required consent")
        
        # Check data retention (would check actual data in production)
        
        return {
            "user_id": user_id,
            "compliant": len(issues) == 0,
            "issues": issues,
            "validation_date": datetime.now().isoformat()
        }


# Global compliance manager instance
_global_compliance_manager: Optional[ComplianceManager] = None


def get_global_compliance_manager() -> ComplianceManager:
    """
    Get or create the global compliance manager instance.
    
    Returns:
        Global ComplianceManager instance
    """
    global _global_compliance_manager
    if _global_compliance_manager is None:
        _global_compliance_manager = ComplianceManager()
    return _global_compliance_manager


def reset_global_compliance_manager():
    """Reset the global compliance manager (useful for testing)."""
    global _global_compliance_manager
    _global_compliance_manager = None
