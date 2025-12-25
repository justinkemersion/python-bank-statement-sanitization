# Use Case Verification: Multi-Account Financial Planning

**Your Goal:** Download a year's worth of statements, sanitize them, extract important information, and export for NotebookLM to help plan finances.

## ✅ Verified Account Support

### Credit Cards
- **Discover** ✅
  - Bank Detection: `Discover`
  - Account Type: `credit_card`
  - Transaction Extraction: ✅
  - Balance Tracking: ✅ (credit limit, minimum payment, APR)
  
- **American Express (AMEX)** ✅
  - Bank Detection: `American Express`
  - Account Type: `credit_card`
  - Transaction Extraction: ✅
  - Balance Tracking: ✅

- **Chase** ✅
  - Bank Detection: `Chase`
  - Account Type: `credit_card`
  - Transaction Extraction: ✅
  - Balance Tracking: ✅

### Banking
- **Charles Schwab Checking** ✅
  - Bank Detection: `Charles Schwab`
  - Account Type: `checking`
  - Transaction Extraction: ✅
  - Balance Tracking: ✅

### Investment Accounts
- **Charles Schwab Roth IRA** ✅
  - Bank Detection: `Charles Schwab`
  - Account Type: `roth_ira`
  - Portfolio Value Extraction: ✅
  - Holdings Extraction: ✅ (securities, quantities, values)
  - Investment Transactions: ✅ (buys, sells, dividends, contributions)

- **Charles Schwab Rollover IRA** ✅
  - Bank Detection: `Charles Schwab`
  - Account Type: `traditional_ira` (includes rollover)
  - Portfolio Value Extraction: ✅
  - Holdings Extraction: ✅
  - Investment Transactions: ✅

## 📊 What Gets Extracted for NotebookLM

### From Credit Card Statements:
- ✅ All transactions (date, amount, merchant, category)
- ✅ Account balances (current balance, credit limit, available credit)
- ✅ Minimum payments and due dates
- ✅ Bank/issuer name (Discover, AMEX, Chase)
- ✅ Recurring bills detection

### From Checking Account Statements:
- ✅ All transactions (date, amount, merchant, category)
- ✅ Account balances
- ✅ Bank name (Charles Schwab)
- ✅ Transaction types (debits/credits)

### From Investment Account Statements (Roth IRA, Rollover IRA):
- ✅ Portfolio value
- ✅ Holdings (ticker symbols, quantities, current values)
- ✅ Investment transactions (buys, sells, dividends, contributions, withdrawals)
- ✅ Account type (roth_ira, traditional_ira)
- ✅ Bank name (Charles Schwab)

## 🚀 Workflow for Your Use Case

### Step 1: Download All Statements
Put all PDFs in one directory:
```
~/financial_data_2024/
├── discover_jan_2024.pdf
├── discover_feb_2024.pdf
├── amex_jan_2024.pdf
├── amex_feb_2024.pdf
├── chase_jan_2024.pdf
├── chase_feb_2024.pdf
├── schwab_checking_jan_2024.pdf
├── schwab_checking_feb_2024.pdf
├── schwab_roth_ira_jan_2024.pdf
├── schwab_roth_ira_feb_2024.pdf
├── schwab_rollover_ira_jan_2024.pdf
└── schwab_rollover_ira_feb_2024.pdf
```

### Step 2: Sanitize and Export (One Command!)
```bash
python sanitize.py ~/financial_data_2024 \
  --export-db ~/finances_2024.db \
  --export-csv ~/finances_2024.csv \
  --verbose
```

**What This Does:**
1. ✅ Sanitizes all PDFs (removes account numbers, SSN, etc.)
2. ✅ Detects bank name for each file (Discover, AMEX, Chase, Charles Schwab)
3. ✅ Detects account type (credit_card, checking, roth_ira, traditional_ira)
4. ✅ Extracts transactions from credit cards and checking
5. ✅ Extracts investment data from Roth IRA and Rollover IRA
6. ✅ Extracts account balances from all accounts
7. ✅ Categorizes all transactions automatically
8. ✅ Detects recurring bills
9. ✅ Stores everything in SQLite database
10. ✅ Exports to CSV for NotebookLM

### Step 3: Upload to NotebookLM
1. Go to [NotebookLM](https://notebooklm.google.com)
2. Create new notebook
3. Upload `finances_2024.csv`
4. Start planning!

## 💡 Example NotebookLM Questions You Can Ask

### Credit Card Analysis:
- "What's my total spending on Discover this year?"
- "Compare my spending between Discover, AMEX, and Chase"
- "What's my current debt on each credit card?"
- "Which credit card do I spend the most on?"
- "What are my recurring bills across all credit cards?"

### Investment Analysis:
- "What's the total value of my Roth IRA?"
- "What's the total value of my Rollover IRA?"
- "What securities do I own across all investment accounts?"
- "What's my total portfolio value (Roth + Rollover IRA)?"
- "What investment transactions did I make this year?"

### Overall Financial Planning:
- "What's my total spending vs income this year?"
- "What's my net worth (checking + investments - credit card debt)?"
- "What are my top spending categories across all accounts?"
- "How much am I saving/investing each month?"
- "What's my debt-to-income ratio?"
- "Create a budget based on my spending patterns"

## ✅ Data Organization

The CSV export includes:
- **Bank separation:** All data tagged with bank_name (Discover, AMEX, Chase, Charles Schwab)
- **Account type separation:** All data tagged with account_type (credit_card, checking, roth_ira, traditional_ira)
- **Transaction categorization:** Automatic categorization (Groceries, Restaurants, Gas, etc.)
- **Merchant standardization:** Clean merchant names (Amazon, Target, etc.)
- **Investment data:** Holdings and investment transactions included
- **Balance tracking:** Account balances and credit limits

## 🎯 Result

You'll have a **single CSV file** with:
- ✅ All transactions from Discover, AMEX, Chase credit cards
- ✅ All transactions from Charles Schwab checking
- ✅ All investment data from Roth IRA and Rollover IRA
- ✅ All account balances and credit limits
- ✅ Everything organized by bank and account type
- ✅ Everything sanitized (safe for AI)
- ✅ Ready for NotebookLM to analyze and help you plan

**Perfect for financial planning!** 🎉

