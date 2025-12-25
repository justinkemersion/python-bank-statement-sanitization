import re

class Sanitizer:
    def __init__(self):
        # Common patterns for sensitive financial data
        # Patterns are ordered from most specific to least specific to avoid conflicts
        self.patterns = {
            # Social Security Number (US format) - very specific pattern
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            
            # Credit Card Numbers - 4 groups of 4 digits with spaces/hyphens, or 13-16 consecutive digits
            # Format: XXXX-XXXX-XXXX-XXXX or XXXX XXXX XXXX XXXX or XXXXXXXXXXXXXXXX
            "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{1,4}\b|\b\d{13,16}\b',
            
            # US Bank Routing Number - exactly 9 digits
            "routing_number": r'\b\d{9}\b',
            
            # Account Numbers - 10-17 digits, but more conservative to reduce false positives
            # Look for patterns that might indicate account numbers (context-aware would be better, but this is a start)
            "account_number": r'\b\d{10,17}\b',
            
            # Email addresses
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            
            # Phone numbers - various formats
            # (XXX) XXX-XXXX, XXX-XXX-XXXX, XXX.XXX.XXXX, XXX XXX XXXX, +1 XXX XXX XXXX
            "phone_number": r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            
            # Street addresses - looks for common patterns like "123 Main St" or "123 Main Street"
            # This is a simplified pattern and may have false positives
            "street_address": r'\b\d+\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Circle|Cir)\b',
            
            # ZIP codes - US format (5 digits or 5+4 format)
            "zip_code": r'\b\d{5}(?:-\d{4})?\b',
        }

    def sanitize_text(self, text):
        """Sanitize text by redacting sensitive information.
        
        Args:
            text: The text content to sanitize
            
        Returns:
            str: The sanitized text with sensitive data replaced by placeholders
        """
        print("Sanitizing text content...")
        sanitized_text = text
        
        # Process patterns in order (most specific first)
        for data_type, pattern in self.patterns.items():
            if data_type == "account_number":
                # For account numbers, use a more conservative approach
                # Replace all matches, but this pattern is still quite broad
                # In a production system, you'd want more sophisticated detection
                sanitized_text = re.sub(pattern, f"[{data_type.upper()}_REDACTED]", sanitized_text)
            else:
                sanitized_text = re.sub(pattern, f"[{data_type.upper()}_REDACTED]", sanitized_text, flags=re.IGNORECASE)
        
        return sanitized_text