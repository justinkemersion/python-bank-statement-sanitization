"""
Database Exporter
Exports sanitized financial data to SQLite database for tax analysis and AI review.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import re


class DatabaseExporter:
    """Exports sanitized financial data to SQLite database."""
    
    def __init__(self, db_path: str):
        """Initialize the database exporter.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def create_schema(self):
        """Create the database schema for financial data."""
        cursor = self.conn.cursor()
        
        # Transactions table - main table for all financial transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                transaction_date TEXT,
                amount REAL,
                description TEXT,
                category TEXT,
                account_type TEXT,
                transaction_type TEXT,
                reference_number TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Files table - track which files have been imported
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS imported_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_type TEXT,
                import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                row_count INTEGER,
                notes TEXT
            )
        """)
        
        # Metadata table - store sanitization metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transaction_date ON transactions(transaction_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_amount ON transactions(amount)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON transactions(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_file ON transactions(source_file)")
        
        self.conn.commit()
    
    def extract_transactions_from_text(self, text: str, source_file: str) -> List[Dict[str, Any]]:
        """Extract transaction-like data from sanitized text.
        
        This is a basic implementation that looks for common patterns.
        For production, you'd want more sophisticated parsing.
        
        Args:
            text: Sanitized text content
            source_file: Source file name
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        lines = text.split('\n')
        
        # Look for date patterns and amounts
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        amount_pattern = r'[\$]?([\d,]+\.?\d*)'
        
        current_date = None
        for line in lines:
            line = line.strip()
            if not line or line.startswith('[') or 'REDACTED' in line:
                continue
            
            # Try to find dates
            date_match = re.search(date_pattern, line)
            if date_match:
                current_date = date_match.group()
            
            # Try to find amounts
            amount_matches = re.findall(amount_pattern, line)
            for amount_str in amount_matches:
                try:
                    amount = float(amount_str.replace(',', ''))
                    # Only consider significant amounts (likely transactions)
                    if abs(amount) > 0.01:
                        transaction = {
                            'source_file': source_file,
                            'transaction_date': current_date or None,
                            'amount': amount,
                            'description': line[:200],  # First 200 chars
                            'category': None,
                            'account_type': None,
                            'transaction_type': 'debit' if amount < 0 else 'credit',
                            'reference_number': None,
                            'notes': None
                        }
                        transactions.append(transaction)
                except ValueError:
                    continue
        
        return transactions
    
    def extract_transactions_from_csv(self, rows: List[Dict], source_file: str) -> List[Dict[str, Any]]:
        """Extract transactions from CSV data.
        
        Args:
            rows: List of CSV row dictionaries
            source_file: Source file name
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        
        # Common column name mappings
        date_columns = ['date', 'transaction_date', 'post_date', 'posted_date']
        amount_columns = ['amount', 'transaction_amount', 'debit', 'credit', 'balance']
        desc_columns = ['description', 'memo', 'details', 'transaction_description']
        
        for row in rows:
            transaction = {
                'source_file': source_file,
                'transaction_date': None,
                'amount': None,
                'description': None,
                'category': None,
                'account_type': None,
                'transaction_type': None,
                'reference_number': None,
                'notes': None
            }
            
            # Find date column
            for col in date_columns:
                if col in row and row[col]:
                    transaction['transaction_date'] = str(row[col])
                    break
            
            # Find amount column
            for col in amount_columns:
                if col in row and row[col]:
                    try:
                        amount_str = str(row[col]).replace('$', '').replace(',', '').strip()
                        transaction['amount'] = float(amount_str)
                        transaction['transaction_type'] = 'debit' if transaction['amount'] < 0 else 'credit'
                    except (ValueError, AttributeError):
                        pass
                    break
            
            # Find description column
            for col in desc_columns:
                if col in row and row[col]:
                    transaction['description'] = str(row[col])[:500]  # Limit length
                    break
            
            # Only add if we have at least a date or amount
            if transaction['transaction_date'] or transaction['amount']:
                transactions.append(transaction)
        
        return transactions
    
    def extract_transactions_from_dataframe(self, df, source_file: str) -> List[Dict[str, Any]]:
        """Extract transactions from pandas DataFrame.
        
        Args:
            df: pandas DataFrame
            source_file: Source file name
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        
        # Convert DataFrame to list of dicts and use CSV extraction logic
        rows = df.to_dict('records')
        return self.extract_transactions_from_csv(rows, source_file)
    
    def insert_transactions(self, transactions: List[Dict[str, Any]]):
        """Insert transactions into the database.
        
        Args:
            transactions: List of transaction dictionaries
        """
        if not transactions:
            return
        
        cursor = self.conn.cursor()
        
        for transaction in transactions:
            cursor.execute("""
                INSERT INTO transactions 
                (source_file, transaction_date, amount, description, category, 
                 account_type, transaction_type, reference_number, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.get('source_file'),
                transaction.get('transaction_date'),
                transaction.get('amount'),
                transaction.get('description'),
                transaction.get('category'),
                transaction.get('account_type'),
                transaction.get('transaction_type'),
                transaction.get('reference_number'),
                transaction.get('notes')
            ))
        
        self.conn.commit()
    
    def record_file_import(self, file_path: str, file_type: str, row_count: int, notes: str = None):
        """Record that a file has been imported.
        
        Args:
            file_path: Path to the imported file
            file_type: Type of file (pdf, csv, xlsx, etc.)
            row_count: Number of transactions imported
            notes: Optional notes about the import
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO imported_files (file_path, file_type, row_count, notes)
            VALUES (?, ?, ?, ?)
        """, (file_path, file_type, row_count, notes))
        self.conn.commit()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total transactions
        cursor.execute("SELECT COUNT(*) FROM transactions")
        stats['total_transactions'] = cursor.fetchone()[0]
        
        # Date range
        cursor.execute("SELECT MIN(transaction_date), MAX(transaction_date) FROM transactions WHERE transaction_date IS NOT NULL")
        date_range = cursor.fetchone()
        stats['date_range'] = {'min': date_range[0], 'max': date_range[1]}
        
        # Total amount
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE amount IS NOT NULL")
        total = cursor.fetchone()[0]
        stats['total_amount'] = total if total else 0
        
        # Files imported
        cursor.execute("SELECT COUNT(*) FROM imported_files")
        stats['files_imported'] = cursor.fetchone()[0]
        
        return stats

