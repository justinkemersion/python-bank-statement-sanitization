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

### Query & Export
- **Database Query Interface:** Query transactions by category, merchant, amount range, date range, and recurring status.
- **Multiple Export Formats:** Export to CSV (for NotebookLM/AI tools), JSON (for programmatic access), or summary reports.
- **Incremental Import:** Add new statements to existing database without duplicates.

## Architecture (Planned)

The application will be designed with modularity in mind, loosely following a Model-View-Controller (MVC) pattern to facilitate future expansion and maintenance.

- **Model:** Handles the core logic of reading, parsing, and sanitizing bank statement data. This will include modules for different file types (e.g., `pdf_parser.py`, `txt_parser.py`) and a `sanitizer.py` module for redaction.
- **View:** (Implicit for a CLI application) Handles how information is presented to the user, such as progress updates and confirmation messages.
- **Controller:** Manages the overall flow of the application, including CLI argument parsing, file discovery, orchestrating the sanitization process, and file saving. This will likely be the main script (`main.py`).

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
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
   git remote add origin <your-repo-url>
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

**Note:** The old `src/main.py` entry point still works but is deprecated. Use `sanitize.py` for the enhanced CLI experience.

### Development

When working on the project, always ensure your virtual environment is activated. You can verify this by checking that your terminal prompt shows `(myenv)` at the beginning.

To deactivate the virtual environment when you're done:
```bash
deactivate
```