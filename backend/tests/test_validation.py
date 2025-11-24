"""
Input Validation Tests
Tests for input validation and sanitization functions
"""

import pytest
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from api.validation import (
    sanitize_string,
    validate_id,
    validate_amount,
    validate_country_code,
    validate_text_input,
    validate_email,
    check_sql_injection,
    check_xss,
    check_path_traversal,
    ValidationError
)


class TestSanitization:
    """Test string sanitization"""
    
    def test_sanitize_removes_null_bytes(self):
        """Test that null bytes are removed"""
        result = sanitize_string("test\x00string")
        assert "\x00" not in result
        assert result == "teststring"  # Null byte is removed without adding space
        
    def test_sanitize_removes_control_characters(self):
        """Test that control characters are removed (except newline/tab)"""
        result = sanitize_string("test\x01\x02string")
        assert result == "teststring"
        
    def test_sanitize_preserves_newlines_and_tabs(self):
        """Test that newlines and tabs are preserved"""
        result = sanitize_string("test\nstring\twith\ttabs")
        assert "\n" in result
        assert "\t" in result
        
    def test_sanitize_trims_to_max_length(self):
        """Test that strings are trimmed to max length"""
        long_string = "a" * 1000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100


class TestIDValidation:
    """Test ID validation"""
    
    def test_valid_id(self):
        """Test valid ID passes"""
        assert validate_id("TXN-123", "transaction_id") == "TXN-123"
        assert validate_id("CUST_456", "customer_id") == "CUST_456"
        assert validate_id("abc123", "id") == "abc123"
        
    def test_invalid_id_with_special_chars(self):
        """Test ID with special characters is rejected"""
        with pytest.raises(ValidationError):
            validate_id("TXN<123>", "transaction_id")
            
        with pytest.raises(ValidationError):
            validate_id("CUST@456", "customer_id")
            
    def test_empty_id_rejected(self):
        """Test empty ID is rejected"""
        with pytest.raises(ValidationError):
            validate_id("", "id")
            
    def test_id_too_long_rejected(self):
        """Test overly long ID is rejected"""
        long_id = "a" * 200
        with pytest.raises(ValidationError):
            validate_id(long_id, "id")


class TestAmountValidation:
    """Test amount validation"""
    
    def test_valid_amounts(self):
        """Test valid amounts pass"""
        assert validate_amount(100.00) == 100.00
        assert validate_amount(0.01) == 0.01
        assert validate_amount(999999.99) == 999999.99
        
    def test_negative_amount_rejected(self):
        """Test negative amount is rejected"""
        with pytest.raises(ValidationError):
            validate_amount(-100.00)
            
    def test_zero_amount_rejected(self):
        """Test zero amount is rejected"""
        with pytest.raises(ValidationError):
            validate_amount(0.00)
            
    def test_too_large_amount_rejected(self):
        """Test amount exceeding max is rejected"""
        with pytest.raises(ValidationError):
            validate_amount(2000000000.00)  # > 1 billion
            
    def test_too_many_decimals_rejected(self):
        """Test amount with too many decimal places is rejected"""
        with pytest.raises(ValidationError):
            validate_amount(100.123)  # More than 2 decimal places


class TestCountryCodeValidation:
    """Test country code validation"""
    
    def test_valid_country_codes(self):
        """Test valid country codes pass"""
        assert validate_country_code("US") == "US"
        assert validate_country_code("GB") == "GB"
        assert validate_country_code("FR") == "FR"
        assert validate_country_code("us") == "US"  # Should convert to uppercase
        
    def test_invalid_country_code_length(self):
        """Test invalid country code length is rejected"""
        with pytest.raises(ValidationError):
            validate_country_code("USA")  # 3 letters
            
        with pytest.raises(ValidationError):
            validate_country_code("U")  # 1 letter
            
    def test_invalid_country_code_format(self):
        """Test invalid country code format is rejected"""
        with pytest.raises(ValidationError):
            validate_country_code("U1")  # Contains number
            
        with pytest.raises(ValidationError):
            validate_country_code("U$")  # Contains special char


class TestSQLInjectionDetection:
    """Test SQL injection detection"""
    
    def test_clean_input_passes(self):
        """Test clean input passes SQL injection check"""
        check_sql_injection("normal text")
        check_sql_injection("Transaction 123")
        # Should not raise exception
        
    def test_sql_keywords_detected(self):
        """Test SQL keywords are detected"""
        with pytest.raises(ValidationError):
            check_sql_injection("SELECT * FROM users")
            
        with pytest.raises(ValidationError):
            check_sql_injection("DROP TABLE accounts")
            
        with pytest.raises(ValidationError):
            check_sql_injection("' OR '1'='1")
            
    def test_sql_comment_syntax_detected(self):
        """Test SQL comment syntax is detected"""
        with pytest.raises(ValidationError):
            check_sql_injection("test -- comment")
            
        with pytest.raises(ValidationError):
            check_sql_injection("test /* comment */")


class TestXSSDetection:
    """Test XSS detection"""
    
    def test_clean_input_passes(self):
        """Test clean input passes XSS check"""
        check_xss("normal text")
        check_xss("Transaction 123")
        # Should not raise exception
        
    def test_script_tags_detected(self):
        """Test script tags are detected"""
        with pytest.raises(ValidationError):
            check_xss("<script>alert('xss')</script>")
            
        with pytest.raises(ValidationError):
            check_xss("<SCRIPT>alert('xss')</SCRIPT>")
            
    def test_javascript_protocol_detected(self):
        """Test javascript: protocol is detected"""
        with pytest.raises(ValidationError):
            check_xss("javascript:alert('xss')")
            
    def test_event_handlers_detected(self):
        """Test event handlers are detected"""
        with pytest.raises(ValidationError):
            check_xss("<img onerror='alert(1)'>")
            
        with pytest.raises(ValidationError):
            check_xss("<body onload='alert(1)'>")


class TestPathTraversalDetection:
    """Test path traversal detection"""
    
    def test_clean_input_passes(self):
        """Test clean input passes path traversal check"""
        check_path_traversal("normal/path")
        check_path_traversal("file.txt")
        # Should not raise exception
        
    def test_dot_dot_detected(self):
        """Test .. is detected"""
        with pytest.raises(ValidationError):
            check_path_traversal("../../../etc/passwd")
            
        with pytest.raises(ValidationError):
            check_path_traversal("..\\windows\\system32")
            
    def test_encoded_traversal_detected(self):
        """Test various path traversal patterns are detected"""
        with pytest.raises(ValidationError):
            check_path_traversal("path/../../file")


class TestTextInputValidation:
    """Test comprehensive text input validation"""
    
    def test_valid_text(self):
        """Test valid text passes all checks"""
        result = validate_text_input("Normal transaction", "description")
        assert result == "Normal transaction"
        
    def test_text_length_limit(self):
        """Test text length limit is enforced"""
        long_text = "a" * 1000
        with pytest.raises(ValidationError):
            validate_text_input(long_text, "description", max_length=500)
            
    def test_dangerous_patterns_rejected(self):
        """Test dangerous patterns are rejected"""
        with pytest.raises(ValidationError):
            validate_text_input("SELECT * FROM users", "input")
            
        with pytest.raises(ValidationError):
            validate_text_input("<script>alert(1)</script>", "input")
            
        with pytest.raises(ValidationError):
            validate_text_input("../../etc/passwd", "input")


class TestEmailValidation:
    """Test email validation"""
    
    def test_valid_emails(self):
        """Test valid email addresses pass"""
        assert validate_email("user@example.com") == "user@example.com"
        assert validate_email("test.user@example.co.uk") == "test.user@example.co.uk"
        
    def test_invalid_email_format(self):
        """Test invalid email format is rejected"""
        with pytest.raises(ValidationError):
            validate_email("not-an-email")
            
        with pytest.raises(ValidationError):
            validate_email("@example.com")
            
        with pytest.raises(ValidationError):
            validate_email("user@")
            
    def test_email_too_long(self):
        """Test overly long email is rejected"""
        long_email = "a" * 300 + "@example.com"
        with pytest.raises(ValidationError):
            validate_email(long_email)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
