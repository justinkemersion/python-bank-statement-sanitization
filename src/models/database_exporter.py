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
from src.models.paystub_extractor import PaystubExtractor
from src.models.balance_extractor import BalanceExtractor
from src.models.investment_extractor import InvestmentExtractor
from src.models.tax_extractor import TaxDocumentExtractor


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
        self.paystub_extractor = PaystubExtractor()
        self.balance_extractor = BalanceExtractor()
        self.investment_extractor = InvestmentExtractor()
        self.tax_extractor = TaxDocumentExtractor()
    
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
                bank_name TEXT,
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
        
        # Paystubs table - store income/payroll data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paystubs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                pay_date TEXT,
                pay_period_start TEXT,
                pay_period_end TEXT,
                employer_name TEXT,
                gross_pay REAL,
                regular_hours REAL,
                overtime_hours REAL,
                regular_rate REAL,
                overtime_rate REAL,
                bonus REAL,
                commission REAL,
                deductions_json TEXT,
                total_deductions REAL,
                net_pay REAL,
                ytd_gross REAL,
                ytd_net REAL,
                ytd_taxes REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_account_type ON transactions(account_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bank_name ON transactions(bank_name)")
        
        # Add bank_name column if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN bank_name TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_paystub_date ON paystubs(pay_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_paystub_source ON paystubs(source_file)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_paystub_employer ON paystubs(employer_name)")
        
        # Account balances table - track account balances over time
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                statement_date TEXT,
                balance REAL NOT NULL,
                available_credit REAL,
                credit_limit REAL,
                minimum_payment REAL,
                payment_due_date TEXT,
                apr REAL,
                account_type TEXT,
                bank_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_balance_date ON account_balances(statement_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_balance_source ON account_balances(source_file)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_balance_bank ON account_balances(bank_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_balance_type ON account_balances(account_type)")
        
        # Bills table - track recurring bills and payments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant_name TEXT NOT NULL,
                category TEXT,
                amount REAL,
                due_date TEXT,
                frequency TEXT,
                is_active INTEGER DEFAULT 1,
                last_paid_date TEXT,
                next_due_date TEXT,
                payment_count INTEGER DEFAULT 0,
                total_paid REAL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bill_merchant ON bills(merchant_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bill_due_date ON bills(next_due_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bill_active ON bills(is_active)")
        
        # Investment accounts table - track investment account information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investment_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                account_type TEXT NOT NULL,
                bank_name TEXT,
                account_name TEXT,
                statement_date TEXT,
                portfolio_value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Holdings table - track securities positions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investment_account_id INTEGER,
                source_file TEXT NOT NULL,
                statement_date TEXT,
                ticker TEXT,
                security_name TEXT,
                quantity REAL,
                market_value REAL,
                cost_basis REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (investment_account_id) REFERENCES investment_accounts(id)
            )
        """)
        
        # Investment transactions table - track buys, sells, dividends, etc.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investment_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investment_account_id INTEGER,
                source_file TEXT NOT NULL,
                transaction_date TEXT,
                transaction_type TEXT NOT NULL,
                security_ticker TEXT,
                security_name TEXT,
                quantity REAL,
                price REAL,
                amount REAL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (investment_account_id) REFERENCES investment_accounts(id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_investment_account_type ON investment_accounts(account_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_investment_bank ON investment_accounts(bank_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_investment_date ON investment_accounts(statement_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_holding_ticker ON holdings(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_holding_date ON holdings(statement_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_trans_type ON investment_transactions(transaction_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_trans_date ON investment_transactions(transaction_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_trans_ticker ON investment_transactions(security_ticker)")
        
        # Tax documents table - track tax forms (1099-INT, 1099-DIV, 1099-B, W-2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tax_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                document_type TEXT NOT NULL,
                tax_year INTEGER,
                payer_name TEXT,
                employer_name TEXT,
                interest_income REAL,
                ordinary_dividends REAL,
                qualified_dividends REAL,
                total_capital_gain REAL,
                proceeds REAL,
                cost_basis REAL,
                gain_loss REAL,
                wages REAL,
                federal_tax_withheld REAL,
                social_security_wages REAL,
                social_security_tax REAL,
                medicare_wages REAL,
                medicare_tax REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tax_doc_type ON tax_documents(document_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tax_doc_year ON tax_documents(tax_year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tax_doc_source ON tax_documents(source_file)")
        
        # Budgets table - track monthly budgets by category
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                budget_amount REAL NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, month, year)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budget_category ON budgets(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budget_month_year ON budgets(year, month)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budget_active ON budgets(is_active)")
        
        # Financial goals table - track financial goals and progress
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_name TEXT NOT NULL,
                goal_type TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                target_date TEXT,
                start_date TEXT,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goal_type ON financial_goals(goal_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goal_active ON financial_goals(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goal_target_date ON financial_goals(target_date)")
        
        self.conn.commit()
    
    def _detect_bank_name(self, text: str, source_file: str) -> Optional[str]:
        """Detect bank/issuer name from statement text and filename.
        
        Args:
            text: Statement text content
            source_file: Source file name
            
        Returns:
            Bank/issuer name (e.g., 'Discover', 'American Express', 'Charles Schwab') or None
        """
        text_lower = text.lower()
        filename_lower = source_file.lower()
        
        # Known bank/issuer patterns (order matters - more specific first)
        bank_patterns = {
            'American Express': [
                r'american\s+express',
                r'amex',
                r'\bamex\b',
            ],
            'Discover': [
                r'discover\s+(?:card|bank|financial)',
                r'\bdiscover\b',
            ],
            'Charles Schwab': [
                r'charles\s+schwab',
                r'schwab\s+(?:bank|investor)',
                r'\bschwab\b',
            ],
            'Chase': [
                r'chase\s+(?:bank|card|sapphire)',
                r'\bchase\b',
            ],
            'Bank of America': [
                r'bank\s+of\s+america',
                r'\bbofa\b',
                r'\bbankofamerica\b',
            ],
            'Wells Fargo': [
                r'wells\s+fargo',
            ],
            'Citibank': [
                r'citi\s+(?:bank|card)',
                r'\bcitibank\b',
            ],
            'Capital One': [
                r'capital\s+one',
            ],
            'US Bank': [
                r'us\s+bank',
                r'\busbank\b',
            ],
            'PNC': [
                r'\bpnc\s+(?:bank|card)',
            ],
            'TD Bank': [
                r'td\s+bank',
            ],
            'Ally Bank': [
                r'ally\s+bank',
            ],
        }
        
        # Check filename first (often most reliable)
        for bank_name, patterns in bank_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    return bank_name
        
        # Check text content
        for bank_name, patterns in bank_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return bank_name
        
        # Try to extract from common statement headers
        header_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:card|bank|statement|account)',
            r'statement\s+from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in header_patterns:
            match = re.search(pattern, text)
            if match:
                potential_bank = match.group(1).strip()
                # Validate it's a known bank or looks like a bank name
                if len(potential_bank) > 2 and potential_bank not in ['Account', 'Credit', 'Debit']:
                    return potential_bank
        
        return None  # Unknown bank
    
    def _detect_account_type(self, text: str, source_file: str) -> Optional[str]:
        """Detect account type from statement text.
        
        Args:
            text: Statement text content
            source_file: Source file name
            
        Returns:
            Account type string (e.g., 'checking', 'savings', 'credit_card') or None
        """
        text_lower = text.lower()
        filename_lower = source_file.lower()
        
        # Check filename for account type indicators
        if any(keyword in filename_lower for keyword in ['checking', 'check']):
            return 'checking'
        if any(keyword in filename_lower for keyword in ['savings', 'save']):
            return 'savings'
        if any(keyword in filename_lower for keyword in ['credit', 'card', 'amex', 'discover', 'visa', 'mastercard']):
            return 'credit_card'
        if any(keyword in filename_lower for keyword in ['roth', 'ira']):
            # Check if it's Roth specifically
            if 'roth' in filename_lower:
                return 'roth_ira'
            return 'traditional_ira'
        if any(keyword in filename_lower for keyword in ['investment', 'brokerage', 'trading', 'portfolio']):
            return 'investment_account'
        
        # Check text content for account type indicators
        account_patterns = {
            'checking': [
                r'checking\s+account',
                r'checking\s+statement',
                r'demand\s+deposit',
            ],
            'savings': [
                r'savings\s+account',
                r'savings\s+statement',
            ],
            'credit_card': [
                r'credit\s+card',
                r'card\s+statement',
                r'cardmember\s+statement',
                r'account\s+summary',
                r'payment\s+due',
                r'minimum\s+payment',
                r'available\s+credit',
                r'credit\s+limit',
            ],
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
                r'portfolio\s+statement',
            ],
        }
        
        for account_type, patterns in account_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return account_type
        
        # Default: try to infer from transaction patterns
        # Credit cards often have negative amounts as purchases
        # Checking accounts have mixed debits/credits
        # This is a fallback heuristic
        return None  # Unknown - let user specify if needed
    
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
        
        # Detect account type and bank name
        account_type = self._detect_account_type(text, source_file)
        bank_name = self._detect_bank_name(text, source_file)
        
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
                            'account_type': account_type,
                            'bank_name': bank_name,
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
            # Detect bank name from filename (for CSV/Excel files)
            bank_name = self._detect_bank_name("", source_file)  # Pass empty text, use filename only
            
            transaction = {
                'source_file': source_file,
                'transaction_date': None,
                'amount': None,
                'description': None,
                'merchant_name': None,
                'category': None,
                'account_type': None,
                'bank_name': bank_name,
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
            
            # Try to detect account type from CSV data
            account_type_columns = ['account_type', 'account', 'account_name', 'account_description']
            for col in account_type_columns:
                if col in row and row[col]:
                    account_str = str(row[col]).lower()
                    if 'checking' in account_str or 'check' in account_str:
                        transaction['account_type'] = 'checking'
                    elif 'savings' in account_str or 'save' in account_str:
                        transaction['account_type'] = 'savings'
                    elif 'credit' in account_str or 'card' in account_str:
                        transaction['account_type'] = 'credit_card'
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
    
    def _is_duplicate_transaction(self, transaction: Dict[str, Any], cursor: sqlite3.Cursor) -> bool:
        """Check if a transaction already exists in the database.
        
        A transaction is considered a duplicate if it has:
        - Same date
        - Same amount (within 0.01 tolerance for floating point)
        - Same merchant name (if available) OR similar description
        
        Args:
            transaction: Transaction dictionary to check
            cursor: Database cursor
            
        Returns:
            bool: True if duplicate found, False otherwise
        """
        date = transaction.get('transaction_date')
        amount = transaction.get('amount')
        merchant = transaction.get('merchant_name')
        description = transaction.get('description')
        
        if not date or amount is None:
            return False  # Can't match without date/amount
        
        # Build query to find potential duplicates
        query = """
            SELECT COUNT(*) FROM transactions
            WHERE transaction_date = ? 
            AND ABS(amount - ?) < 0.01
        """
        params = [date, amount]
        
        # If we have a merchant name, use it for matching (more reliable)
        if merchant:
            query += " AND merchant_name = ?"
            params.append(merchant)
        # Otherwise, try to match on description (first 50 chars for fuzzy matching)
        elif description:
            query += " AND description LIKE ?"
            params.append(f"{description[:50]}%")
        else:
            # No merchant or description - can't reliably detect duplicate
            return False
        
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        return count > 0
    
    def insert_transactions(self, transactions: List[Dict[str, Any]], skip_duplicates: bool = True) -> Dict[str, int]:
        """Insert transactions into the database.
        
        Args:
            transactions: List of transaction dictionaries
            skip_duplicates: If True, skip duplicate transactions (default: True)
            
        Returns:
            Dictionary with 'inserted' and 'skipped' counts
        """
        if not transactions:
            return {'inserted': 0, 'skipped': 0}
        
        cursor = self.conn.cursor()
        inserted_count = 0
        skipped_count = 0
        
        try:
            for transaction in transactions:
                # Check for duplicates if enabled
                if skip_duplicates and self._is_duplicate_transaction(transaction, cursor):
                    skipped_count += 1
                    continue
                
                cursor.execute("""
                    INSERT INTO transactions 
                    (source_file, transaction_date, amount, description, merchant_name, category, 
                     account_type, bank_name, transaction_type, reference_number, notes, is_recurring)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction.get('source_file'),
                    transaction.get('transaction_date'),
                    transaction.get('amount'),
                    transaction.get('description'),
                    transaction.get('merchant_name'),
                    transaction.get('category'),
                    transaction.get('account_type'),
                    transaction.get('bank_name'),
                    transaction.get('transaction_type'),
                    transaction.get('reference_number'),
                    transaction.get('notes'),
                    transaction.get('is_recurring', 0)
                ))
                inserted_count += 1
            
            self.conn.commit()
            
            # After inserting, detect and mark recurring transactions
            if inserted_count > 0:
                try:
                    self._detect_recurring_transactions()
                    # Update bills table from recurring transactions
                    self.update_bills_from_recurring_transactions()
                except Exception as e:
                    # Log but don't fail - recurring detection is not critical
                    print(f"Warning: Failed to detect recurring transactions: {e}")
            
            return {'inserted': inserted_count, 'skipped': skipped_count}
        except Exception as e:
            self.conn.rollback()
            print(f"Error inserting transactions: {e}")
            return {'inserted': 0, 'skipped': skipped_count}
    
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
        
        # Paystub statistics
        paystub_stats = self.get_paystub_statistics()
        stats['paystubs'] = paystub_stats
        
        # Account type statistics
        account_stats = self.get_account_statistics()
        stats['accounts'] = account_stats
        
        # Bank/issuer statistics
        bank_stats = self.get_bank_statistics()
        stats['banks'] = bank_stats
        
        # Investment account statistics
        investment_stats = self.get_investment_statistics()
        stats['investments'] = investment_stats
        
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
                    account_type,
                    bank_name,
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
#   - account_type: Type of account ('checking', 'savings', 'credit_card', etc.)
#   - bank_name: Bank/issuer name (e.g., 'Discover', 'American Express', 'Charles Schwab')
#   - transaction_type: 'debit' or 'credit'
#   - source_file: Original statement file name
#   - reference_number: Transaction reference number (if available)
#   - notes: Additional notes
#   - is_recurring: Whether this is a recurring transaction (Yes/No)
#
# NOTE: All sensitive information (account numbers, SSN, etc.) has been redacted.
# The [REDACTED] placeholders indicate where sensitive data was removed.
#
"""
                    f.write(metadata)
                    f.write("\n")
                
                # Write CSV data
                fieldnames = ['transaction_date', 'amount', 'description', 'merchant_name',
                            'category', 'account_type', 'bank_name', 'transaction_type', 
                            'source_file', 'reference_number', 'notes', 'is_recurring']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in rows:
                    writer.writerow({
                        'transaction_date': row[0] or '',
                        'amount': row[1] if row[1] is not None else '',
                        'description': row[2] or '',
                        'merchant_name': row[3] or '',
                        'category': row[4] or '',
                        'account_type': row[5] or '',
                        'bank_name': row[6] or '',
                        'transaction_type': row[7] or '',
                        'source_file': row[8] or '',
                        'reference_number': row[9] or '',
                        'notes': row[10] or '',
                        'is_recurring': 'Yes' if row[11] else 'No'
                    })
            
            # Also export investment data if available
            cursor.execute("""
                SELECT 
                    ia.account_type, ia.bank_name, ia.statement_date, ia.portfolio_value,
                    h.ticker, h.security_name, h.quantity, h.market_value
                FROM investment_accounts ia
                LEFT JOIN holdings h ON h.investment_account_id = ia.id
                WHERE (ia.account_type, ia.bank_name, ia.statement_date) IN (
                    SELECT account_type, bank_name, MAX(statement_date)
                    FROM investment_accounts
                    GROUP BY account_type, bank_name
                )
                ORDER BY ia.account_type, ia.bank_name, h.market_value DESC
            """)
            
            investment_rows = cursor.fetchall()
            if investment_rows:
                # Append investment data to CSV
                f.write("\n\n# INVESTMENT ACCOUNT DATA\n")
                f.write("# This section contains investment account information.\n")
                f.write("# Columns: account_type, bank_name, statement_date, portfolio_value, ticker, security_name, quantity, market_value\n\n")
                
                investment_writer = csv.writer(f)
                investment_writer.writerow(['account_type', 'bank_name', 'statement_date', 'portfolio_value', 
                                           'ticker', 'security_name', 'quantity', 'market_value'])
                
                for row in investment_rows:
                    investment_writer.writerow([
                        row[0] or '',  # account_type
                        row[1] or '',   # bank_name
                        row[2] or '',   # statement_date
                        row[3] if row[3] is not None else '',  # portfolio_value
                        row[4] or '',  # ticker
                        row[5] or '',  # security_name
                        row[6] if row[6] is not None else '',  # quantity
                        row[7] if row[7] is not None else '',  # market_value
                    ])
            
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
    
    def _detect_recurring_income(self):
        """Detect and track recurring income sources.
        
        Income is considered recurring if:
        - Positive amount (credit)
        - Same merchant/description appears multiple times
        - Similar amount (within 10% variance for income)
        - Regular intervals (monthly, bi-weekly, etc.)
        """
        cursor = self.conn.cursor()
        
        # Find positive transactions (income) with same merchant/description
        cursor.execute("""
            SELECT 
                COALESCE(merchant_name, description) as income_source,
                COUNT(*) as count,
                AVG(amount) as avg_amount,
                MIN(transaction_date) as first_date,
                MAX(transaction_date) as last_date,
                SUM(amount) as total_amount
            FROM transactions
            WHERE amount > 0
            AND (merchant_name IS NOT NULL OR description IS NOT NULL)
            GROUP BY income_source
            HAVING count >= 2
        """)
        
        income_sources = cursor.fetchall()
        
        recurring_income = []
        for row in income_sources:
            income_source = row[0]
            count = row[1]
            avg_amount = row[2]
            first_date = row[3]
            last_date = row[4]
            total_amount = row[5]
            
            # Check if amounts are similar (within 10% variance)
            cursor.execute("""
                SELECT amount
                FROM transactions
                WHERE amount > 0
                AND (COALESCE(merchant_name, description) = ?)
                ORDER BY transaction_date
            """, (income_source,))
            
            amounts = [r[0] for r in cursor.fetchall()]
            if len(amounts) >= 2:
                # Check variance
                variance = max(amounts) / min(amounts) if min(amounts) > 0 else 0
                if variance <= 1.10:  # Within 10% variance
                    recurring_income.append({
                        'income_source': income_source,
                        'count': count,
                        'avg_amount': avg_amount,
                        'total_amount': total_amount,
                        'first_date': first_date,
                        'last_date': last_date,
                        'frequency': 'monthly' if count >= 3 else 'irregular',
                    })
        
        return recurring_income
    
    def get_recurring_income(self) -> List[Dict[str, Any]]:
        """Get all recurring income sources.
        
        Returns:
            List of recurring income dictionaries
        """
        return self._detect_recurring_income()
    
    def get_income_summary(self, year: Optional[int] = None) -> Dict[str, Any]:
        """Get income summary statistics.
        
        Args:
            year: Optional year to filter by
            
        Returns:
            Dictionary with income statistics
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                SUM(amount) as total_income,
                COUNT(*) as transaction_count,
                AVG(amount) as avg_income,
                MIN(transaction_date) as first_income,
                MAX(transaction_date) as last_income
            FROM transactions
            WHERE amount > 0
        """
        
        params = []
        if year:
            query += " AND strftime('%Y', transaction_date) = ?"
            params.append(str(year))
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        # Get income from paystubs
        paystub_query = """
            SELECT 
                SUM(gross_pay) as total_paystub_income,
                COUNT(*) as paystub_count
            FROM paystubs
            WHERE 1=1
        """
        
        paystub_params = []
        if year:
            paystub_query += " AND strftime('%Y', pay_date) = ?"
            paystub_params.append(str(year))
        
        cursor.execute(paystub_query, paystub_params)
        paystub_row = cursor.fetchone()
        
        # Get recurring income
        recurring_income = self._detect_recurring_income()
        
        return {
            'total_income': row[0] or 0,
            'transaction_count': row[1] or 0,
            'avg_income': row[2] or 0,
            'first_income': row[3],
            'last_income': row[4],
            'paystub_income': paystub_row[0] or 0,
            'paystub_count': paystub_row[1] or 0,
            'recurring_income': recurring_income,
            'recurring_income_total': sum(r['total_amount'] for r in recurring_income),
        }
    
    def update_bills_from_recurring_transactions(self):
        """Update bills table from recurring transactions.
        
        Identifies recurring transactions and creates/updates bill records.
        """
        cursor = self.conn.cursor()
        
        # Get recurring transactions grouped by merchant
        cursor.execute("""
            SELECT 
                merchant_name,
                category,
                AVG(amount) as avg_amount,
                COUNT(*) as count,
                MIN(transaction_date) as first_date,
                MAX(transaction_date) as last_date
            FROM transactions
            WHERE is_recurring = 1 AND merchant_name IS NOT NULL
            GROUP BY merchant_name
            HAVING count >= 2
        """)
        
        recurring = cursor.fetchall()
        
        for row in recurring:
            merchant_name = row[0]
            category = row[1]
            avg_amount = abs(row[2]) if row[2] else 0
            count = row[3]
            first_date = row[4]
            last_date = row[5]
            
            # Check if bill already exists
            cursor.execute("SELECT id FROM bills WHERE merchant_name = ?", (merchant_name,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing bill
                cursor.execute("""
                    UPDATE bills
                    SET amount = ?,
                        category = ?,
                        payment_count = ?,
                        last_paid_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE merchant_name = ?
                """, (avg_amount, category, count, last_date, merchant_name))
            else:
                # Create new bill
                cursor.execute("""
                    INSERT INTO bills (merchant_name, category, amount, frequency, 
                                     last_paid_date, payment_count, total_paid)
                    VALUES (?, ?, ?, 'monthly', ?, ?, ?)
                """, (merchant_name, category, avg_amount, last_date, count, avg_amount * count))
        
        self.conn.commit()
    
    def get_upcoming_bills(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get bills due in the next N days.
        
        Args:
            days_ahead: Number of days to look ahead (default: 30)
        
        Returns:
            List of upcoming bills
        """
        from datetime import datetime, timedelta
        
        cursor = self.conn.cursor()
        cutoff_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        # Get bills with due dates in the next N days
        cursor.execute("""
            SELECT 
                id, merchant_name, category, amount, due_date, next_due_date,
                frequency, last_paid_date, payment_count
            FROM bills
            WHERE is_active = 1
            AND (next_due_date IS NOT NULL AND next_due_date <= ?)
            ORDER BY next_due_date ASC
        """, (cutoff_date,))
        
        rows = cursor.fetchall()
        
        bills = []
        for row in rows:
            bills.append({
                'id': row[0],
                'merchant_name': row[1],
                'category': row[2],
                'amount': row[3],
                'due_date': row[4],
                'next_due_date': row[5],
                'frequency': row[6],
                'last_paid_date': row[7],
                'payment_count': row[8],
            })
        
        return bills
    
    def get_all_bills(self) -> List[Dict[str, Any]]:
        """Get all active bills.
        
        Returns:
            List of all bills
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, merchant_name, category, amount, due_date, next_due_date,
                frequency, last_paid_date, payment_count, total_paid, notes
            FROM bills
            WHERE is_active = 1
            ORDER BY merchant_name
        """)
        
        rows = cursor.fetchall()
        
        bills = []
        for row in rows:
            bills.append({
                'id': row[0],
                'merchant_name': row[1],
                'category': row[2],
                'amount': row[3],
                'due_date': row[4],
                'next_due_date': row[5],
                'frequency': row[6],
                'last_paid_date': row[7],
                'payment_count': row[8],
                'total_paid': row[9],
                'notes': row[10],
            })
        
        return bills
    
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
                    account_type,
                    bank_name,
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
                    'account_type': row[6],
                    'bank_name': row[7],
                    'transaction_type': row[8],
                    'source_file': row[9],
                    'reference_number': row[10],
                    'notes': row[11],
                    'is_recurring': bool(row[12]) if row[12] is not None else False
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
    
    def get_account_statistics(self) -> Dict[str, Any]:
        """Get statistics by account type.
        
        Returns:
            Dictionary with account type breakdown
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                COALESCE(account_type, 'Unknown') as account_type,
                COUNT(*) as count,
                SUM(amount) as total,
                AVG(amount) as average,
                MIN(transaction_date) as first_transaction,
                MAX(transaction_date) as last_transaction
            FROM transactions
            WHERE amount IS NOT NULL
            GROUP BY account_type
            ORDER BY count DESC
        """)
        
        rows = cursor.fetchall()
        accounts = []
        for row in rows:
            accounts.append({
                'account_type': row[0],
                'transaction_count': row[1],
                'total_amount': row[2] or 0,
                'average_amount': row[3] or 0,
                'first_transaction': row[4],
                'last_transaction': row[5]
            })
        
        return {
            'accounts': accounts,
            'total_accounts': len(accounts)
        }
    
    def get_bank_statistics(self) -> Dict[str, Any]:
        """Get statistics by bank/issuer name.
        
        Returns:
            Dictionary with bank breakdown
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                COALESCE(bank_name, 'Unknown') as bank_name,
                COALESCE(account_type, 'Unknown') as account_type,
                COUNT(*) as count,
                SUM(amount) as total,
                AVG(amount) as average,
                MIN(transaction_date) as first_transaction,
                MAX(transaction_date) as last_transaction
            FROM transactions
            WHERE amount IS NOT NULL
            GROUP BY bank_name, account_type
            ORDER BY count DESC
        """)
        
        rows = cursor.fetchall()
        banks = []
        for row in rows:
            banks.append({
                'bank_name': row[0],
                'account_type': row[1],
                'transaction_count': row[2],
                'total_amount': row[3] or 0,
                'average_amount': row[4] or 0,
                'first_transaction': row[5],
                'last_transaction': row[6]
            })
        
        return {
            'banks': banks,
            'total_banks': len(set(b[0] for b in banks))
        }
    
    def extract_balance_from_text(self, text: str, source_file: str, account_type: Optional[str] = None,
                                  bank_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Extract balance information from statement text.
        
        Args:
            text: Statement text content
            source_file: Source file name
            account_type: Account type (checking, savings, credit_card)
            bank_name: Bank/issuer name
            
        Returns:
            Dictionary with balance data, or None if not found
        """
        return self.balance_extractor.extract_balance(text, source_file, account_type, bank_name)
    
    def insert_balance(self, balance: Dict[str, Any], skip_duplicates: bool = True) -> bool:
        """Insert account balance into the database.
        
        Args:
            balance: Dictionary with balance data
            skip_duplicates: If True, skip if balance already exists (same statement_date + source_file)
            
        Returns:
            True if inserted, False if skipped or failed
        """
        if not balance:
            return False
        
        cursor = self.conn.cursor()
        
        # Check for duplicates if enabled
        if skip_duplicates:
            statement_date = balance.get('statement_date')
            source_file = balance.get('source_file')
            if statement_date and source_file:
                cursor.execute("""
                    SELECT COUNT(*) FROM account_balances
                    WHERE statement_date = ? AND source_file = ?
                """, (statement_date, source_file))
                count = cursor.fetchone()[0]
                if count > 0:
                    return False  # Duplicate found
        
        # Insert balance
        try:
            cursor.execute("""
                INSERT INTO account_balances 
                (source_file, statement_date, balance, available_credit, credit_limit,
                 minimum_payment, payment_due_date, apr, account_type, bank_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                balance.get('source_file'),
                balance.get('statement_date'),
                balance.get('balance'),
                balance.get('available_credit'),
                balance.get('credit_limit'),
                balance.get('minimum_payment'),
                balance.get('payment_due_date'),
                balance.get('apr'),
                balance.get('account_type'),
                balance.get('bank_name'),
            ))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error inserting balance: {e}")
            return False
    
    def get_balance_history(self, bank_name: Optional[str] = None, account_type: Optional[str] = None,
                           limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get balance history for accounts.
        
        Args:
            bank_name: Filter by bank name
            account_type: Filter by account type
            limit: Maximum number of records to return
            
        Returns:
            List of balance records
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                id, source_file, statement_date, balance, available_credit, credit_limit,
                minimum_payment, payment_due_date, apr, account_type, bank_name
            FROM account_balances
            WHERE 1=1
        """
        
        params = []
        if bank_name:
            query += " AND bank_name = ?"
            params.append(bank_name)
        
        if account_type:
            query += " AND account_type = ?"
            params.append(account_type)
        
        query += " ORDER BY statement_date DESC, id DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        balances = []
        for row in rows:
            balances.append({
                'id': row[0],
                'source_file': row[1],
                'statement_date': row[2],
                'balance': row[3],
                'available_credit': row[4],
                'credit_limit': row[5],
                'minimum_payment': row[6],
                'payment_due_date': row[7],
                'apr': row[8],
                'account_type': row[9],
                'bank_name': row[10],
            })
        
        return balances
    
    def get_current_debts(self) -> List[Dict[str, Any]]:
        """Get current debt balances (most recent balance per bank/account).
        
        Returns:
            List of current debt information
        """
        cursor = self.conn.cursor()
        
        # Get most recent balance for each bank/account combination
        cursor.execute("""
            SELECT 
                bank_name, account_type, balance, credit_limit, available_credit,
                minimum_payment, payment_due_date, apr, statement_date
            FROM account_balances
            WHERE account_type = 'credit_card' AND balance IS NOT NULL
            AND (bank_name, account_type, statement_date) IN (
                SELECT bank_name, account_type, MAX(statement_date)
                FROM account_balances
                WHERE account_type = 'credit_card'
                GROUP BY bank_name, account_type
            )
            ORDER BY balance DESC
        """)
        
        rows = cursor.fetchall()
        
        debts = []
        for row in rows:
            debts.append({
                'bank_name': row[0],
                'account_type': row[1],
                'balance': row[2],
                'credit_limit': row[3],
                'available_credit': row[4],
                'minimum_payment': row[5],
                'payment_due_date': row[6],
                'apr': row[7],
                'statement_date': row[8],
            })
        
        return debts
    
    def calculate_debt_payoff(self, monthly_payment: float, strategy: str = 'avalanche') -> Dict[str, Any]:
        """Calculate debt payoff strategy.
        
        Args:
            monthly_payment: Total monthly payment available for debt
            strategy: 'snowball' or 'avalanche' (default: 'avalanche')
        
        Returns:
            Dictionary with payoff strategy details
        """
        from src.models.debt_calculator import DebtCalculator
        
        debts = self.get_current_debts()
        if not debts:
            return {
                'error': 'No debt found in database',
                'debts': []
            }
        
        calculator = DebtCalculator()
        
        if strategy.lower() == 'snowball':
            result = calculator.calculate_snowball_strategy(debts, monthly_payment)
        elif strategy.lower() == 'avalanche':
            result = calculator.calculate_avalanche_strategy(debts, monthly_payment)
        else:
            # Compare both
            result = calculator.compare_strategies(debts, monthly_payment)
        
        return result
    
    def query_transactions(self, category: Optional[str] = None, 
                          merchant: Optional[str] = None,
                          account_type: Optional[str] = None,
                          bank_name: Optional[str] = None,
                          min_amount: Optional[float] = None,
                          max_amount: Optional[float] = None,
                          date_range: Optional[Tuple[str, str]] = None,
                          is_recurring: Optional[bool] = None,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query transactions with various filters.
        
        Args:
            category: Filter by category name
            merchant: Filter by merchant name (partial match)
            account_type: Filter by account type (e.g., 'checking', 'savings', 'credit_card')
            bank_name: Filter by bank/issuer name (e.g., 'Discover', 'American Express')
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
                category, account_type, bank_name, transaction_type, source_file, 
                reference_number, notes, is_recurring
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
        
        if account_type:
            query += " AND account_type = ?"
            params.append(account_type)
        
        if bank_name:
            query += " AND bank_name = ?"
            params.append(bank_name)
        
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
                'account_type': row[6],
                'bank_name': row[7],
                'transaction_type': row[8],
                'source_file': row[9],
                'reference_number': row[10],
                'notes': row[11],
                'is_recurring': bool(row[12]) if row[12] is not None else False
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
    
    def extract_tax_document_from_text(self, text: str, source_file: str) -> Optional[Dict[str, Any]]:
        """Extract tax document data from sanitized text.
        
        Args:
            text: Sanitized text content
            source_file: Source file name
            
        Returns:
            Dictionary with tax document data, or None if not a tax document
        """
        return self.tax_extractor.extract(text, source_file)
    
    def insert_tax_document(self, tax_doc: Dict[str, Any], skip_duplicates: bool = True) -> Optional[int]:
        """Insert a tax document into the database.
        
        Args:
            tax_doc: Dictionary with tax document data
            skip_duplicates: If True, skip if document already exists (same document_type, tax_year, source_file)
            
        Returns:
            Document ID if inserted, None if skipped or failed
        """
        if not tax_doc:
            return None
        
        cursor = self.conn.cursor()
        
        # Check for duplicates if enabled
        if skip_duplicates:
            doc_type = tax_doc.get('document_type')
            tax_year = tax_doc.get('tax_year')
            source_file = tax_doc.get('source_file')
            if doc_type and tax_year and source_file:
                cursor.execute("""
                    SELECT id FROM tax_documents
                    WHERE document_type = ? AND tax_year = ? AND source_file = ?
                """, (doc_type, tax_year, source_file))
                existing = cursor.fetchone()
                if existing:
                    return None  # Duplicate found
        
        # Insert tax document
        try:
            cursor.execute("""
                INSERT INTO tax_documents 
                (source_file, document_type, tax_year, payer_name, interest_income, 
                 ordinary_dividends, qualified_dividends, total_capital_gain, capital_gain_distributions,
                 federal_tax_withheld, state_tax_withheld, wages, state_wages, 
                 local_wages, social_security_wages, medicare_wages, data_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tax_doc.get('source_file'),
                tax_doc.get('document_type'),
                tax_doc.get('tax_year'),
                tax_doc.get('payer_name'),
                tax_doc.get('interest_income'),
                tax_doc.get('ordinary_dividends'),
                tax_doc.get('qualified_dividends'),
                tax_doc.get('total_capital_gain'),
                tax_doc.get('capital_gain_distributions'),
                tax_doc.get('federal_tax_withheld'),
                tax_doc.get('state_tax_withheld'),
                tax_doc.get('wages'),
                tax_doc.get('state_wages'),
                tax_doc.get('local_wages'),
                tax_doc.get('social_security_wages'),
                tax_doc.get('medicare_wages'),
                json.dumps(tax_doc) if tax_doc else None,
            ))
            
            doc_id = cursor.lastrowid
            self.conn.commit()
            return doc_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error inserting tax document: {e}")
            return None
    
    def extract_paystub_from_text(self, text: str, source_file: str) -> List[Dict[str, Any]]:
        """Extract paystub data from sanitized text (handles multiple paystubs).
        
        Args:
            text: Sanitized text content
            source_file: Source file name
            
        Returns:
            List of paystub dictionaries (empty if not a paystub)
        """
        # Check if this is a paystub
        if not self.paystub_extractor.is_paystub(text):
            return []
        
        # Extract all paystubs (handles multiple paystubs in one document)
        return self.paystub_extractor.extract_all(text, source_file)
    
    def insert_paystub(self, paystub: Dict[str, Any], skip_duplicates: bool = True) -> bool:
        """Insert a paystub into the database.
        
        Args:
            paystub: Dictionary with paystub data
            skip_duplicates: If True, skip if paystub already exists (same pay_date and source_file)
            
        Returns:
            True if inserted, False if skipped or failed
        """
        if not paystub:
            return False
        
        cursor = self.conn.cursor()
        
        # Check for duplicates if enabled
        if skip_duplicates:
            pay_date = paystub.get('pay_date')
            source_file = paystub.get('source_file')
            if pay_date and source_file:
                cursor.execute("""
                    SELECT COUNT(*) FROM paystubs
                    WHERE pay_date = ? AND source_file = ?
                """, (pay_date, source_file))
                count = cursor.fetchone()[0]
                if count > 0:
                    return False  # Duplicate found
        
        # Insert paystub
        try:
            cursor.execute("""
                INSERT INTO paystubs 
                (source_file, pay_date, pay_period_start, pay_period_end, employer_name,
                 gross_pay, regular_hours, overtime_hours, regular_rate, overtime_rate,
                 bonus, commission, deductions_json, total_deductions, net_pay,
                 ytd_gross, ytd_net, ytd_taxes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paystub.get('source_file'),
                paystub.get('pay_date'),
                paystub.get('pay_period_start'),
                paystub.get('pay_period_end'),
                paystub.get('employer_name'),
                paystub.get('gross_pay'),
                paystub.get('regular_hours'),
                paystub.get('overtime_hours'),
                paystub.get('regular_rate'),
                paystub.get('overtime_rate'),
                paystub.get('bonus'),
                paystub.get('commission'),
                paystub.get('deductions_json'),
                paystub.get('total_deductions'),
                paystub.get('net_pay'),
                paystub.get('ytd_gross'),
                paystub.get('ytd_net'),
                paystub.get('ytd_taxes'),
            ))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error inserting paystub: {e}")
            return False
    
    def get_paystub_statistics(self) -> Dict[str, Any]:
        """Get statistics about paystubs in the database.
        
        Returns:
            Dictionary with paystub statistics
        """
        cursor = self.conn.cursor()
        
        # Total paystubs
        cursor.execute("SELECT COUNT(*) FROM paystubs")
        total_count = cursor.fetchone()[0]
        
        if total_count == 0:
            return {
                'total_paystubs': 0,
                'total_gross': 0,
                'total_net': 0,
                'average_gross': 0,
                'average_net': 0,
                'total_taxes': 0,
                'employers': []
            }
        
        # Sum totals
        cursor.execute("""
            SELECT 
                SUM(gross_pay) as total_gross,
                SUM(net_pay) as total_net,
                SUM(total_deductions) as total_deductions,
                AVG(gross_pay) as avg_gross,
                AVG(net_pay) as avg_net
            FROM paystubs
            WHERE gross_pay IS NOT NULL
        """)
        row = cursor.fetchone()
        total_gross = row[0] or 0
        total_net = row[1] or 0
        total_deductions = row[2] or 0
        avg_gross = row[3] or 0
        avg_net = row[4] or 0
        
        # Get date range
        cursor.execute("""
            SELECT MIN(pay_date) as first_pay, MAX(pay_date) as last_pay
            FROM paystubs
            WHERE pay_date IS NOT NULL
        """)
        date_row = cursor.fetchone()
        first_pay = date_row[0] if date_row else None
        last_pay = date_row[1] if date_row else None
        
        # Get unique employers
        cursor.execute("""
            SELECT DISTINCT employer_name, COUNT(*) as count
            FROM paystubs
            WHERE employer_name IS NOT NULL
            GROUP BY employer_name
        """)
        employers = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        return {
            'total_paystubs': total_count,
            'total_gross': total_gross,
            'total_net': total_net,
            'total_deductions': total_deductions,
            'average_gross': avg_gross,
            'average_net': avg_net,
            'first_pay_date': first_pay,
            'last_pay_date': last_pay,
            'employers': employers
        }
    
    def set_budget(self, category: str, month: str, year: int, amount: float) -> bool:
        """Set or update a monthly budget for a category.
        
        Args:
            category: Category name (e.g., 'Groceries', 'Restaurants')
            month: Month string (e.g., '01', '02', 'January')
            year: Year (e.g., 2024)
            amount: Budget amount
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Normalize month to MM format
            month_map = {
                'january': '01', 'jan': '01', '1': '01',
                'february': '02', 'feb': '02', '2': '02',
                'march': '03', 'mar': '03', '3': '03',
                'april': '04', 'apr': '04', '4': '04',
                'may': '05', '5': '05',
                'june': '06', 'jun': '06', '6': '06',
                'july': '07', 'jul': '07', '7': '07',
                'august': '08', 'aug': '08', '8': '08',
                'september': '09', 'sep': '09', 'sept': '09', '9': '09',
                'october': '10', 'oct': '10', '10': '10',
                'november': '11', 'nov': '11', '11': '11',
                'december': '12', 'dec': '12', '12': '12',
            }
            
            month_lower = str(month).lower()
            if month_lower in month_map:
                month = month_map[month_lower]
            elif len(str(month)) == 1:
                month = f"0{month}"
            elif len(str(month)) == 2 and month.isdigit():
                month = str(month)
            else:
                return False  # Invalid month format
            
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO budgets (category, month, year, budget_amount, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (category, month, year, amount))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error setting budget: {e}")
            return False
    
    def get_budget(self, category: str, month: str, year: int) -> Optional[float]:
        """Get budget amount for a category and month.
        
        Args:
            category: Category name
            month: Month string (e.g., '01', 'January')
            year: Year
            
        Returns:
            Budget amount or None if not set
        """
        # Normalize month
        month_map = {
            'january': '01', 'jan': '01', '1': '01',
            'february': '02', 'feb': '02', '2': '02',
            'march': '03', 'mar': '03', '3': '03',
            'april': '04', 'apr': '04', '4': '04',
            'may': '05', '5': '05',
            'june': '06', 'jun': '06', '6': '06',
            'july': '07', 'jul': '07', '7': '07',
            'august': '08', 'aug': '08', '8': '08',
            'september': '09', 'sep': '09', 'sept': '09', '9': '09',
            'october': '10', 'oct': '10', '10': '10',
            'november': '11', 'nov': '11', '11': '11',
            'december': '12', 'dec': '12', '12': '12',
        }
        
        month_lower = str(month).lower()
        if month_lower in month_map:
            month = month_map[month_lower]
        elif len(str(month)) == 1:
            month = f"0{month}"
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT budget_amount FROM budgets
            WHERE category = ? AND month = ? AND year = ? AND is_active = 1
        """, (category, month, year))
        
        row = cursor.fetchone()
        return row[0] if row else None
    
    def get_budget_status(self, month: Optional[str] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get budget status (budget vs actual spending) for a month.
        
        Args:
            month: Month string (default: current month)
            year: Year (default: current year)
            
        Returns:
            List of budget status dictionaries
        """
        from datetime import datetime
        
        if not month or not year:
            now = datetime.now()
            month = month or f"{now.month:02d}"
            year = year or now.year
        
        # Normalize month
        month_map = {
            'january': '01', 'jan': '01', '1': '01',
            'february': '02', 'feb': '02', '2': '02',
            'march': '03', 'mar': '03', '3': '03',
            'april': '04', 'apr': '04', '4': '04',
            'may': '05', '5': '05',
            'june': '06', 'jun': '06', '6': '06',
            'july': '07', 'jul': '07', '7': '07',
            'august': '08', 'aug': '08', '8': '08',
            'september': '09', 'sep': '09', 'sept': '09', '9': '09',
            'october': '10', 'oct': '10', '10': '10',
            'november': '11', 'nov': '11', '11': '11',
            'december': '12', 'dec': '12', '12': '12',
        }
        
        month_lower = str(month).lower()
        if month_lower in month_map:
            month = month_map[month_lower]
        elif len(str(month)) == 1:
            month = f"0{month}"
        
        cursor = self.conn.cursor()
        
        # Get all active budgets for the month
        cursor.execute("""
            SELECT category, budget_amount
            FROM budgets
            WHERE month = ? AND year = ? AND is_active = 1
        """, (month, year))
        
        budgets = cursor.fetchall()
        
        # Get actual spending for each category
        month_start = f"{year}-{month}-01"
        # Calculate last day of month
        if month == '12':
            month_end = f"{year}-12-31"
        else:
            next_month = int(month) + 1
            month_end = f"{year}-{next_month:02d}-01"
        
        status_list = []
        for category, budget_amount in budgets:
            # Get actual spending for this category in this month
            cursor.execute("""
                SELECT COALESCE(SUM(ABS(amount)), 0)
                FROM transactions
                WHERE category = ?
                AND transaction_date >= ?
                AND transaction_date < ?
                AND amount < 0
            """, (category, month_start, month_end))
            
            actual_spending = cursor.fetchone()[0] or 0
            remaining = budget_amount - actual_spending
            percentage = (actual_spending / budget_amount * 100) if budget_amount > 0 else 0
            
            status_list.append({
                'category': category,
                'budget': budget_amount,
                'spent': actual_spending,
                'remaining': remaining,
                'percentage': percentage,
                'status': 'over' if actual_spending > budget_amount else 'under',
            })
        
        return status_list
    
    def get_all_budgets(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all active budgets.
        
        Args:
            year: Optional year filter (default: all years)
            
        Returns:
            List of budget dictionaries
        """
        cursor = self.conn.cursor()
        
        if year:
            cursor.execute("""
                SELECT category, month, year, budget_amount
                FROM budgets
                WHERE year = ? AND is_active = 1
                ORDER BY year, month, category
            """, (year,))
        else:
            cursor.execute("""
                SELECT category, month, year, budget_amount
                FROM budgets
                WHERE is_active = 1
                ORDER BY year, month, category
            """)
        
        rows = cursor.fetchall()
        
        budgets = []
        for row in rows:
            budgets.append({
                'category': row[0],
                'month': row[1],
                'year': row[2],
                'budget_amount': row[3],
            })
        
        return budgets
    
    def set_financial_goal(self, goal_name: str, goal_type: str, target_amount: float, 
                          target_date: Optional[str] = None, description: Optional[str] = None) -> Optional[int]:
        """Set or create a financial goal.
        
        Args:
            goal_name: Name of the goal (e.g., 'Emergency Fund', 'Pay off Discover')
            goal_type: Type of goal ('debt_payoff', 'savings', 'investment', 'other')
            target_amount: Target amount to reach
            target_date: Target date (YYYY-MM-DD format, optional)
            description: Optional description
            
        Returns:
            Goal ID if successful, None otherwise
        """
        try:
            cursor = self.conn.cursor()
            from datetime import datetime
            
            start_date = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute("""
                INSERT INTO financial_goals 
                (goal_name, goal_type, target_amount, current_amount, target_date, start_date, description)
                VALUES (?, ?, ?, 0, ?, ?, ?)
            """, (goal_name, goal_type, target_amount, target_date, start_date, description))
            
            goal_id = cursor.lastrowid
            self.conn.commit()
            return goal_id
        except Exception as e:
            print(f"Error setting financial goal: {e}")
            return None
    
    def update_goal_progress(self, goal_id: int, current_amount: float) -> bool:
        """Update progress toward a financial goal.
        
        Args:
            goal_id: Goal ID
            current_amount: Current progress amount
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE financial_goals
                SET current_amount = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (current_amount, goal_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating goal progress: {e}")
            return False
    
    def get_all_goals(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all financial goals.
        
        Args:
            active_only: If True, only return active goals
            
        Returns:
            List of goal dictionaries with progress information
        """
        cursor = self.conn.cursor()
        
        if active_only:
            cursor.execute("""
                SELECT id, goal_name, goal_type, target_amount, current_amount,
                       target_date, start_date, description
                FROM financial_goals
                WHERE is_active = 1
                ORDER BY target_date, goal_name
            """)
        else:
            cursor.execute("""
                SELECT id, goal_name, goal_type, target_amount, current_amount,
                       target_date, start_date, description
                FROM financial_goals
                ORDER BY target_date, goal_name
            """)
        
        rows = cursor.fetchall()
        
        goals = []
        for row in rows:
            goal_id = row[0]
            goal_name = row[1]
            goal_type = row[2]
            target_amount = row[3]
            current_amount = row[4] or 0
            target_date = row[5]
            start_date = row[6]
            description = row[7]
            
            # Calculate progress
            progress_percentage = (current_amount / target_amount * 100) if target_amount > 0 else 0
            remaining = target_amount - current_amount
            
            goals.append({
                'id': goal_id,
                'goal_name': goal_name,
                'goal_type': goal_type,
                'target_amount': target_amount,
                'current_amount': current_amount,
                'remaining': remaining,
                'progress_percentage': progress_percentage,
                'target_date': target_date,
                'start_date': start_date,
                'description': description,
            })
        
        return goals
    
    def calculate_cash_flow_forecast(self, months_ahead: int = 6) -> List[Dict[str, Any]]:
        """Calculate cash flow forecast based on historical patterns.
        
        Args:
            months_ahead: Number of months to forecast (default: 6)
            
        Returns:
            List of monthly cash flow forecasts
        """
        from datetime import datetime, timedelta
        from collections import defaultdict
        import calendar
        
        cursor = self.conn.cursor()
        
        # Get historical income and expenses by month
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expenses
            FROM transactions
            WHERE transaction_date IS NOT NULL
            AND transaction_date >= date('now', '-12 months')
            GROUP BY month
            ORDER BY month
        """)
        
        historical = cursor.fetchall()
        
        if not historical:
            return []
        
        # Calculate averages
        monthly_income = defaultdict(list)
        monthly_expenses = defaultdict(list)
        
        for row in historical:
            month = row[0]
            income = row[1] or 0
            expenses = row[2] or 0
            
            # Extract month number (01-12)
            month_num = int(month.split('-')[1])
            monthly_income[month_num].append(income)
            monthly_expenses[month_num].append(expenses)
        
        # Calculate averages per month
        avg_income_by_month = {}
        avg_expenses_by_month = {}
        
        # Overall averages as fallback
        all_income = [sum(monthly_income[m]) for m in monthly_income if monthly_income[m]]
        all_expenses = [sum(monthly_expenses[m]) for m in monthly_expenses if monthly_expenses[m]]
        overall_avg_income = sum(all_income) / len(all_income) if all_income else 0
        overall_avg_expenses = sum(all_expenses) / len(all_expenses) if all_expenses else 0
        
        for month_num in range(1, 13):
            if monthly_income[month_num]:
                avg_income_by_month[month_num] = sum(monthly_income[month_num]) / len(monthly_income[month_num])
            else:
                avg_income_by_month[month_num] = overall_avg_income
            
            if monthly_expenses[month_num]:
                avg_expenses_by_month[month_num] = sum(monthly_expenses[month_num]) / len(monthly_expenses[month_num])
            else:
                avg_expenses_by_month[month_num] = overall_avg_expenses
        
        # Get recurring income
        recurring_income = self._detect_recurring_income()
        monthly_recurring_income = sum(r['avg_amount'] for r in recurring_income)
        
        # Get recurring bills
        bills = self.get_all_bills()
        monthly_recurring_expenses = sum(b.get('amount', 0) for b in bills)
        
        # Generate forecast
        forecast = []
        now = datetime.now()
        
        for i in range(months_ahead):
            forecast_date = now + timedelta(days=30 * i)
            month_num = forecast_date.month
            year = forecast_date.year
            month_name = calendar.month_name[month_num]
            
            # Projected income (historical average + recurring)
            projected_income = avg_income_by_month.get(month_num, overall_avg_income) + monthly_recurring_income
            
            # Projected expenses (historical average + recurring bills)
            projected_expenses = avg_expenses_by_month.get(month_num, overall_avg_expenses) + monthly_recurring_expenses
            
            # Net cash flow
            net_cash_flow = projected_income - projected_expenses
            
            forecast.append({
                'month': f"{year}-{month_num:02d}",
                'month_name': f"{month_name} {year}",
                'projected_income': projected_income,
                'projected_expenses': projected_expenses,
                'net_cash_flow': net_cash_flow,
                'is_positive': net_cash_flow > 0,
            })
        
        return forecast

