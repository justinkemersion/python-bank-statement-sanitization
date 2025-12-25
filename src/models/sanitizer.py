import re

class Sanitizer:
    def __init__(self):
        # Common patterns for sensitive financial data
        # Patterns are ordered from most specific to least specific to avoid conflicts
        # Process in order: SSN -> Credit Cards (formatted) -> Routing -> Account Numbers -> Email -> Phone -> Address -> ZIP
        self.patterns = {
            # Social Security Number (US format) - very specific pattern
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            
            # Credit Card Numbers - prioritize formatted patterns (with dashes/spaces)
            # Format: XXXX-XXXX-XXXX-XXXX or XXXX XXXX XXXX XXXX
            # Only match unformatted 13-16 digit numbers if they're NOT already matched as account numbers
            # We'll handle unformatted credit cards separately after account numbers
            "credit_card_formatted": r'\b(?:\d{4}[-\s]){3}\d{1,4}\b',
            
            # US Bank Routing Number - exactly 9 digits (must be processed before account numbers)
            "routing_number": r'\b\d{9}\b',
            
            # Account Numbers - 10-12 digits and 17+ digits (exclude 13-16 which are likely credit cards)
            # This avoids matching credit card numbers as account numbers
            "account_number": r'\b(?:\d{10,12}|\d{17,})\b',
            
            # Unformatted Credit Card Numbers - 13-16 consecutive digits
            # Process after account numbers to catch credit cards that weren't formatted
            "credit_card_unformatted": r'\b\d{13,16}\b',
            
            # Email addresses
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            
            # Phone numbers - various formats, fixed to handle parentheses properly
            # (XXX) XXX-XXXX, XXX-XXX-XXXX, XXX.XXX.XXXX, XXX XXX XXXX, +1 XXX XXX XXXX
            # Note: Use lookbehind/lookahead for word boundaries to handle parentheses
            "phone_number": r'(?<!\d)(?:\+?1[-.\s]?)?(?:\(\d{3}\)\s*\d{3}[-.\s]?\d{4}|\d{3}[-.\s]?\d{3}[-.\s]?\d{4})(?!\d)',
            
            # ZIP codes - US format (5 digits or 5+4 format)
            # Process before street addresses to avoid conflicts
            "zip_code": r'\b\d{5}(?:-\d{4})?\b',
            
            # Street addresses - looks for common patterns like "123 Main St" or "123 Main Street"
            # Exclude ZIP codes by requiring street name before the street type
            "street_address": r'\b\d+\s+[A-Za-z0-9\s]{2,}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Circle|Cir)\b',
        }

    def sanitize_text(self, text, track_patterns=False):
        """Sanitize text by redacting sensitive information.
        
        Args:
            text: The text content to sanitize
            track_patterns: If True, return tuple (sanitized_text, detected_patterns)
            
        Returns:
            str or tuple: The sanitized text, or (sanitized_text, detected_patterns) if track_patterns=True
        """
        print("Sanitizing text content...")
        sanitized_text = text
        detected_patterns = set()
        
        # Use a placeholder system to avoid double-matching
        # Replace matches with unique placeholders first, then replace placeholders with final labels
        placeholder_counter = 0
        placeholders = {}
        
        # Process patterns in specific order to avoid conflicts
        # Order: SSN -> Formatted Credit Cards -> Routing -> Account (excluding 13-16) -> Unformatted Credit Cards (13-16) -> Email -> Phone -> ZIP -> Address
        pattern_order = [
            "ssn",
            "credit_card_formatted",
            "routing_number", 
            "account_number",
            "credit_card_unformatted",
            "email",
            "phone_number",
            "zip_code",
            "street_address",
        ]
        
        for data_type in pattern_order:
            if data_type not in self.patterns:
                continue
                
            pattern = self.patterns[data_type]
            
            # Find all matches
            matches = list(re.finditer(pattern, sanitized_text, flags=re.IGNORECASE))
            
            if matches and track_patterns:
                # Track which patterns were detected
                if data_type in ["credit_card_formatted", "credit_card_unformatted"]:
                    detected_patterns.add("credit_card")
                else:
                    detected_patterns.add(data_type)
            
            # Replace matches in reverse order to preserve positions
            for match in reversed(matches):
                start, end = match.span()
                matched_text = sanitized_text[start:end]
                
                # Skip if this text is already a placeholder (already redacted)
                if matched_text.startswith("__PLACEHOLDER_"):
                    continue
                
                # Determine the redaction label
                if data_type == "credit_card_formatted" or data_type == "credit_card_unformatted":
                    label = "CREDIT_CARD_REDACTED"
                else:
                    label = f"{data_type.upper()}_REDACTED"
                
                # Use placeholder to avoid interfering with subsequent pattern matching
                placeholder = f"__PLACEHOLDER_{placeholder_counter}__"
                placeholders[placeholder] = f"[{label}]"
                placeholder_counter += 1
                
                # Replace the match with placeholder
                sanitized_text = sanitized_text[:start] + placeholder + sanitized_text[end:]
        
        # Replace all placeholders with their final labels
        for placeholder, label in placeholders.items():
            sanitized_text = sanitized_text.replace(placeholder, label)
        
        if track_patterns:
            return sanitized_text, detected_patterns
        return sanitized_text