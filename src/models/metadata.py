"""
Metadata generation for sanitized files.
Provides AI-friendly context about the sanitization process.
"""

from datetime import datetime
from typing import List, Set


class MetadataGenerator:
    """Generates metadata headers for sanitized files to help AI tools understand the content."""
    
    def __init__(self, include_metadata: bool = True):
        """Initialize the metadata generator.
        
        Args:
            include_metadata: Whether to include metadata headers in sanitized files
        """
        self.include_metadata = include_metadata
        self.tool_version = "1.0.0"
    
    def generate_header(self, detected_patterns: Set[str] = None) -> str:
        """Generate a metadata header explaining the sanitization process.
        
        Args:
            detected_patterns: Set of pattern types that were detected and redacted
            
        Returns:
            str: Formatted metadata header text
        """
        if not self.include_metadata:
            return ""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        header = f"""================================================================================
SANITIZED BANK STATEMENT - AI CONTEXT INFORMATION
================================================================================

This file has been automatically sanitized to remove sensitive personally 
identifiable information (PII) for safe sharing with AI tools and analysis.

SANITIZATION DETAILS:
  - Tool: Bank Statement Sanitizer v{self.tool_version}
  - Processed: {timestamp}
  - Purpose: Privacy protection for AI-assisted financial analysis

WHAT WAS REDACTED:
"""
        
        # List of all possible patterns with descriptions
        pattern_descriptions = {
            "ssn": "Social Security Numbers (SSN) - Format: XXX-XX-XXXX",
            "credit_card": "Credit/Debit Card Numbers - 13-16 digit card numbers",
            "routing_number": "Bank Routing Numbers - 9-digit US bank routing numbers",
            "account_number": "Bank Account Numbers - 10-12 or 17+ digit account numbers",
            "email": "Email Addresses - Standard email format (user@domain.com)",
            "phone_number": "Phone Numbers - Various formats including (XXX) XXX-XXXX",
            "zip_code": "ZIP/Postal Codes - 5 or 9-digit US postal codes",
            "street_address": "Street Addresses - Physical addresses with street names",
        }
        
        if detected_patterns:
            header += "  The following types of sensitive data were detected and redacted:\n"
            for pattern in sorted(detected_patterns):
                desc = pattern_descriptions.get(pattern, pattern)
                header += f"    • {desc}\n"
        else:
            header += "  Sensitive data patterns were automatically detected and redacted.\n"
            header += "  Common redacted data types include:\n"
            for pattern, desc in sorted(pattern_descriptions.items()):
                header += f"    • {desc}\n"
        
        header += """
REDACTION FORMAT:
  Sensitive data has been replaced with placeholders in the format:
  [DATA_TYPE_REDACTED]
  
  Examples:
    - [ACCOUNT_NUMBER_REDACTED] - Original account number was removed
    - [CREDIT_CARD_REDACTED] - Original credit card number was removed
    - [EMAIL_REDACTED] - Original email address was removed

IMPORTANT NOTES FOR AI TOOLS:
  1. The placeholders (e.g., [ACCOUNT_NUMBER_REDACTED]) are NOT actual data
  2. Do NOT attempt to reconstruct, guess, or infer the original values
  3. These placeholders indicate that sensitive information was intentionally removed
  4. The remaining content (dates, amounts, descriptions) is safe for analysis
  5. This sanitization was performed to protect privacy while enabling analysis

USE CASE:
  This file is safe to upload to AI tools (like NotebookLM, ChatGPT, Claude, etc.)
  for purposes such as:
    - Expense tracking and categorization
    - Budget analysis and planning
    - Financial pattern recognition
    - Transaction categorization
    - Spending habit analysis

The original sensitive data cannot be recovered from this file. If you need
the original data, refer to the unsanitized source file.

================================================================================
END OF METADATA - SANITIZED CONTENT FOLLOWS
================================================================================

"""
        
        return header
    
    def generate_footer(self) -> str:
        """Generate a metadata footer.
        
        Returns:
            str: Formatted metadata footer text
        """
        if not self.include_metadata:
            return ""
        
        return f"""

================================================================================
END OF SANITIZED CONTENT
================================================================================
This file was sanitized by Bank Statement Sanitizer v{self.tool_version}
For questions or issues, refer to the tool documentation.
================================================================================
"""

