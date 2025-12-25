"""
Data Validation Utilities
Provides validation functions for financial data.
"""

import re
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any


class DataValidator:
    """Validates financial data for quality and consistency."""
    
    @staticmethod
    def validate_date(date_str: str) -> Tuple[bool, Optional[str]]:
        """Validate date string format.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not date_str:
            return False, "Date is empty"
        
        # Try common date formats
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
        ]
        
        for fmt in date_formats:
            try:
                datetime.strptime(date_str, fmt)
                return True, None
            except ValueError:
                continue
        
        return False, f"Invalid date format: {date_str}"
    
    @staticmethod
    def validate_amount(amount: Any) -> Tuple[bool, Optional[str]]:
        """Validate transaction amount.
        
        Args:
            amount: Amount to validate (can be string, int, or float)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if amount is None:
            return False, "Amount is None"
        
        try:
            amount_float = float(amount)
            
            # Check for reasonable range (not too large)
            if abs(amount_float) > 100000000:  # $100 million
                return False, f"Amount seems unreasonably large: {amount_float}"
            
            return True, None
        except (ValueError, TypeError):
            return False, f"Invalid amount format: {amount}"
    
    @staticmethod
    def validate_account_type(account_type: str) -> Tuple[bool, Optional[str]]:
        """Validate account type.
        
        Args:
            account_type: Account type string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_types = [
            'checking', 'savings', 'credit_card',
            'investment_account', 'roth_ira', 'traditional_ira',
        ]
        
        if account_type and account_type.lower() not in valid_types:
            return False, f"Invalid account type: {account_type}. Valid types: {', '.join(valid_types)}"
        
        return True, None
    
    @staticmethod
    def validate_transaction(transaction: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a transaction dictionary.
        
        Args:
            transaction: Transaction dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate date
        if 'transaction_date' in transaction:
            is_valid, error = DataValidator.validate_date(transaction['transaction_date'])
            if not is_valid:
                errors.append(error)
        
        # Validate amount
        if 'amount' in transaction:
            is_valid, error = DataValidator.validate_amount(transaction['amount'])
            if not is_valid:
                errors.append(error)
        
        # Validate account type
        if 'account_type' in transaction and transaction['account_type']:
            is_valid, error = DataValidator.validate_account_type(transaction['account_type'])
            if not is_valid:
                errors.append(error)
        
        # Check required fields
        required_fields = ['transaction_date', 'amount']
        for field in required_fields:
            if field not in transaction or transaction[field] is None:
                errors.append(f"Missing required field: {field}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate file path exists and is readable.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        import os
        
        if not file_path:
            return False, "File path is empty"
        
        if not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"
        
        if not os.path.isfile(file_path):
            return False, f"Path is not a file: {file_path}"
        
        if not os.access(file_path, os.R_OK):
            return False, f"File is not readable: {file_path}"
        
        return True, None
    
    @staticmethod
    def check_duplicate_transaction(transaction: Dict[str, Any], existing_transactions: List[Dict[str, Any]]) -> bool:
        """Check if a transaction is a duplicate.
        
        Args:
            transaction: Transaction to check
            existing_transactions: List of existing transactions
            
        Returns:
            True if duplicate, False otherwise
        """
        for existing in existing_transactions:
            # Check if same date, amount, and description/merchant
            if (transaction.get('transaction_date') == existing.get('transaction_date') and
                abs(float(transaction.get('amount', 0)) - float(existing.get('amount', 0))) < 0.01 and
                (transaction.get('description') == existing.get('description') or
                 transaction.get('merchant_name') == existing.get('merchant_name'))):
                return True
        
        return False
    
    @staticmethod
    def validate_database_connection(conn) -> Tuple[bool, Optional[str]]:
        """Validate database connection is working.
        
        Args:
            conn: Database connection object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True, None
        except Exception as e:
            return False, f"Database connection error: {str(e)}"

