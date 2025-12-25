# Bank Statement Sanitizer

## Project Overview

This project aims to develop a robust Python application for sanitizing sensitive information from bank statement files (PDF, TXT, etc.). The primary goal is to enable users to share their bank information with AI tools for purposes like expense tracking, budgeting, and financial analysis without compromising their privacy.

## Features

### Core Sanitization
- **Sensitive Data Redaction:** Identify and remove personally identifiable information (PII) such as account numbers, names, addresses, and transaction details from bank statements.
- **File Type Support:** Support for PDF, TXT, CSV, and Excel (.xlsx, .xls) files.
- **Directory Processing:** Process all eligible files within a specified input directory or single files.
- **Intelligent Skipping:** Automatically skip files that have already been sanitized (identified by a "-sanitized" suffix in the filename).
- **Output Management:** Save sanitized files with a clear naming convention (e.g., `original_filename-sanitized.pdf`).
- **AI-Friendly Metadata:** Optional metadata headers in sanitized files to help AI tools understand the data.

### Transaction Analysis
- **Automatic Categorization:** Automatically categorize transactions (Groceries, Restaurants, Gas, Utilities, Subscriptions, etc.) based on merchant names and keywords.
- **Merchant Name Extraction:** Extract clean merchant names from transaction descriptions (e.g., "AMZN MKTP US*1234" → "Amazon").
- **Recurring Transaction Detection:** Automatically identify subscriptions and recurring bills based on patterns.
- **SQLite Database Export:** Export sanitized transactions to a SQLite database for analysis and tax preparation.
- **Date Range Filtering:** Filter transactions by date range when exporting or querying.
- **Bank/Issuer Tracking:** Automatically detects and tracks bank/issuer names (Discover, American Express, Charles Schwab, etc.) for multi-bank analysis.
- **Account Type Detection:** Identifies account types (checking, savings, credit_card) for better organization.

### Financial Management Features
- **Account Balance Tracking:** Extracts and tracks account balances over time from statements, including credit limits, available credit, and APR.
- **Debt Payoff Calculator:** Calculate optimal debt payoff strategies (snowball vs avalanche) with interest calculations and payoff timelines.
- **Bill Detection & Reminders:** Automatically detects recurring bills, tracks due dates, and shows upcoming payments.
- **Payment Due Date Tracking:** Extracts payment due dates from credit card statements to avoid late fees.
- **Budget Tracking:** Set monthly budgets by category, track spending vs budget, and get alerts when approaching limits.
- **Financial Goals Tracking:** Set and track financial goals (debt payoff, savings, investments) with progress monitoring.
- **Cash Flow Forecasting:** Predict future cash flow based on historical patterns and identify potential cash flow issues.

### Income Tracking
- **Paystub Support:** Extract structured data from paystubs including gross pay, net pay, deductions, and year-to-date totals.
- **Multiple Paystubs per PDF:** Handles PDFs containing multiple paystubs, extracting each individually.
- **Income Analytics:** Compare income vs spending, calculate savings rate, and track income trends.
- **Recurring Income Detection:** Automatically detect and track recurring income sources (salary, dividends, interest).

### Tax Preparation
- **Tax Document Extraction:** Extract data from 1099-INT, 1099-DIV, 1099-B, and W-2 forms.
- **Tax-Deductible Expense Tracking:** Automatically categorize and track deductible expenses (business, medical, charity, etc.).
- **Tax Summary Reports:** Generate comprehensive tax summaries by year with all income sources.
- **Tax Report Export:** Export tax-ready reports for filing (Schedule A, Schedule C, Schedule D).
- **See [TAX_PREPARATION_GUIDE.md](TAX_PREPARATION_GUIDE.md) for complete tax preparation workflow.**

### Query & Export
- **Database Query Interface:** Query transactions by category, merchant, bank, account type, amount range, date range, and recurring status.
- **Multiple Export Formats:** Export to CSV (for NotebookLM/AI tools), JSON (for programmatic access), or summary reports.
- **Incremental Import:** Add new statements to existing database without duplicates (both file-level and transaction-level duplicate prevention).
- **Spending Analytics:** Generate comprehensive spending reports with monthly trends, category breakdowns, and top merchants.
- **Data Validation:** Validate data quality, check for duplicates, and ensure data integrity.

## Architecture

The application is designed with modularity in mind, following a Model-View-Controller (MVC) pattern:

- **Model:** Handles the core logic of reading, parsing, and sanitizing bank statement data. Includes modules for different file types (`pdf_handler.py`, `txt_handler.py`, `csv_handler.py`, `excel_handler.py`), sanitization (`sanitizer.py`), categorization (`transaction_categorizer.py`), merchant extraction (`merchant_extractor.py`), paystub extraction (`paystub_extractor.py`), balance extraction (`balance_extractor.py`), debt calculation (`debt_calculator.py`), tax extraction (`tax_extractor.py`), investment extraction (`investment_extractor.py`), and database operations (`database_exporter.py`, `spending_analytics.py`).
- **View:** Manages command-line interface presentation (`cli.py`) with colored output, progress bars, and formatted messages.
- **Controller:** Orchestrates the overall flow through the main entry point (`sanitize.py`), including CLI argument parsing, file discovery, and workflow management.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository:**
   ```bash
   git clone git@github.com:justinkemersion/python-bank-statement-sanitization.git
   cd python-bank-statement-sanitization
   ```
   
   Or using HTTPS:
   ```bash
   git clone https://github.com/justinkemersion/python-bank-statement-sanitization.git
   cd python-bank-statement-sanitization
   ```

2. **Create and activate a virtual environment:**
   
   On Linux/macOS:
   ```bash
   python3 -m venv myenv
   source myenv/bin/activate
   ```
   
   On Windows:
   ```bash
   python -m venv myenv
   myenv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### GitHub Setup

If you're setting up this project for the first time with an existing remote repository:

1. **Initialize git repository (if not already initialized):**
   ```bash
   git init
   ```

2. **Add the remote repository:**
   ```bash
   git remote add origin git@github.com:justinkemersion/python-bank-statement-sanitization.git
   ```
   
   Or using HTTPS:
   ```bash
   git remote add origin https://github.com/justinkemersion/python-bank-statement-sanitization.git
   ```

3. **Verify the remote:**
   ```bash
   git remote -v
   ```

4. **Stage and commit your files:**
   ```bash
   git add .
   git commit -m "Initial commit"
   ```

5. **Push to GitHub:**
   ```bash
   git branch -M main
   git push -u origin main
   ```

### Usage

**Activate the virtual environment** (if not already activated):
```bash
source myenv/bin/activate  # Linux/macOS
# or
myenv\Scripts\activate     # Windows
```

**Run the sanitizer:**
```bash
python sanitize.py <input_directory> [options]
```

**Basic Examples:**
```bash
# Sanitize files in a directory (output to same directory)
python sanitize.py ./statements

# Specify output directory
python sanitize.py ./statements -o ./sanitized

# Verbose mode with detailed output
python sanitize.py ./statements --verbose

# Quiet mode (only errors)
python sanitize.py ./statements --quiet

# Dry run (see what would be done without modifying files)
python sanitize.py ./statements --dry-run
```

**Command-Line Options:**

**Basic Options:**
- `-o, --output-dir`: Output directory for sanitized files (default: same as input directory)
- `-v, --verbose`: Enable verbose output with detailed processing information
- `-q, --quiet`: Suppress all output except errors
- `--dry-run`: Show what would be done without actually modifying files
- `--no-metadata`: Disable AI-friendly metadata headers in sanitized files
- `--version`: Show version information
- `-h, --help`: Show help message

**Database Export Options:**
- `--export-db <path>`: Export sanitized data to SQLite database for analysis
- `--force-reimport`: Force re-import of files that have already been imported
- `--date-range YYYY-MM-DD:YYYY-MM-DD`: Filter transactions by date range
- `--export-csv <path>`: Export database to CSV file (for NotebookLM/AI tools)
- `--export-json <path>`: Export database to JSON file (for programmatic access)
- `--export-report <path>`: Export database to summary report text file

**Query Options (use with `--query-db`):**
- `--query-db <path>`: Query existing database (query mode)
- `--category <name>`: Filter by category name
- `--merchant <name>`: Filter by merchant name (partial match)
- `--min-amount <amount>`: Filter by minimum transaction amount
- `--max-amount <amount>`: Filter by maximum transaction amount
- `--recurring`: Show only recurring transactions
- `--list-recurring`: List all recurring transactions grouped by merchant
- `--limit <number>`: Limit number of results

**Spending Analytics Options:**
- `--spending-report <path>`: Generate comprehensive spending analysis report
- `--top-categories <N>`: Show top N spending categories
- `--top-merchants <N>`: Show top N merchants by spending
- `--year <YYYY>`: Filter spending reports by specific year

**Debt Management Options:**
- `--show-debts`: Show current debt balances across all credit cards
- `--debt-payoff <amount>`: Calculate debt payoff strategy with specified monthly payment
- `--payoff-strategy <snowball|avalanche|compare>`: Choose payoff strategy (default: compare)

**Investment Account Options:**
- `--show-investments`: Show investment account summary (requires --query-db)
- `--show-holdings`: Show current investment holdings (requires --query-db)

**Bill Management Options:**
- `--show-bills`: Show all recurring bills detected from transactions
- `--upcoming-bills [days]`: Show bills due in next N days (default: 30 days)

**Tax Preparation Options:**
- `--tax-summary [year]`: Show tax summary for a given year (default: current year, requires --query-db)
- `--tax-deductions [year]`: Show tax-deductible expenses for a given year (default: current year, requires --query-db)
- `--export-tax-report <path>`: Export comprehensive tax report to file (requires --query-db)

**Examples:**

**Basic Sanitization:**
```bash
# Sanitize a single file
python sanitize.py statement.pdf

# Sanitize all files in a directory
python sanitize.py ./statements -o ./sanitized
```

**Database Export:**
```bash
# Sanitize and export to database
python sanitize.py ./statements --export-db finances.db

# Export with date range filter
python sanitize.py ./statements --export-db finances.db --date-range 2024-01-01:2024-12-31

# Export to CSV for NotebookLM
python sanitize.py ./statements --export-db finances.db --export-csv transactions.csv

# Export to JSON for programmatic access
python sanitize.py ./statements --export-db finances.db --export-json transactions.json
```

**Querying Database:**
```bash
# List all recurring transactions
python sanitize.py --query-db finances.db --list-recurring

# Query by category
python sanitize.py --query-db finances.db --category "Groceries"

# Query by merchant
python sanitize.py --query-db finances.db --merchant "Amazon"

# Query by amount range
python sanitize.py --query-db finances.db --min-amount 50 --max-amount 200

# Query recurring transactions in date range
python sanitize.py --query-db finances.db --recurring --date-range 2024-01-01:2024-12-31

# Complex query: Groceries over $100
python sanitize.py --query-db finances.db --category "Groceries" --min-amount 100
```

**Spending Analytics:**
```bash
# Generate comprehensive spending report
python sanitize.py --query-db finances.db --spending-report spending_2024.txt

# Show top 10 spending categories
python sanitize.py --query-db finances.db --top-categories 10

# Show top 20 merchants
python sanitize.py --query-db finances.db --top-merchants 20

# Spending report for specific year
python sanitize.py --query-db finances.db --spending-report report.txt --year 2024
```

**Debt Management:**
```bash
# Show current debt balances
python sanitize.py --query-db finances.db --show-debts

# Calculate debt payoff strategy (compare both methods)
python sanitize.py --query-db finances.db --debt-payoff 500 --payoff-strategy compare

# Calculate snowball strategy only
python sanitize.py --query-db finances.db --debt-payoff 500 --payoff-strategy snowball

# Calculate avalanche strategy only
python sanitize.py --query-db finances.db --debt-payoff 500 --payoff-strategy avalanche
```

**Bill Management:**
```bash
# Show all recurring bills
python sanitize.py --query-db finances.db --show-bills

# Show bills due in next 14 days
python sanitize.py --query-db finances.db --upcoming-bills 14

# Show bills due in next 30 days (default)
python sanitize.py --query-db finances.db --upcoming-bills
```

**Note:** The old `src/main.py` entry point still works but is deprecated. Use `sanitize.py` for the enhanced CLI experience.

## Quick Start for NotebookLM

**Want to quickly sanitize your bank data and upload to NotebookLM?** See the [NotebookLM Quick Start Guide](#notebooklm-quick-start) below for a streamlined workflow.

### Development

When working on the project, always ensure your virtual environment is activated. You can verify this by checking that your terminal prompt shows `(myenv)` at the beginning.

To deactivate the virtual environment when you're done:
```bash
deactivate
```

## NotebookLM Quick Start

**Get your financial data ready for NotebookLM in 3 simple steps!**

### Step 1: Collect Your Statements

Download your bank statements (PDF, CSV, or Excel) from:
- Credit cards (Discover, American Express, etc.)
- Checking accounts (Charles Schwab, etc.)
- Any other financial accounts

Organize them in a directory:
```bash
mkdir ~/financial_data_2024
# Download all your statements here
```

### Step 2: Sanitize and Export (One Command!)

Run this single command to sanitize, organize, and export everything:
```bash
python sanitize.py ~/financial_data_2024 \
  --export-db ~/finances_2024.db \
  --export-csv ~/finances_2024.csv
```

**What this does:**
- ✅ Sanitizes all files (removes sensitive data like account numbers, SSN, etc.)
- ✅ Extracts transactions, balances, and paystubs
- ✅ Organizes by bank/issuer (Discover, AMEX, Charles Schwab, etc.)
- ✅ Categorizes transactions automatically
- ✅ Detects recurring bills and subscriptions
- ✅ Creates a CSV file ready for NotebookLM

### Step 3: Upload to NotebookLM

1. Go to [NotebookLM](https://notebooklm.google.com)
2. Create a new notebook
3. Upload the CSV file (`finances_2024.csv`)
4. Start asking questions!

### What Data Gets Exported?

The CSV includes everything NotebookLM needs:
- **Transactions:** Date, amount, merchant, category, bank name
- **Account Information:** Account type (checking/credit_card), bank name
- **Balances:** Account balances over time (if extracted)
- **Metadata:** Explains what was sanitized and how to interpret the data

### Example NotebookLM Prompts

Once uploaded, try these prompts:

**Spending Analysis:**
- "What are my top 10 spending categories this year?"
- "Show me all spending on my Discover card"
- "Compare my spending between credit cards and checking account"
- "What's my average monthly spending on restaurants?"

**Debt Management:**
- "What's my total debt across all credit cards?"
- "How should I prioritize paying off Discover vs American Express?"
- "Calculate my debt payoff timeline if I pay $500/month"
- "Which credit card has the highest balance?"

**Bill Management:**
- "What bills are due this month?"
- "Show me all my recurring subscriptions"
- "What's my total monthly bill obligations?"

**Income & Budget:**
- "What's my total income this year?"
- "Compare my income vs expenses"
- "What's my savings rate?"
- "Help me create a budget based on my actual spending"

**Merchant Analysis:**
- "Where am I spending too much money?"
- "Show me all Amazon purchases this year"
- "Which merchants appear on multiple credit cards?"

**Tax Preparation:**
- "Identify all tax-deductible expenses"
- "What were my total business expenses?"
- "Categorize expenses for tax filing"

### Pro Tips for NotebookLM

1. **Start Broad, Then Narrow:** Begin with overview questions, then drill down
2. **Use Bank Names:** Reference specific banks ("Show me Discover spending") for better results
3. **Ask for Comparisons:** "Compare X vs Y" questions work great
4. **Request Action Plans:** Ask for strategies ("How should I pay off debt?")
5. **Export Insights:** Ask NotebookLM to summarize key findings

### Incremental Updates

Add new statements throughout the year:
```bash
# Add January statement
python sanitize.py jan_statement.pdf --export-db ~/finances_2024.db

# Add February statement
python sanitize.py feb_statement.pdf --export-db ~/finances_2024.db

# ... continue each month

# At year end, export everything to CSV
python sanitize.py . --export-db ~/finances_2024.db --export-csv ~/finances_2024.csv
```

The database automatically prevents duplicates, so you can safely re-import or add overlapping statements.

### Multi-Bank Workflow

If you have statements from multiple banks (Discover, AMEX, Charles Schwab, etc.):

```bash
# Process all statements at once
python sanitize.py ~/all_statements_2024 \
  --export-db ~/finances_2024.db \
  --export-csv ~/finances_2024.csv
```

The system automatically:
- Detects which bank each statement is from
- Separates transactions by bank/issuer
- Tracks balances per bank
- Enables bank-specific queries in NotebookLM

### What Makes This Perfect for NotebookLM?

1. **Structured Data:** CSV format with clear columns and metadata
2. **Bank Separation:** Transactions tagged by bank for easy filtering
3. **Rich Context:** Categories, merchants, and account types included
4. **Safe:** All sensitive data removed before upload
5. **Comprehensive:** Transactions, balances, bills, and income all in one file

For more detailed NotebookLM workflow guidance, see [NOTEBOOKLM_WORKFLOW.md](NOTEBOOKLM_WORKFLOW.md).