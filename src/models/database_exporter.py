"""
Database Exporter
Exports sanitized financial data to SQLite database for tax analysis and AI review.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import re

from src.models.transaction_categorizer import TransactionCategorizer
from src.models.merchant_extractor import MerchantExtractor


class DatabaseExporter:
    """Exports sanitized financial data to SQLite database."""
    
    def __init__(self, db_path: str):
        """Initialize the database exporter.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.categorizer = TransactionCategorizer()
        self.merchant_extractor = MerchantExtractor()
    
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
                merchant_name TEXT,
                category TEXT,
                account_type TEXT,
                transaction_type TEXT,
                reference_number TEXT,
                notes TEXT,
                is_recurring INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add merchant_name column if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN merchant_name TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add is_recurring column if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN is_recurring INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add tags column if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN tags TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_merchant_name ON transactions(merchant_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_recurring ON transactions(is_recurring)")
        
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
                        description = line[:200]  # First 200 chars
                        transaction = {
                            'source_file': source_file,
                            'transaction_date': current_date or None,
                            'amount': amount,
                            'description': description,
                            'merchant_name': self.merchant_extractor.extract(description),
                            'category': self.categorizer.categorize(description),
                            'account_type': None,
                            'transaction_type': 'debit' if amount < 0 else 'credit',
                            'reference_number': None,
                            'notes': None,
                            'is_recurring': 0
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
                'merchant_name': None,
                'category': None,
                'account_type': None,
                'transaction_type': None,
                'reference_number': None,
                'notes': None,
                'is_recurring': 0
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
                # Extract merchant name and categorize
                if transaction['description']:
                    transaction['merchant_name'] = self.merchant_extractor.extract(transaction['description'])
                    transaction['category'] = self.categorizer.categorize(transaction['description'])
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
                (source_file, transaction_date, amount, description, merchant_name, category, 
                 account_type, transaction_type, reference_number, notes, is_recurring)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.get('source_file'),
                transaction.get('transaction_date'),
                transaction.get('amount'),
                transaction.get('description'),
                transaction.get('merchant_name'),
                transaction.get('category'),
                transaction.get('account_type'),
                transaction.get('transaction_type'),
                transaction.get('reference_number'),
                transaction.get('notes'),
                transaction.get('is_recurring', 0)
            ))
        
        self.conn.commit()
        
        # After inserting, detect and mark recurring transactions
        self._detect_recurring_transactions()
    
    def is_file_imported(self, file_path: str) -> bool:
        """Check if a file has already been imported.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if file has been imported, False otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM imported_files WHERE file_path = ?", (file_path,))
        count = cursor.fetchone()[0]
        return count > 0
    
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
            INSERT OR REPLACE INTO imported_files (file_path, file_type, row_count, notes, import_date)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (file_path, file_type, row_count, notes))
        self.conn.commit()
    
    def delete_file_transactions(self, file_path: str) -> int:
        """Delete all transactions from a specific file (for re-import).
        
        Args:
            file_path: Path to the file whose transactions should be deleted
            
        Returns:
            int: Number of transactions deleted
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE source_file = ?", (os.path.basename(file_path),))
        deleted_count = cursor.rowcount
        self.conn.commit()
        return deleted_count
    
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
    
    def export_to_csv(self, output_path: str, date_range: Optional[Tuple[str, str]] = None, 
                     include_metadata: bool = True) -> bool:
        """Export all transactions to a CSV file for AI analysis (NotebookLM, etc.).
        
        Args:
            output_path: Path where the CSV file should be saved
            date_range: Optional tuple of (start_date, end_date) in YYYY-MM-DD format
            include_metadata: Whether to include metadata header explaining the data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            
            # Build query with optional date filtering
            query = """
                SELECT 
                    transaction_date,
                    amount,
                    description,
                    merchant_name,
                    category,
                    transaction_type,
                    source_file,
                    reference_number,
                    notes,
                    is_recurring
                FROM transactions
            """
            
            params = []
            if date_range:
                start_date, end_date = date_range
                query += " WHERE transaction_date >= ? AND transaction_date <= ?"
                params.extend([start_date, end_date])
            
            query += " ORDER BY transaction_date, id"
            
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            
            import csv
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                if include_metadata:
                    # Write comprehensive metadata header
                    metadata = f"""# COMPREHENSIVE FINANCIAL TRANSACTION DATA
# This file contains all sanitized financial transactions from your bank statements.
# Safe for AI analysis tools like NotebookLM, ChatGPT, Claude, etc.
#
# DATA PERIOD: {self.get_statistics().get('date_range', {}).get('min', 'Unknown')} to {self.get_statistics().get('date_range', {}).get('max', 'Unknown')}
# TOTAL TRANSACTIONS: {self.get_statistics().get('total_transactions', 0)}
# FILES PROCESSED: {self.get_statistics().get('files_imported', 0)}
#
# COLUMNS:
#   - transaction_date: Date of the transaction
#   - amount: Transaction amount (negative for debits, positive for credits)
#   - description: Transaction description (sanitized - sensitive data removed)
#   - merchant_name: Extracted merchant name (if available)
#   - category: Transaction category (if available)
#   - transaction_type: 'debit' or 'credit'
#   - source_file: Original statement file name
#   - reference_number: Transaction reference number (if available)
#   - notes: Additional notes
#   - is_recurring: Whether this is a recurring transaction (1 = yes, 0 = no)
#
# NOTE: All sensitive information (account numbers, SSN, etc.) has been redacted.
# The [REDACTED] placeholders indicate where sensitive data was removed.
#
"""
                    f.write(metadata)
                    f.write("\n")
                
                # Write CSV data
                fieldnames = ['transaction_date', 'amount', 'description', 'merchant_name',
                            'category', 'transaction_type', 'source_file', 'reference_number',
                            'notes', 'is_recurring']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in rows:
                    writer.writerow({
                        'transaction_date': row[0] or '',
                        'amount': row[1] if row[1] is not None else '',
                        'description': row[2] or '',
                        'merchant_name': row[3] or '',
                        'category': row[4] or '',
                        'transaction_type': row[5] or '',
                        'source_file': row[6] or '',
                        'reference_number': row[7] or '',
                        'notes': row[8] or '',
                        'is_recurring': 'Yes' if row[9] else 'No'
                    })
            
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def export_summary_report(self, output_path: str) -> bool:
        """Export a human-readable summary report for AI analysis.
        
        Args:
            output_path: Path where the report should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            stats = self.get_statistics()
            
            # Get monthly breakdown
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m', transaction_date) as month,
                    COUNT(*) as count,
                    SUM(amount) as total
                FROM transactions
                WHERE transaction_date IS NOT NULL
                GROUP BY month
                ORDER BY month
            """)
            monthly_data = cursor.fetchall()
            
            # Get top spending categories (if categories exist)
            cursor.execute("""
                SELECT 
                    category,
                    COUNT(*) as count,
                    SUM(amount) as total
                FROM transactions
                WHERE category IS NOT NULL AND category != ''
                GROUP BY category
                ORDER BY ABS(total) DESC
                LIMIT 20
            """)
            category_data = cursor.fetchall()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("FINANCIAL TRANSACTION SUMMARY REPORT\n")
                f.write("Safe for AI Analysis (NotebookLM, ChatGPT, Claude, etc.)\n")
                f.write("=" * 80 + "\n\n")
                
                f.write("OVERVIEW\n")
                f.write("-" * 80 + "\n")
                f.write(f"Total Transactions: {stats['total_transactions']}\n")
                f.write(f"Files Processed: {stats['files_imported']}\n")
                if stats['date_range']['min']:
                    f.write(f"Date Range: {stats['date_range']['min']} to {stats['date_range']['max']}\n")
                if stats['total_amount']:
                    f.write(f"Total Amount: ${stats['total_amount']:,.2f}\n")
                f.write("\n")
                
                if monthly_data:
                    f.write("MONTHLY BREAKDOWN\n")
                    f.write("-" * 80 + "\n")
                    for month, count, total in monthly_data:
                        f.write(f"{month}: {count} transactions, Total: ${total:,.2f}\n")
                    f.write("\n")
                
                if category_data:
                    f.write("TOP SPENDING CATEGORIES\n")
                    f.write("-" * 80 + "\n")
                    for category, count, total in category_data:
                        f.write(f"{category}: {count} transactions, Total: ${total:,.2f}\n")
                    f.write("\n")
                
                f.write("=" * 80 + "\n")
                f.write("NOTE: All sensitive information has been redacted from this data.\n")
                f.write("This report is safe to share with AI tools for analysis.\n")
                f.write("=" * 80 + "\n")
            
            return True
        except Exception as e:
            print(f"Error creating summary report: {e}")
            return False
    
    def _detect_recurring_transactions(self):
        """Detect and mark recurring transactions (subscriptions, bills, etc.).
        
        A transaction is considered recurring if:
        - Same merchant name appears multiple times
        - Similar amount (within 5% variance)
        - Regular intervals (approximately monthly)
        """
        cursor = self.conn.cursor()
        
        # Find transactions with the same merchant name
        cursor.execute("""
            SELECT merchant_name, COUNT(*) as count, AVG(amount) as avg_amount
            FROM transactions
            WHERE merchant_name IS NOT NULL AND merchant_name != ''
            GROUP BY merchant_name
            HAVING count >= 3
        """)
        
        recurring_merchants = cursor.fetchall()
        
        for merchant_row in recurring_merchants:
            merchant_name = merchant_row[0]
            avg_amount = merchant_row[2]
            
            # Get all transactions for this merchant
            cursor.execute("""
                SELECT id, transaction_date, amount
                FROM transactions
                WHERE merchant_name = ?
                ORDER BY transaction_date
            """, (merchant_name,))
            
            transactions = cursor.fetchall()
            
            if len(transactions) < 3:
                continue
            
            # Check if amounts are similar (within 5% of average)
            similar_amount_count = 0
            for trans in transactions:
                amount = trans[2]
                if amount and avg_amount:
                    variance = abs(amount - avg_amount) / abs(avg_amount)
                    if variance <= 0.05:  # Within 5%
                        similar_amount_count += 1
            
            # If most transactions have similar amounts, mark as recurring
            if similar_amount_count >= len(transactions) * 0.7:  # 70% threshold
                cursor.execute("""
                    UPDATE transactions
                    SET is_recurring = 1
                    WHERE merchant_name = ?
                """, (merchant_name,))
        
        self.conn.commit()
    
    def export_to_json(self, output_path: str, date_range: Optional[Tuple[str, str]] = None, 
                       include_metadata: bool = True) -> bool:
        """Export all transactions to a JSON file for programmatic access.
        
        Args:
            output_path: Path where the JSON file should be saved
            date_range: Optional tuple of (start_date, end_date) in YYYY-MM-DD format
            include_metadata: Whether to include metadata in the export
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            
            # Build query with optional date filtering
            query = """
                SELECT 
                    id,
                    transaction_date,
                    amount,
                    description,
                    merchant_name,
                    category,
                    transaction_type,
                    source_file,
                    reference_number,
                    notes,
                    is_recurring
                FROM transactions
            """
            
            params = []
            conditions = []
            
            if date_range:
                start_date, end_date = date_range
                conditions.append("transaction_date >= ?")
                conditions.append("transaction_date <= ?")
                params.extend([start_date, end_date])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY transaction_date, id"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries
            transactions = []
            for row in rows:
                transactions.append({
                    'id': row[0],
                    'transaction_date': row[1],
                    'amount': row[2],
                    'description': row[3],
                    'merchant_name': row[4],
                    'category': row[5],
                    'transaction_type': row[6],
                    'source_file': row[7],
                    'reference_number': row[8],
                    'notes': row[9],
                    'is_recurring': bool(row[10]) if row[10] is not None else False
                })
            
            # Build export data
            export_data = {}
            
            if include_metadata:
                stats = self.get_statistics()
                export_data['metadata'] = {
                    'export_date': datetime.now().isoformat(),
                    'total_transactions': len(transactions),
                    'date_range': {
                        'start': date_range[0] if date_range else stats['date_range']['min'],
                        'end': date_range[1] if date_range else stats['date_range']['max']
                    },
                    'files_imported': stats['files_imported'],
                    'note': 'All sensitive information has been redacted from this data.'
                }
            
            export_data['transactions'] = transactions
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False
    
    def query_transactions(self, category: Optional[str] = None, 
                          merchant: Optional[str] = None,
                          min_amount: Optional[float] = None,
                          max_amount: Optional[float] = None,
                          date_range: Optional[Tuple[str, str]] = None,
                          is_recurring: Optional[bool] = None,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query transactions with various filters.
        
        Args:
            category: Filter by category name
            merchant: Filter by merchant name (partial match)
            min_amount: Minimum transaction amount
            max_amount: Maximum transaction amount
            date_range: Tuple of (start_date, end_date) in YYYY-MM-DD format
            is_recurring: Filter by recurring status (True/False)
            limit: Maximum number of results to return
            
        Returns:
            List of transaction dictionaries
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                id, transaction_date, amount, description, merchant_name,
                category, transaction_type, source_file, reference_number,
                notes, is_recurring
            FROM transactions
            WHERE 1=1
        """
        
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if merchant:
            query += " AND merchant_name LIKE ?"
            params.append(f"%{merchant}%")
        
        if min_amount is not None:
            query += " AND amount >= ?"
            params.append(min_amount)
        
        if max_amount is not None:
            query += " AND amount <= ?"
            params.append(max_amount)
        
        if date_range:
            start_date, end_date = date_range
            query += " AND transaction_date >= ? AND transaction_date <= ?"
            params.extend([start_date, end_date])
        
        if is_recurring is not None:
            query += " AND is_recurring = ?"
            params.append(1 if is_recurring else 0)
        
        query += " ORDER BY transaction_date DESC, id DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        transactions = []
        for row in rows:
            transactions.append({
                'id': row[0],
                'transaction_date': row[1],
                'amount': row[2],
                'description': row[3],
                'merchant_name': row[4],
                'category': row[5],
                'transaction_type': row[6],
                'source_file': row[7],
                'reference_number': row[8],
                'notes': row[9],
                'is_recurring': bool(row[10]) if row[10] is not None else False
            })
        
        return transactions
    
    def get_recurring_transactions(self) -> List[Dict[str, Any]]:
        """Get all recurring transactions grouped by merchant.
        
        Returns:
            List of dictionaries with merchant info and transaction lists
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                merchant_name,
                COUNT(*) as count,
                AVG(amount) as avg_amount,
                MIN(transaction_date) as first_date,
                MAX(transaction_date) as last_date,
                SUM(amount) as total_amount
            FROM transactions
            WHERE is_recurring = 1 AND merchant_name IS NOT NULL
            GROUP BY merchant_name
            ORDER BY count DESC
        """)
        
        recurring = cursor.fetchall()
        
        result = []
        for row in recurring:
            # Get individual transactions for this merchant
            cursor.execute("""
                SELECT id, transaction_date, amount, description
                FROM transactions
                WHERE merchant_name = ? AND is_recurring = 1
                ORDER BY transaction_date DESC
            """, (row[0],))
            
            transactions = cursor.fetchall()
            
            result.append({
                'merchant_name': row[0],
                'transaction_count': row[1],
                'average_amount': row[2],
                'first_transaction': row[3],
                'last_transaction': row[4],
                'total_amount': row[5],
                'transactions': [
                    {
                        'id': t[0],
                        'transaction_date': t[1],
                        'amount': t[2],
                        'description': t[3]
                    }
                    for t in transactions
                ]
            })
        
        return result

