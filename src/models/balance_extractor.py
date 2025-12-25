"""
Balance Extractor
Extracts account balances from bank statements (PDF, TXT, CSV).
"""

import re
from datetime import datetime
from typing import Dict, Optional, Any, List
from decimal import Decimal


class BalanceExtractor:
    """Extracts account balance information from statements."""
    
    def __init__(self):
        """Initialize the balance extractor."""
        # Patterns for balance extraction
        self.balance_patterns = {
            # Credit card balances
            'credit_card_balance': [
                r'(?:new\s+)?balance[:\s]+\$?([\d,]+\.?\d*)',
                r'(?:current\s+)?balance[:\s]+\$?([\d,]+\.?\d*)',
                r'account\s+balance[:\s]+\$?([\d,]+\.?\d*)',
                r'total\s+balance[:\s]+\$?([\d,]+\.?\d*)',
                r'outstanding\s+balance[:\s]+\$?([\d,]+\.?\d*)',
            ],
            # Available credit
            'available_credit': [
                r'available\s+credit[:\s]+\$?([\d,]+\.?\d*)',
                r'credit\s+available[:\s]+\$?([\d,]+\.?\d*)',
                r'available\s+to\s+spend[:\s]+\$?([\d,]+\.?\d*)',
            ],
            # Credit limit
            'credit_limit': [
                r'credit\s+limit[:\s]+\$?([\d,]+\.?\d*)',
                r'credit\s+line[:\s]+\$?([\d,]+\.?\d*)',
                r'total\s+credit\s+limit[:\s]+\$?([\d,]+\.?\d*)',
            ],
            # Checking/savings balances
            'account_balance': [
                r'account\s+balance[:\s]+\$?([\d,]+\.?\d*)',
                r'ending\s+balance[:\s]+\$?([\d,]+\.?\d*)',
                r'current\s+balance[:\s]+\$?([\d,]+\.?\d*)',
                r'balance[:\s]+\$?([\d,]+\.?\d*)',
                r'available\s+balance[:\s]+\$?([\d,]+\.?\d*)',
            ],
            # Statement date
            'statement_date': [
                r'statement\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'as\s+of[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'statement\s+period[:\s]+.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            # Minimum payment
            'minimum_payment': [
                r'minimum\s+payment[:\s]+\$?([\d,]+\.?\d*)',
                r'min\s+payment[:\s]+\$?([\d,]+\.?\d*)',
                r'payment\s+due[:\s]+\$?([\d,]+\.?\d*)',
            ],
            # Payment due date
            'payment_due_date': [
                r'payment\s+due\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'due\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'payment\s+due[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            # APR/Interest rate
            'apr': [
                r'apr[:\s]+([\d,]+\.?\d*)%?',
                r'annual\s+percentage\s+rate[:\s]+([\d,]+\.?\d*)%?',
                r'interest\s+rate[:\s]+([\d,]+\.?\d*)%?',
            ],
        }
        
        # Compile patterns
        self.compiled_patterns = {}
        for field, pattern_list in self.balance_patterns.items():
            self.compiled_patterns[field] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                for pattern in pattern_list
            ]
    
    def _extract_value(self, text: str, field: str) -> Optional[float]:
        """Extract a numeric value for a field.
        
        Args:
            text: Text to search
            field: Field name to extract
            
        Returns:
            Extracted value as float, or None if not found
        """
        if field not in self.compiled_patterns:
            return None
        
        for pattern in self.compiled_patterns[field]:
            match = pattern.search(text)
            if match:
                try:
                    value_str = match.group(1) if match.groups() else match.group(0)
                    value_str = value_str.replace(',', '').replace('$', '')
                    return float(value_str)
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_date(self, text: str, field: str) -> Optional[str]:
        """Extract a date value for a field.
        
        Args:
            text: Text to search
            field: Field name to extract
            
        Returns:
            Extracted date as string (YYYY-MM-DD format if possible), or None
        """
        if field not in self.compiled_patterns:
            return None
        
        for pattern in self.compiled_patterns[field]:
            match = pattern.search(text)
            if match:
                try:
                    date_str = match.group(1) if match.groups() else match.group(0)
                    # Try to normalize date format
                    # Common formats: MM/DD/YYYY, DD/MM/YYYY, MM-DD-YYYY
                    date_str = date_str.strip()
                    return date_str
                except (IndexError):
                    continue
        return None
    
    def extract_balance(self, text: str, source_file: str, account_type: Optional[str] = None, 
                       bank_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Extract balance information from statement text.
        
        Args:
            text: Statement text content
            source_file: Source file name
            account_type: Account type (checking, savings, credit_card)
            bank_name: Bank/issuer name
            
        Returns:
            Dictionary with balance data, or None if extraction fails
        """
        if not text:
            return None
        
        # Normalize text
        text = re.sub(r'\s+', ' ', text)
        
        # Extract statement date
        statement_date = self._extract_date(text, 'statement_date')
        
        # Extract based on account type
        balance = None
        available_credit = None
        credit_limit = None
        
        if account_type == 'credit_card':
            # For credit cards, look for balance, available credit, and limit
            balance = self._extract_value(text, 'credit_card_balance')
            available_credit = self._extract_value(text, 'available_credit')
            credit_limit = self._extract_value(text, 'credit_limit')
            
            # If we have available credit and limit, calculate balance
            if balance is None and available_credit is not None and credit_limit is not None:
                balance = credit_limit - available_credit
        else:
            # For checking/savings, look for account balance
            balance = self._extract_value(text, 'account_balance')
        
        # Extract payment information (for credit cards)
        minimum_payment = self._extract_value(text, 'minimum_payment')
        payment_due_date = self._extract_date(text, 'payment_due_date')
        apr = self._extract_value(text, 'apr')
        
        # Validate that we extracted at least a balance
        if balance is None:
            return None
        
        return {
            'source_file': source_file,
            'statement_date': statement_date,
            'balance': balance,
            'available_credit': available_credit,
            'credit_limit': credit_limit,
            'minimum_payment': minimum_payment,
            'payment_due_date': payment_due_date,
            'apr': apr,
            'account_type': account_type,
            'bank_name': bank_name,
        }

