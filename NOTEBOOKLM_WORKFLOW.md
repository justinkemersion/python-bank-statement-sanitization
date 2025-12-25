# NotebookLM Workflow Guide

## Best Workflow for Expense Analysis with NotebookLM

### Recommended Approach

**Option 1: Database + CSV Export (Recommended)**
This gives you the most structured data for AI analysis.

### Step-by-Step Workflow

#### 1. Collect Your Statements
Download all 12 months of bank statements (PDF, CSV, or Excel format) into a directory:
```bash
mkdir ~/statements_2024
# Download all your statements here
```

#### 2. Sanitize and Build Database (One Command!)
Process all files and build your database in one go:
```bash
python sanitize.py ~/statements_2024 --export-db ~/2024_finances.db --export-csv ~/2024_transactions.csv
```

This will:
- ✅ Sanitize all files (remove sensitive data)
- ✅ Create SQLite database with all transactions
- ✅ Export to CSV for NotebookLM upload

#### 3. Upload to NotebookLM
Upload the CSV file (`2024_transactions.csv`) to NotebookLM. The CSV includes:
- All transactions with dates, amounts, descriptions
- Metadata explaining what was sanitized
- Safe for AI analysis (no sensitive data)

#### 4. Ask NotebookLM Questions
Once uploaded, you can ask questions like:
- "What are my top spending categories?"
- "Show me all transactions over $500"
- "What's my average monthly spending?"
- "Identify any unusual spending patterns"
- "Help me categorize expenses for tax deductions"

### Alternative: Incremental Building

If you want to add statements throughout the year:

```bash
# January
python sanitize.py jan_statement.csv --export-db 2024_finances.db

# February  
python sanitize.py feb_statement.csv --export-db 2024_finances.db

# ... continue each month

# At year end, export everything to CSV
python sanitize.py . --export-db 2024_finances.db --export-csv 2024_transactions.csv
```

### What Gets Exported to CSV?

The CSV includes:
- **transaction_date**: Date of transaction
- **amount**: Amount (negative = debit, positive = credit)
- **description**: Transaction description (sanitized)
- **category**: Category if available
- **transaction_type**: 'debit' or 'credit'
- **source_file**: Which statement it came from
- **reference_number**: Transaction reference
- **notes**: Additional notes

### Additional Export Options

#### Summary Report (Human-Readable)
```bash
python sanitize.py ~/statements_2024 --export-db ~/2024_finances.db --export-report ~/2024_summary.txt
```

This creates a text report with:
- Overview statistics
- Monthly breakdowns
- Top spending categories
- Perfect for quick overview before detailed analysis

### Why This Workflow?

1. **Database First**: Structured, queryable data for complex analysis
2. **CSV Export**: Easy upload to NotebookLM (CSV is well-supported)
3. **Incremental**: Build your database month-by-month
4. **Safe**: All sensitive data removed before AI analysis
5. **Comprehensive**: All transactions in one place

### Example NotebookLM Prompts

Once you upload the CSV, try these prompts:

**Spending Analysis:**
- "Analyze my spending patterns and identify my top 10 expense categories"
- "What's my average spending per month?"
- "Show me months where I spent significantly more than average"

**Tax Preparation:**
- "Identify all transactions that might be tax-deductible"
- "Categorize my expenses into tax categories"
- "What were my total business expenses this year?"

**Budget Planning:**
- "Help me create a budget based on my actual spending"
- "What are my recurring monthly expenses?"
- "Identify areas where I could reduce spending"

**Pattern Recognition:**
- "Are there any unusual spending patterns I should be aware of?"
- "What times of year do I spend the most?"
- "Identify any duplicate or suspicious transactions"

### Tips

1. **Start with Summary**: Use `--export-report` first to get an overview
2. **Upload CSV**: NotebookLM works best with CSV files
3. **Ask Specific Questions**: More specific = better AI analysis
4. **Iterate**: Upload new data as you get more statements
5. **Keep Database**: The SQLite DB is useful for SQL queries later

