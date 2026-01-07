"""
Unit tests for Security Utilities
Tests for InputSanitizer class and security functions
"""
import pytest
from src.utils.security import (
    InputSanitizer, sanitize, escape_html, safe_filename
)


class TestInputSanitizer:
    """Tests for InputSanitizer class"""
    
    # ========== sanitize_string tests ==========
    
    def test_sanitize_string_strips_whitespace(self):
        """Test that whitespace is stripped"""
        assert InputSanitizer.sanitize_string("  hello  ") == "hello"
        assert InputSanitizer.sanitize_string("\t\ntest\n\t") == "test"
    
    def test_sanitize_string_removes_null_bytes(self):
        """Test that null bytes are removed"""
        assert InputSanitizer.sanitize_string("hello\x00world") == "helloworld"
    
    def test_sanitize_string_limits_length(self):
        """Test that string is truncated to max_length"""
        long_string = "a" * 2000
        result = InputSanitizer.sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_string_handles_none(self):
        """Test that None returns empty string"""
        assert InputSanitizer.sanitize_string(None) == ""
    
    def test_sanitize_string_converts_non_string(self):
        """Test that non-string values are converted"""
        assert InputSanitizer.sanitize_string(123) == "123"
        assert InputSanitizer.sanitize_string(45.67) == "45.67"
    
    # ========== escape_html tests ==========
    
    def test_escape_html_escapes_special_chars(self):
        """Test that HTML special characters are escaped"""
        assert InputSanitizer.escape_html("<script>") == "&lt;script&gt;"
        assert InputSanitizer.escape_html("a & b") == "a &amp; b"
        assert InputSanitizer.escape_html('"quoted"') == "&quot;quoted&quot;"
    
    def test_escape_html_handles_none(self):
        """Test that None returns empty string"""
        assert InputSanitizer.escape_html(None) == ""
    
    def test_escape_html_preserves_safe_text(self):
        """Test that safe text is preserved"""
        assert InputSanitizer.escape_html("Hello World") == "Hello World"
    
    # ========== sanitize_filename tests ==========
    
    def test_sanitize_filename_removes_path_separators(self):
        """Test that path separators are removed"""
        assert InputSanitizer.sanitize_filename("path/to/file.txt") == "pathtofile.txt"
        assert InputSanitizer.sanitize_filename("path\\to\\file.txt") == "pathtofile.txt"
    
    def test_sanitize_filename_removes_dangerous_chars(self):
        """Test that dangerous characters are removed"""
        assert InputSanitizer.sanitize_filename('file<>:"|?*.txt') == "file.txt"
    
    def test_sanitize_filename_handles_empty(self):
        """Test that empty/None returns empty string"""
        assert InputSanitizer.sanitize_filename("") == ""
        assert InputSanitizer.sanitize_filename(None) == ""
    
    def test_sanitize_filename_strips_dots_and_spaces(self):
        """Test that leading/trailing dots and spaces are stripped"""
        assert InputSanitizer.sanitize_filename("...file.txt...") == "file.txt"
        assert InputSanitizer.sanitize_filename("  file.txt  ") == "file.txt"
    
    def test_sanitize_filename_limits_length(self):
        """Test that filename is limited to 255 chars"""
        long_name = "a" * 300 + ".txt"
        result = InputSanitizer.sanitize_filename(long_name)
        assert len(result) <= 255
    
    # ========== SQL injection detection tests ==========
    
    def test_check_sql_injection_detects_keywords(self):
        """Test that SQL keywords are detected"""
        assert InputSanitizer.check_sql_injection("SELECT * FROM users") is True
        assert InputSanitizer.check_sql_injection("DROP TABLE users") is True
        assert InputSanitizer.check_sql_injection("1; DELETE FROM users") is True
    
    def test_check_sql_injection_detects_comments(self):
        """Test that SQL comments are detected"""
        assert InputSanitizer.check_sql_injection("admin'--") is True
        assert InputSanitizer.check_sql_injection("/* comment */") is True
    
    def test_check_sql_injection_detects_or_patterns(self):
        """Test that OR 1=1 patterns are detected"""
        assert InputSanitizer.check_sql_injection("' OR 1=1") is True
        assert InputSanitizer.check_sql_injection("' AND 1=1") is True
    
    def test_check_sql_injection_allows_safe_input(self):
        """Test that safe input passes"""
        assert InputSanitizer.check_sql_injection("John Doe") is False
        assert InputSanitizer.check_sql_injection("test@email.com") is False
        assert InputSanitizer.check_sql_injection("") is False
    
    # ========== Path traversal detection tests ==========
    
    def test_check_path_traversal_detects_patterns(self):
        """Test that path traversal patterns are detected"""
        assert InputSanitizer.check_path_traversal("../../../etc/passwd") is True
        assert InputSanitizer.check_path_traversal("..\\..\\windows") is True
        assert InputSanitizer.check_path_traversal("%2e%2e%2f") is True
    
    def test_check_path_traversal_allows_safe_paths(self):
        """Test that safe paths pass"""
        assert InputSanitizer.check_path_traversal("documents/file.txt") is False
        assert InputSanitizer.check_path_traversal("myfile.pdf") is False
        assert InputSanitizer.check_path_traversal("") is False
    
    # ========== sanitize_for_log tests ==========
    
    def test_sanitize_for_log_masks_passwords(self):
        """Test that passwords are masked in logs"""
        result = InputSanitizer.sanitize_for_log("password=secret123")
        assert "secret123" not in result
        assert "[MASKED]" in result
    
    def test_sanitize_for_log_limits_length(self):
        """Test that log output is limited"""
        long_text = "a" * 500
        result = InputSanitizer.sanitize_for_log(long_text, max_length=100)
        assert len(result) <= 103  # 100 + "..."


class TestConvenienceFunctions:
    """Tests for convenience functions"""
    
    def test_sanitize_function(self):
        """Test sanitize() convenience function"""
        assert sanitize("  test  ") == "test"
        assert sanitize(None) == ""
    
    def test_escape_html_function(self):
        """Test escape_html() convenience function"""
        assert escape_html("<b>") == "&lt;b&gt;"
    
    def test_safe_filename_function(self):
        """Test safe_filename() convenience function"""
        assert safe_filename("../file.txt") == "file.txt"

