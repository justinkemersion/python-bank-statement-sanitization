"""
Investment Account Extractor
Extracts investment account data from statements (portfolio value, holdings, transactions).
"""

import re
from datetime import datetime
from typing import Dict, Optional, Any, List
from decimal import Decimal


class InvestmentExtractor:
    """Extracts investment account data from statements."""
    
    def __init__(self):
        """Initialize the investment extractor."""
        # Patterns for investment account detection
        self.account_type_patterns = {
            'roth_ira': [
                r'roth\s+ira',
                r'roth\s+individual\s+retirement',
            ],
            'traditional_ira': [
                r'traditional\s+ira',
                r'rollover\s+ira',
                r'ira\s+account',
                r'individual\s+retirement\s+account',
            ],
            'investment_account': [
                r'investment\s+account',
                r'brokerage\s+account',
                r'securities\s+account',
                r'trading\s+account',
            ],
        }
        
        # Patterns for portfolio value
        self.portfolio_patterns = [
            r'portfolio\s+value[:\s]+\$?([\d,]+\.?\d*)',
            r'account\s+value[:\s]+\$?([\d,]+\.?\d*)',
            r'total\s+value[:\s]+\$?([\d,]+\.?\d*)',
            r'account\s+balance[:\s]+\$?([\d,]+\.?\d*)',
            r'total\s+assets[:\s]+\$?([\d,]+\.?\d*)',
        ]
        
        # Patterns for holdings (securities)
        self.holding_patterns = [
            # Format: TICKER  QTY  VALUE
            r'([A-Z]{1,5})\s+(\d+\.?\d*)\s+\$?([\d,]+\.?\d*)',
            # Format: SECURITY NAME - QTY shares - $VALUE
            r'([A-Z][A-Za-z\s&,\.]+)\s+-\s+(\d+\.?\d*)\s+shares?\s+-\s+\$?([\d,]+\.?\d*)',
            # Format: SECURITY (TICKER) - QTY - $VALUE
            r'([A-Z][A-Za-z\s&,\.]+)\s+\(([A-Z]{1,5})\)\s+(\d+\.?\d*)\s+\$?([\d,]+\.?\d*)',
        ]
        
        # Patterns for transactions
        self.transaction_patterns = {
            'buy': [
                r'buy\s+(\d+\.?\d*)\s+([A-Z]{1,5})\s+@\s+\$?([\d,]+\.?\d*)',
                r'purchase\s+(\d+\.?\d*)\s+([A-Z]{1,5})',
                r'bought\s+(\d+\.?\d*)\s+([A-Z]{1,5})',
            ],
            'sell': [
                r'sell\s+(\d+\.?\d*)\s+([A-Z]{1,5})\s+@\s+\$?([\d,]+\.?\d*)',
                r'sold\s+(\d+\.?\d*)\s+([A-Z]{1,5})',
            ],
            'dividend': [
                r'dividend\s+([A-Z]{1,5})\s+\$?([\d,]+\.?\d*)',
                r'dividend\s+payment\s+\$?([\d,]+\.?\d*)',
            ],
            'contribution': [
                r'contribution\s+\$?([\d,]+\.?\d*)',
                r'ira\s+contribution\s+\$?([\d,]+\.?\d*)',
                r'contributed\s+\$?([\d,]+\.?\d*)',
            ],
            'withdrawal': [
                r'withdrawal\s+\$?([\d,]+\.?\d*)',
                r'withdrew\s+\$?([\d,]+\.?\d*)',
                r'distribution\s+\$?([\d,]+\.?\d*)',
            ],
        }
        
        # Compile patterns
        self.compiled_account_patterns = {}
        for account_type, pattern_list in self.account_type_patterns.items():
            self.compiled_account_patterns[account_type] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                for pattern in pattern_list
            ]
        
        self.compiled_portfolio_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
            for pattern in self.portfolio_patterns
        ]
        
        self.compiled_holding_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
            for pattern in self.holding_patterns
        ]
        
        self.compiled_transaction_patterns = {}
        for trans_type, pattern_list in self.transaction_patterns.items():
            self.compiled_transaction_patterns[trans_type] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                for pattern in pattern_list
            ]
    
    def detect_account_type(self, text: str, source_file: str) -> Optional[str]:
        """Detect investment account type from statement.
        
        Args:
            text: Statement text content
            source_file: Source file name
            
        Returns:
            Account type string (roth_ira, traditional_ira, investment_account) or None
        """
        text_lower = text.lower()
        filename_lower = source_file.lower()
        
        # Check filename first
        for account_type, patterns in self.compiled_account_patterns.items():
            for pattern in patterns:
                if pattern.search(filename_lower):
                    return account_type
        
        # Check text content
        for account_type, patterns in self.compiled_account_patterns.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    return account_type
        
        return None
    
    def is_investment_account(self, text: str, source_file: str) -> bool:
        """Check if statement is from an investment account.
        
        Args:
            text: Statement text content
            source_file: Source file name
            
        Returns:
            True if this appears to be an investment account statement
        """
        account_type = self.detect_account_type(text, source_file)
        if account_type:
            return True
        
        # Check for investment-related keywords
        text_lower = text.lower()
        investment_keywords = [
            'portfolio', 'securities', 'stocks', 'shares', 'holdings',
            'dividend', 'capital gains', 'cost basis', 'market value',
            'brokerage', 'trading', 'equity', 'mutual fund', 'etf'
        ]
        
        keyword_count = sum(1 for keyword in investment_keywords if keyword in text_lower)
        return keyword_count >= 3
    
    def extract_portfolio_value(self, text: str) -> Optional[float]:
        """Extract portfolio/account value from statement.
        
        Args:
            text: Statement text content
            
        Returns:
            Portfolio value as float, or None if not found
        """
        for pattern in self.compiled_portfolio_patterns:
            match = pattern.search(text)
            if match:
                try:
                    value_str = match.group(1) if match.groups() else match.group(0)
                    value_str = value_str.replace(',', '').replace('$', '')
                    return float(value_str)
                except (ValueError, IndexError):
                    continue
        return None
    
    def extract_holdings(self, text: str) -> List[Dict[str, Any]]:
        """Extract holdings (securities) from statement.
        
        Args:
            text: Statement text content
            
        Returns:
            List of holding dictionaries
        """
        holdings = []
        
        # Look for holdings table/section
        # Common patterns: "Holdings", "Positions", "Securities"
        holdings_section = None
        for section_marker in [r'holdings', r'positions', r'securities', r'portfolio']:
            match = re.search(rf'{section_marker}.*?(?=\n\n|\n[A-Z]{{3,}}|$)', text, re.IGNORECASE | re.DOTALL)
            if match:
                holdings_section = match.group(0)
                break
        
        if not holdings_section:
            holdings_section = text  # Search entire text
        
        # Try to extract holdings using patterns
        for pattern in self.compiled_holding_patterns:
            matches = pattern.finditer(holdings_section)
            for match in matches:
                try:
                    groups = match.groups()
                    if len(groups) >= 3:
                        # Try different group combinations
                        if len(groups) == 3:
                            # Format: TICKER QTY VALUE
                            ticker = groups[0].strip()
                            quantity = float(groups[1].replace(',', ''))
                            value = float(groups[2].replace(',', '').replace('$', ''))
                            security_name = ticker
                        elif len(groups) == 4:
                            # Format: NAME (TICKER) QTY VALUE
                            security_name = groups[0].strip()
                            ticker = groups[1].strip()
                            quantity = float(groups[2].replace(',', ''))
                            value = float(groups[3].replace(',', '').replace('$', ''))
                        else:
                            continue
                        
                        holdings.append({
                            'ticker': ticker if len(ticker) <= 5 else None,
                            'security_name': security_name,
                            'quantity': quantity,
                            'market_value': value,
                        })
                except (ValueError, IndexError):
                    continue
        
        return holdings
    
    def extract_transactions(self, text: str, statement_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract investment transactions from statement.
        
        Args:
            text: Statement text content
            statement_date: Statement date (for transactions without explicit dates)
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        lines = text.split('\n')
        
        # Date pattern
        date_pattern = re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}')
        
        current_date = statement_date
        
        for line in lines:
            line_lower = line.lower()
            
            # Update current date if found
            date_match = date_pattern.search(line)
            if date_match:
                current_date = date_match.group()
            
            # Check for each transaction type
            for trans_type, patterns in self.compiled_transaction_patterns.items():
                for pattern in patterns:
                    match = pattern.search(line_lower)
                    if match:
                        try:
                            groups = match.groups()
                            transaction = {
                                'transaction_date': current_date,
                                'transaction_type': trans_type,
                                'amount': None,
                                'security_ticker': None,
                                'quantity': None,
                                'price': None,
                            }
                            
                            if trans_type in ['buy', 'sell']:
                                if len(groups) >= 3:
                                    transaction['quantity'] = float(groups[0].replace(',', ''))
                                    transaction['security_ticker'] = groups[1].strip().upper()
                                    transaction['price'] = float(groups[2].replace(',', '').replace('$', ''))
                                    transaction['amount'] = transaction['quantity'] * transaction['price']
                            elif trans_type == 'dividend':
                                if len(groups) >= 2:
                                    transaction['security_ticker'] = groups[0].strip().upper() if groups[0] else None
                                    transaction['amount'] = float(groups[-1].replace(',', '').replace('$', ''))
                            elif trans_type in ['contribution', 'withdrawal']:
                                if groups:
                                    transaction['amount'] = float(groups[0].replace(',', '').replace('$', ''))
                            
                            if transaction['amount'] or transaction['quantity']:
                                transactions.append(transaction)
                                break
                        except (ValueError, IndexError):
                            continue
        
        return transactions
    
    def extract_statement_date(self, text: str) -> Optional[str]:
        """Extract statement date.
        
        Args:
            text: Statement text content
            
        Returns:
            Statement date as string, or None
        """
        date_patterns = [
            r'statement\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'as\s+of[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'period\s+ending[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]
        
        for pattern_str in date_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            match = pattern.search(text)
            if match:
                return match.group(1)
        
        return None
    
    def extract(self, text: str, source_file: str, bank_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Extract investment account data from statement.
        
        Args:
            text: Statement text content
            source_file: Source file name
            bank_name: Bank/brokerage name (e.g., 'Charles Schwab')
            
        Returns:
            Dictionary with investment account data, or None if not an investment account
        """
        if not text:
            return None
        
        # Check if this is an investment account
        if not self.is_investment_account(text, source_file):
            return None
        
        # Detect account type
        account_type = self.detect_account_type(text, source_file)
        if not account_type:
            account_type = 'investment_account'  # Default
        
        # Extract data
        statement_date = self.extract_statement_date(text)
        portfolio_value = self.extract_portfolio_value(text)
        holdings = self.extract_holdings(text)
        transactions = self.extract_transactions(text, statement_date)
        
        # Validate we extracted something
        if not portfolio_value and not holdings and not transactions:
            return None
        
        return {
            'source_file': source_file,
            'account_type': account_type,
            'bank_name': bank_name,
            'statement_date': statement_date,
            'portfolio_value': portfolio_value,
            'holdings': holdings,
            'transactions': transactions,
        }

