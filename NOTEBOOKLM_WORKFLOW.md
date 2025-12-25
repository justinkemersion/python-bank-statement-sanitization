# NotebookLM Quick Start Guide

**Get your financial data ready for NotebookLM in minutes!**

## 🚀 Quick Start (3 Steps)

### Step 1: Collect Your Statements

Download statements from all your accounts:
- **Credit Cards:** Discover, American Express, etc.
- **Checking/Savings:** Charles Schwab, Bank of America, etc.
- **Paystubs:** If you want income tracking

Put them all in one directory:
```bash
mkdir ~/financial_data_2024
# Download all statements here
```

### Step 2: Sanitize and Export (One Command!)

```bash
python sanitize.py ~/financial_data_2024 \
  --export-db ~/finances_2024.db \
  --export-csv ~/finances_2024.csv
```

**That's it!** This single command:
- ✅ Sanitizes all files (removes sensitive data)
- ✅ Extracts transactions, balances, bills, and paystubs
- ✅ Organizes by bank/issuer automatically
- ✅ Creates a CSV ready for NotebookLM

### Step 3: Upload to NotebookLM

1. Go to [NotebookLM](https://notebooklm.google.com)
2. Create a new notebook
3. Upload `finances_2024.csv`
4. Start asking questions!

---

## 📊 What Data Gets Exported?

The CSV includes everything NotebookLM needs:

### Transaction Data
- **transaction_date**: When the transaction occurred
- **amount**: Transaction amount (negative = spending, positive = income)
- **description**: Transaction description (sanitized - safe for AI)
- **merchant_name**: Clean merchant name (e.g., "Amazon" instead of "AMZN MKTP US*1234")
- **category**: Auto-categorized (Groceries, Restaurants, Gas, etc.)
- **account_type**: checking, savings, or credit_card
- **bank_name**: Discover, American Express, Charles Schwab, etc.
- **is_recurring**: Whether it's a recurring bill/subscription

### Why This Structure?

- **Bank Separation:** Query "Show me Discover spending" vs "Show me AMEX spending"
- **Account Types:** Compare credit card vs checking account spending
- **Categories:** Analyze spending by category across all accounts
- **Merchants:** Find where you're spending too much

---

## 💡 Example NotebookLM Prompts

### Spending Analysis

**Overview Questions:**
- "What are my top 10 spending categories this year?"
- "What's my total spending by bank (Discover, AMEX, etc.)?"
- "Compare my credit card spending vs checking account spending"
- "What's my average monthly spending?"

**Bank-Specific Questions:**
- "Show me all spending on my Discover card"
- "What's my total debt on American Express?"
- "Compare spending between Discover and AMEX"
- "Which bank do I spend the most on?"

**Category Questions:**
- "How much do I spend on restaurants per month?"
- "Show me all grocery purchases"
- "What's my total gas spending this year?"
- "Which category do I overspend in?"

**Merchant Questions:**
- "Where am I spending too much money?"
- "Show me all Amazon purchases"
- "Which merchants appear on multiple credit cards?"
- "What's my spending at Starbucks this year?"

### Debt Management

**Debt Overview:**
- "What's my total debt across all credit cards?"
- "Show me the balance for each credit card"
- "Which credit card has the highest balance?"
- "What are the interest rates on my credit cards?"

**Payoff Strategy:**
- "How should I prioritize paying off Discover vs AMEX?"
- "If I pay $500/month, how long to pay off all debt?"
- "Which debt payoff strategy saves me more money?"
- "Calculate my debt payoff timeline"

**Payment Planning:**
- "What are the minimum payments for each credit card?"
- "When are my credit card payments due?"
- "How much interest am I paying per month?"

### Bill Management

**Recurring Bills:**
- "What bills are due this month?"
- "Show me all my recurring subscriptions"
- "What's my total monthly bill obligations?"
- "Which bills have I paid most consistently?"

**Payment Tracking:**
- "Have I paid all my bills this month?"
- "Which bills are overdue?"
- "What's the total amount due in the next 30 days?"

### Income & Budget

**Income Analysis:**
- "What's my total income this year?"
- "What's my average monthly take-home pay?"
- "How much am I contributing to retirement?"
- "What percentage of income goes to taxes?"

**Budget Planning:**
- "Compare my income vs expenses"
- "What's my savings rate?"
- "Help me create a budget based on my actual spending"
- "How much can I afford to save each month?"

**Cash Flow:**
- "Show me months with negative cash flow"
- "What's my average monthly income vs spending?"
- "When do I have the most money left over?"

### Tax Preparation

**Deductions:**
- "Identify all tax-deductible expenses"
- "What were my total business expenses?"
- "Show me vehicle maintenance expenses"
- "Categorize expenses for tax filing"

**Income Documentation:**
- "What's my total W-2 income this year?"
- "Show me all paystub data"
- "What deductions were taken from my paychecks?"

### Advanced Analysis

**Patterns:**
- "Are there any unusual spending patterns?"
- "What times of year do I spend the most?"
- "Identify any duplicate or suspicious transactions"
- "Show me spending trends over time"

**Optimization:**
- "Where can I reduce spending?"
- "Which subscriptions can I cancel?"
- "What's my biggest expense category?"
- "How can I improve my savings rate?"

---

## 🔄 Incremental Workflow

Add statements throughout the year:

```bash
# January
python sanitize.py jan_statement.pdf --export-db ~/finances_2024.db

# February
python sanitize.py feb_statement.pdf --export-db ~/finances_2024.db

# ... continue each month

# At year end, export everything to CSV
python sanitize.py . --export-db ~/finances_2024.db --export-csv ~/finances_2024.csv
```

**Benefits:**
- Database prevents duplicates automatically
- Can add overlapping statements safely
- Build comprehensive database over time
- Export fresh CSV whenever needed

---

## 🏦 Multi-Bank Workflow

If you have statements from multiple banks:

```bash
# Process all at once
python sanitize.py ~/all_statements_2024 \
  --export-db ~/finances_2024.db \
  --export-csv ~/finances_2024.csv
```

**The system automatically:**
- Detects bank/issuer from filenames and content
- Tags each transaction with bank name
- Separates by account type (credit_card, checking, savings)
- Enables bank-specific queries in NotebookLM

**Example queries:**
- "Show me all Discover card transactions"
- "Compare spending between my credit cards"
- "What's my debt on each bank?"

---

## 📈 Pre-Upload Analysis

Before uploading to NotebookLM, you can get a quick overview:

```bash
# Generate summary report
python sanitize.py ~/financial_data_2024 \
  --export-db ~/finances_2024.db \
  --export-report ~/summary.txt

# View current debts
python sanitize.py --query-db ~/finances_2024.db --show-debts

# See upcoming bills
python sanitize.py --query-db ~/finances_2024.db --upcoming-bills

# Top spending categories
python sanitize.py --query-db ~/finances_2024.db --top-categories 10
```

This helps you understand your data before asking NotebookLM questions.

---

## 🎯 Pro Tips

### 1. Be Specific
**Good:** "Show me all Discover card spending on restaurants"
**Less Good:** "Show me spending"

### 2. Use Bank Names
**Good:** "What's my total debt on American Express?"
**Less Good:** "What's my debt?"

### 3. Ask for Comparisons
**Good:** "Compare my spending between Discover and AMEX"
**Good:** "Compare credit card vs checking account spending"

### 4. Request Strategies
**Good:** "How should I prioritize paying off my debts?"
**Good:** "Help me create a budget based on my spending"

### 5. Ask for Insights
**Good:** "What patterns do you see in my spending?"
**Good:** "Identify areas where I could save money"

### 6. Use Date Ranges
**Good:** "Show me spending in Q4 2024"
**Good:** "Compare January vs December spending"

---

## 🔒 Privacy & Security

**What gets sanitized:**
- ✅ Account numbers → `[ACCOUNT_NUMBER_REDACTED]`
- ✅ Social Security Numbers → `[SSN_REDACTED]`
- ✅ Credit card numbers → `[CREDIT_CARD_REDACTED]`
- ✅ Email addresses → `[EMAIL_REDACTED]`
- ✅ Phone numbers → `[PHONE_NUMBER_REDACTED]`
- ✅ Street addresses → `[ADDRESS_REDACTED]`
- ✅ Routing numbers → `[ROUTING_NUMBER_REDACTED]`

**What stays:**
- ✅ Transaction dates
- ✅ Amounts
- ✅ Merchant names (cleaned)
- ✅ Categories
- ✅ Bank/issuer names
- ✅ Account types

**The CSV is safe to upload to NotebookLM** - all sensitive PII has been removed.

---

## 📝 CSV Structure

The exported CSV includes these columns:

| Column | Description | Example |
|--------|-------------|---------|
| `transaction_date` | Date of transaction | 2024-01-15 |
| `amount` | Transaction amount | -45.67 |
| `description` | Transaction description | AMAZON MKTP US |
| `merchant_name` | Clean merchant name | Amazon |
| `category` | Auto-categorized | Online Shopping |
| `account_type` | Type of account | credit_card |
| `bank_name` | Bank/issuer | Discover |
| `transaction_type` | debit or credit | debit |
| `source_file` | Source statement | discover_jan_2024.pdf |
| `is_recurring` | Recurring bill? | Yes/No |

---

## 🚨 Troubleshooting

**Problem:** CSV is empty or missing data
- **Solution:** Check that statements were processed successfully. Use `--verbose` flag to see details.

**Problem:** Bank names not detected
- **Solution:** Ensure filenames include bank name (e.g., `discover_statement.pdf`). The system detects from filename and content.

**Problem:** Duplicate transactions
- **Solution:** The system prevents duplicates automatically. If you see duplicates, use `--force-reimport` to refresh.

**Problem:** Missing categories
- **Solution:** Categories are auto-assigned based on merchant names. Some transactions may be "Uncategorized" if merchant isn't recognized.

---

## 📚 Additional Resources

- **Full Documentation:** See [README.md](README.md) for complete feature list
- **CLI Help:** Run `python sanitize.py --help` for all options
- **Database Queries:** See README for query examples

---

## 🎉 You're Ready!

Your financial data is now:
- ✅ Sanitized (safe for AI)
- ✅ Organized (by bank, category, date)
- ✅ Structured (ready for analysis)
- ✅ Comprehensive (transactions, balances, bills, income)

Upload to NotebookLM and start getting insights!
