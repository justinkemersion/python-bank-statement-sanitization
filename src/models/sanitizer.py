import re

class Sanitizer:
    def __init__(self):
        # Common patterns for sensitive financial data
        self.patterns = {
            "account_number": r'\b\d{10,17}\b',  # Generic 10-17 digit number, often used for bank accounts
            "credit_card": r'\b(?:\d[ -]*?){13,16}\b',  # 13-16 digits with optional spaces/hyphens
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',  # Social Security Number (US format)
            # Add more patterns as needed, e.g., routing numbers, specific bank formats
        }

    def sanitize_text(self, text):
        print("Sanitizing text content...")
        sanitized_text = text
        for data_type, pattern in self.patterns.items():
            sanitized_text = re.sub(pattern, f"[{data_type.upper()}_REDACTED]", sanitized_text)
        return sanitized_text