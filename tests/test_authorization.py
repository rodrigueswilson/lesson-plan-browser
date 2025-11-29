"""
Unit tests for authorization module.

Tests verify_user_access and verify_slot_ownership functions.
"""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock, MagicMock

from backend.authorization import (
    verify_user_access,
    verify_slot_ownership,
    _validate_user_id_format,
    _sanitize_user_id,
)


class TestValidateUserIDFormat:
    """Test user ID format validation."""
    
    def test_valid_user_id(self):
        """Valid user IDs should pass."""
        assert _validate_user_id_format("user-123") is True
        assert _validate_user_id_format("abc_def-123") is True
        assert _validate_user_id_format("a") is True
        assert _validate_user_id_format("user123") is True
    
    def test_invalid_user_id(self):
        """Invalid user IDs should fail."""
        assert _validate_user_id_format("") is False
        assert _validate_user_id_format("user@123") is False  # Special chars
        assert _validate_user_id_format("user 123") is False  # Spaces
        assert _validate_user_id_format("user.123") is False  # Dots
        assert _validate_user_id_format(None) is False
        assert _validate_user_id_format(123) is False  # Not a string
    
    def test_too_long_user_id(self):
        """Very long user IDs should fail."""
        long_id = "a" * 256
        assert _validate_user_id_format(long_id) is False


class TestSanitizeUserID:
    """Test user ID sanitization for logging."""
    
    def test_short_id(self):
        """Short IDs should be returned as-is."""
        assert _sanitize_user_id("user123") == "user123"
    
    def test_long_id(self):
        """Long IDs should be truncated."""
        long_id = "a" * 20
        result = _sanitize_user_id(long_id)
        assert len(result) == 11  # 8 chars + "..."
        assert result.endswith("...")
    
    def test_empty_id(self):
        """Empty IDs should return 'empty'."""
        assert _sanitize_user_id("") == "empty"
        assert _sanitize_user_id(None) == "empty"


class TestVerifyUserAccess:
    """Test verify_user_access function."""
    
    def test_matching_user_ids(self):
        """Matching user IDs should succeed."""
        verify_user_access("user-123", "user-123", allow_if_none=False)
        # Should not raise
    
    def test_mismatched_user_ids(self):
        """Mismatched user IDs should raise 403."""
        with pytest.raises(HTTPException) as exc_info:
            verify_user_access("user-123", "user-456", allow_if_none=False)
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail
    
    def test_none_current_user_allowed(self):
        """None current_user_id should be allowed if allow_if_none=True."""
        verify_user_access("user-123", None, allow_if_none=True)
        # Should not raise
    
    def test_none_current_user_not_allowed(self):
        """None current_user_id should raise 403 if allow_if_none=False."""
        with pytest.raises(HTTPException) as exc_info:
            verify_user_access("user-123", None, allow_if_none=False)
        
        assert exc_info.value.status_code == 403
    
    def test_invalid_requested_user_id_format(self):
        """Invalid requested_user_id format should raise 400."""
        with pytest.raises(HTTPException) as exc_info:
            verify_user_access("user@123", "user-123", allow_if_none=False)
        
        assert exc_info.value.status_code == 400
        assert "Invalid user ID format" in exc_info.value.detail
    
    def test_invalid_current_user_id_format(self):
        """Invalid current_user_id format should raise 400."""
        with pytest.raises(HTTPException) as exc_info:
            verify_user_access("user-123", "user@123", allow_if_none=False)
        
        assert exc_info.value.status_code == 400
        assert "Invalid current user ID format" in exc_info.value.detail


class TestVerifySlotOwnership:
    """Test verify_slot_ownership function."""
    
    def test_valid_ownership(self):
        """Valid slot ownership should succeed."""
        mock_db = Mock()
        mock_db.get_slot.return_value = {
            "id": "slot-123",
            "user_id": "user-123",
        }
        
        result = verify_slot_ownership(
            "slot-123",
            "user-123",
            mock_db,
            allow_if_none=False,
        )
        
        assert result == "user-123"
        mock_db.get_slot.assert_called_once_with("slot-123")
    
    def test_slot_not_found(self):
        """Non-existent slot should raise 404."""
        mock_db = Mock()
        mock_db.get_slot.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            verify_slot_ownership(
                "slot-123",
                "user-123",
                mock_db,
                allow_if_none=False,
            )
        
        assert exc_info.value.status_code == 404
        assert "Slot not found" in exc_info.value.detail
    
    def test_slot_missing_user_id(self):
        """Slot without user_id should raise 500."""
        mock_db = Mock()
        mock_db.get_slot.return_value = {
            "id": "slot-123",
            # Missing user_id
        }
        
        with pytest.raises(HTTPException) as exc_info:
            verify_slot_ownership(
                "slot-123",
                "user-123",
                mock_db,
                allow_if_none=False,
            )
        
        assert exc_info.value.status_code == 500
        assert "integrity error" in exc_info.value.detail.lower()
    
    def test_unauthorized_access(self):
        """Accessing another user's slot should raise 403."""
        mock_db = Mock()
        mock_db.get_slot.return_value = {
            "id": "slot-123",
            "user_id": "user-456",  # Different user
        }
        
        with pytest.raises(HTTPException) as exc_info:
            verify_slot_ownership(
                "slot-123",
                "user-123",  # Current user doesn't own slot
                mock_db,
                allow_if_none=False,
            )
        
        assert exc_info.value.status_code == 403
    
    def test_invalid_slot_id_format(self):
        """Invalid slot_id format should raise 400."""
        mock_db = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            verify_slot_ownership(
                "slot@123",  # Invalid format
                "user-123",
                mock_db,
                allow_if_none=False,
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid slot ID format" in exc_info.value.detail
        # Should not call database
        mock_db.get_slot.assert_not_called()


class TestAuthorizationEdgeCases:
    """Test edge cases and security scenarios."""
    
    def test_empty_strings(self):
        """Empty strings should be rejected."""
        with pytest.raises(HTTPException) as exc_info:
            verify_user_access("", "user-123", allow_if_none=False)
        assert exc_info.value.status_code == 400
    
    def test_sql_injection_attempt(self):
        """SQL injection attempts should be rejected by format validation."""
        malicious_id = "user'; DROP TABLE users; --"
        with pytest.raises(HTTPException) as exc_info:
            verify_user_access(malicious_id, "user-123", allow_if_none=False)
        assert exc_info.value.status_code == 400
    
    def test_very_long_user_id(self):
        """Very long user IDs should be rejected."""
        long_id = "a" * 300
        with pytest.raises(HTTPException) as exc_info:
            verify_user_access(long_id, "user-123", allow_if_none=False)
        assert exc_info.value.status_code == 400
    
    def test_unicode_user_id(self):
        """Unicode characters should be handled."""
        unicode_id = "user-测试-123"
        # Should pass format validation (alphanumeric + dashes/underscores)
        # But may fail in actual use depending on database constraints
        # This tests that format validation works correctly
        assert _validate_user_id_format(unicode_id) is False  # Contains non-ASCII

