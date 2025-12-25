# Tax Preparation Guide

**Complete guide to using the Bank Statement Sanitizer for tax preparation and filing.**

## 🎯 Overview

This tool helps you prepare for tax filing by:
- Extracting data from tax documents (1099-INT, 1099-DIV, 1099-B, W-2)
- Tracking tax-deductible expenses throughout the year
- Generating tax-ready reports
- Organizing all financial data for tax filing
- Enabling AI assistance (NotebookLM) for tax preparation

---

## 📋 Step 1: Collect Your Tax Documents

### Required Documents

**Income Documents:**
- **W-2 Forms**: Wage statements from all employers
- **1099-INT**: Interest income from banks/savings accounts
- **1099-DIV**: Dividend income from investments
- **1099-B**: Broker transactions (capital gains/losses)
- **1099-MISC**: Miscellaneous income (if applicable)
- **1099-NEC**: Non-employee compensation (if applicable)

**Expense Documents:**
- Bank statements (for deductible expenses)
- Credit card statements (for business expenses)
- Receipts (for business, medical, charitable expenses)

**Investment Documents:**
- Investment account statements
- IRA contribution statements
- 401(k) statements

### Organize Your Files

Create a directory for tax documents:
```bash
mkdir ~/tax_documents_2024
# Download all your tax documents here
```

---

## 🔧 Step 2: Sanitize and Import Tax Documents

### Process All Documents

Run the sanitizer on your tax documents directory:

```bash
python sanitize.py ~/tax_documents_2024 \
  --export-db ~/tax_2024.db \
  --export-csv ~/tax_2024.csv
```

**What this does:**
- ✅ Sanitizes all documents (removes sensitive data)
- ✅ Extracts tax form data (W-2, 1099s)
- ✅ Extracts transactions and expenses
- ✅ Creates database for analysis
- ✅ Exports CSV for NotebookLM

### Supported Tax Documents

The tool automatically detects and extracts:
- **1099-INT**: Interest income, federal tax withheld
- **1099-DIV**: Ordinary dividends, qualified dividends, capital gains
- **1099-B**: Broker proceeds, cost basis, gains/losses
- **W-2**: Wages, federal/state taxes, SS/Medicare

---

## 📊 Step 3: Review Your Tax Summary

### View Tax Summary

```bash
python sanitize.py --query-db ~/tax_2024.db --tax-summary 2024
```

**Shows:**
- Total interest income
- Total dividend income (ordinary and qualified)
- Total capital gains/losses
- Total wages
- Total federal tax withheld
- Breakdown by document type

### View Tax-Deductible Expenses

```bash
python sanitize.py --query-db ~/tax_2024.db --tax-deductions 2024
```

**Shows:**
- Total deductible expenses
- Expenses by category (Business, Medical, Charity, etc.)
- Recent deductible expenses
- Ready for Schedule A (Itemized Deductions)

**Deductible Categories Tracked:**
- Business Expenses
- Medical Expenses
- Charitable Contributions
- Education Expenses
- Home Office Expenses
- Vehicle Maintenance (business use)
- Professional Services

---

## 📄 Step 4: Generate Tax Report

### Export Comprehensive Tax Report

```bash
python sanitize.py --query-db ~/tax_2024.db --export-tax-report tax_report_2024.txt
```

**Report Includes:**
- Tax year summary
- All income sources (W-2, 1099s)
- Tax withholdings
- Tax-deductible expenses by category
- Complete expense list with dates and amounts

**Use this report to:**
- Fill out tax forms (Schedule A, Schedule C, etc.)
- Provide to your tax preparer
- Verify against your tax software
- Keep as a record

---

## 🤖 Step 5: Use NotebookLM for Tax Filing

### Upload Your Data

1. Export your data to CSV:
   ```bash
   python sanitize.py --query-db ~/tax_2024.db --export-csv tax_data_2024.csv
   ```

2. Upload `tax_data_2024.csv` to [NotebookLM](https://notebooklm.google.com)

3. Upload your tax report:
   ```bash
   python sanitize.py --query-db ~/tax_2024.db --export-tax-report tax_report_2024.txt
   ```
   Upload `tax_report_2024.txt` to NotebookLM

### Example NotebookLM Prompts

**Income Verification:**
- "What's my total income for 2024 from all sources?"
- "Show me all my W-2 income"
- "What interest income did I receive this year?"
- "What dividends did I receive, and how much was qualified?"
- "What were my capital gains or losses?"

**Deduction Analysis:**
- "What are my total tax-deductible expenses for 2024?"
- "Show me all my business expenses"
- "What medical expenses can I deduct?"
- "What charitable contributions did I make?"
- "Help me categorize expenses for Schedule A"

**Tax Form Assistance:**
- "Help me fill out Schedule A (Itemized Deductions)"
- "What goes on line 1 of Form 1040 (wages)?"
- "Calculate my adjusted gross income (AGI)"
- "What's my taxable income after deductions?"
- "Help me identify all tax credits I might qualify for"

**Tax Strategy:**
- "What deductions am I missing?"
- "Should I itemize or take the standard deduction?"
- "What tax-saving strategies should I consider for next year?"
- "Help me estimate my tax refund/owed amount"

**Verification:**
- "Verify my income matches my tax forms"
- "Check for any missing 1099s or W-2s"
- "Are there any duplicate entries in my tax data?"
- "Help me reconcile my bank statements with tax documents"

---

## 📝 Common Tax Scenarios

### Scenario 1: W-2 Employee with Investments

**Documents Needed:**
- W-2 from employer
- 1099-INT from savings accounts
- 1099-DIV from investments
- Bank/credit card statements for deductions

**Workflow:**
```bash
# 1. Process all documents
python sanitize.py ~/tax_docs_2024 --export-db tax_2024.db

# 2. Review summary
python sanitize.py --query-db tax_2024.db --tax-summary 2024

# 3. Check deductions
python sanitize.py --query-db tax_2024.db --tax-deductions 2024

# 4. Export for tax filing
python sanitize.py --query-db tax_2024.db --export-tax-report tax_2024.txt
```

### Scenario 2: Self-Employed / Freelancer

**Documents Needed:**
- 1099-NEC or 1099-MISC (if received)
- Bank statements (business expenses)
- Credit card statements (business expenses)
- Receipts for business expenses

**Workflow:**
```bash
# 1. Process all documents
python sanitize.py ~/tax_docs_2024 --export-db tax_2024.db

# 2. Review business expenses
python sanitize.py --query-db tax_2024.db --category "Business Expenses"

# 3. Get deductible expenses
python sanitize.py --query-db tax_2024.db --tax-deductions 2024

# 4. Export for Schedule C
python sanitize.py --query-db tax_2024.db --export-tax-report schedule_c_2024.txt
```

### Scenario 3: Investor with Multiple Accounts

**Documents Needed:**
- 1099-DIV from all brokerages
- 1099-B from all brokerages
- Investment account statements
- IRA contribution statements

**Workflow:**
```bash
# 1. Process all investment documents
python sanitize.py ~/investment_docs_2024 --export-db tax_2024.db

# 2. Review investment income
python sanitize.py --query-db tax_2024.db --tax-summary 2024

# 3. Check capital gains/losses
python sanitize.py --query-db tax_2024.db --show-investments

# 4. Export for Schedule D
python sanitize.py --query-db tax_2024.db --export-tax-report schedule_d_2024.txt
```

---

## 💡 Tips for Tax Preparation

### 1. Start Early
- Process documents as you receive them throughout the year
- Don't wait until tax season

### 2. Keep Everything Organized
- Use consistent file naming (e.g., `w2_employer_2024.pdf`)
- Organize by document type in folders
- Keep receipts with statements

### 3. Verify Against Originals
- Always verify extracted data against original documents
- The tool helps organize, but you're responsible for accuracy

### 4. Use NotebookLM for Complex Scenarios
- Ask NotebookLM to help with tax strategies
- Get explanations of tax rules
- Verify calculations

### 5. Export Multiple Reports
- Export separate reports for different schedules (A, C, D)
- Keep detailed records for audit purposes

### 6. Track Throughout the Year
- Add documents as you receive them
- Monitor deductible expenses monthly
- Avoid last-minute scrambling

---

## 🔍 Verification Checklist

Before filing, verify:

- [ ] All W-2s processed and income matches
- [ ] All 1099s processed (INT, DIV, B, etc.)
- [ ] Interest income matches bank statements
- [ ] Dividend income matches investment statements
- [ ] Capital gains/losses calculated correctly
- [ ] All deductible expenses captured
- [ ] Business expenses properly categorized
- [ ] Medical expenses above threshold (if applicable)
- [ ] Charitable contributions documented
- [ ] Tax withholdings match W-2s
- [ ] No duplicate entries
- [ ] All documents accounted for

---

## 📚 Tax Form Mapping

### Form 1040 (Main Tax Return)
- **Line 1 (Wages)**: Use `--tax-summary` → Total Wages
- **Line 2b (Taxable Interest)**: Use `--tax-summary` → Interest Income
- **Line 3a (Qualified Dividends)**: Use `--tax-summary` → Qualified Dividends
- **Line 3b (Ordinary Dividends)**: Use `--tax-summary` → Ordinary Dividends
- **Line 7 (Capital Gains)**: Use `--tax-summary` → Capital Gains

### Schedule A (Itemized Deductions)
- **Line 4 (Medical Expenses)**: Use `--tax-deductions` → Medical category
- **Line 11 (Charitable Contributions)**: Use `--tax-deductions` → Charity category
- **Line 13 (Tax Preparation)**: Use `--tax-deductions` → Professional Services

### Schedule C (Business Income)
- **Part I (Income)**: Use transaction queries for business income
- **Part II (Expenses)**: Use `--tax-deductions` → Business Expenses category

### Schedule D (Capital Gains)
- **Part I (Short-term)**: Use investment transaction queries
- **Part II (Long-term)**: Use investment transaction queries
- **1099-B Data**: Use `--tax-summary` → 1099-B information

---

## 🚨 Important Notes

### Disclaimer
- This tool helps organize and extract data, but does not provide tax advice
- Always verify data against original documents
- Consult a tax professional for complex situations
- You are responsible for accurate tax filing

### Data Privacy
- All sensitive data is sanitized before processing
- Account numbers, SSNs, and other PII are redacted
- Safe to use with AI tools like NotebookLM
- Original documents remain private

### Accuracy
- The tool uses pattern matching to extract data
- Some documents may require manual verification
- Always cross-reference with original tax forms
- Report any extraction issues

---

## 🆘 Troubleshooting

### Tax Document Not Detected
- **Problem**: Document not recognized as tax form
- **Solution**: Check filename contains "1099", "W-2", or tax year
- **Solution**: Verify document text contains form identifiers

### Missing Data in Summary
- **Problem**: Some fields not extracted
- **Solution**: Check original document format
- **Solution**: Manually verify and add missing data
- **Solution**: Use `--verbose` to see extraction details

### Deductible Expenses Not Showing
- **Problem**: Expenses not in deductible categories
- **Solution**: Check transaction categorization
- **Solution**: Manually recategorize if needed
- **Solution**: Add custom categories in config.yaml

### Duplicate Documents
- **Problem**: Same document imported multiple times
- **Solution**: Use `--force-reimport` to refresh
- **Solution**: Check `imported_files` table in database

---

## 📖 Additional Resources

- **IRS Forms**: [irs.gov/forms](https://www.irs.gov/forms)
- **Tax Preparation Software**: TurboTax, H&R Block, etc.
- **Tax Professional**: Consult for complex situations
- **NotebookLM**: Use for AI-assisted tax preparation

---

## 🎉 Quick Start Summary

```bash
# 1. Collect all tax documents in one folder
mkdir ~/tax_docs_2024

# 2. Process everything
python sanitize.py ~/tax_docs_2024 --export-db tax_2024.db --export-csv tax_2024.csv

# 3. Review your tax summary
python sanitize.py --query-db tax_2024.db --tax-summary 2024

# 4. Check deductible expenses
python sanitize.py --query-db tax_2024.db --tax-deductions 2024

# 5. Export tax report
python sanitize.py --query-db tax_2024.db --export-tax-report tax_2024.txt

# 6. Upload to NotebookLM and ask for help!
```

**You're ready for tax filing!** 🎉

