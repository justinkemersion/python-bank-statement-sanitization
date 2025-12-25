#!/usr/bin/env python3
"""
Bank Statement Sanitizer - Command Line Interface
Entry point for the bank statement sanitization tool.
"""

import argparse
import sys
import os
from typing import Tuple

# Add src to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.controllers.file_processor import FileProcessor
from src.models.sanitizer import Sanitizer
from src.models.pdf_handler import PDFHandler
from src.models.txt_handler import TXTHandler
from src.models.csv_handler import CSVHandler
from src.models.excel_handler import ExcelHandler
from src.models.metadata import MetadataGenerator
from src.models.database_exporter import DatabaseExporter
from src.models.spending_analytics import SpendingAnalytics
from src.views.cli import CLIView, MessageLevel, Colors


def parse_arguments():
    """Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Sanitize bank statements to remove sensitive information (PII).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ./statements                    # Process all files in directory
  %(prog)s ./statement.pdf                 # Process a single file
  %(prog)s ./statements -o ./sanitized     # Specify output directory
  %(prog)s ./statement.pdf -o ./output     # Process file to specific directory
  %(prog)s ./statements --verbose          # Verbose output
  %(prog)s ./statements --dry-run          # Preview without modifying
  %(prog)s ./statements --quiet            # Minimal output
        """
    )
    
    parser.add_argument(
        "input_path",
        nargs='?',
        help="Path to a file or directory containing bank statements to sanitize (optional if using --query-db)"
    )
    
    parser.add_argument(
        "-o", "--output-dir",
        dest="output_dir",
        help="Output directory for sanitized files (default: same as input directory)",
        default=None
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output with detailed processing information"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually modifying files"
    )
    
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Disable AI-friendly metadata headers in sanitized files (metadata enabled by default)"
    )
    
    parser.add_argument(
        "--export-db",
        dest="export_db",
        help="Export sanitized data to SQLite database for tax analysis (specify database file path)"
    )
    
    parser.add_argument(
        "--force-reimport",
        action="store_true",
        help="Force re-import of files that have already been imported to the database"
    )
    
    parser.add_argument(
        "--export-csv",
        dest="export_csv",
        help="Export database to CSV file for AI analysis (requires --export-db)"
    )
    
    parser.add_argument(
        "--export-report",
        dest="export_report",
        help="Export database to summary report text file for AI analysis (requires --export-db)"
    )
    
    parser.add_argument(
        "--export-json",
        dest="export_json",
        help="Export database to JSON file for programmatic access (requires --export-db)"
    )
    
    parser.add_argument(
        "--date-range",
        dest="date_range",
        help="Filter transactions by date range (format: YYYY-MM-DD:YYYY-MM-DD, e.g., 2024-01-01:2024-12-31)"
    )
    
    # Query mode arguments
    parser.add_argument(
        "--query-db",
        dest="query_db",
        help="Query existing database (specify database file path). Use with --category, --merchant, --min-amount, --max-amount, --recurring"
    )
    
    parser.add_argument(
        "--category",
        dest="query_category",
        help="Filter query results by category name"
    )
    
    parser.add_argument(
        "--merchant",
        dest="query_merchant",
        help="Filter query results by merchant name (partial match)"
    )
    
    parser.add_argument(
        "--min-amount",
        dest="query_min_amount",
        type=float,
        help="Filter query results by minimum transaction amount"
    )
    
    parser.add_argument(
        "--max-amount",
        dest="query_max_amount",
        type=float,
        help="Filter query results by maximum transaction amount"
    )
    
    parser.add_argument(
        "--recurring",
        dest="query_recurring",
        action="store_true",
        help="Show only recurring transactions in query results"
    )
    
    parser.add_argument(
        "--list-recurring",
        dest="list_recurring",
        action="store_true",
        help="List all recurring transactions grouped by merchant (requires --query-db)"
    )
    
    parser.add_argument(
        "--limit",
        dest="query_limit",
        type=int,
        help="Limit number of query results (default: no limit)"
    )
    
    # Spending analytics arguments
    parser.add_argument(
        "--spending-report",
        dest="spending_report",
        help="Generate comprehensive spending analysis report (requires --query-db or --export-db)"
    )
    
    parser.add_argument(
        "--year",
        dest="report_year",
        type=int,
        help="Filter spending report by year (use with --spending-report)"
    )
    
    parser.add_argument(
        "--top-categories",
        dest="top_categories",
        type=int,
        help="Show top N spending categories (requires --query-db)"
    )
    
    parser.add_argument(
        "--top-merchants",
        dest="top_merchants",
        type=int,
        help="Show top N merchants by spending (requires --query-db)"
    )
    
    # Debt payoff calculator arguments
    parser.add_argument(
        "--debt-payoff",
        dest="debt_payoff",
        type=float,
        help="Calculate debt payoff strategy (specify monthly payment amount, requires --query-db)"
    )
    
    parser.add_argument(
        "--payoff-strategy",
        dest="payoff_strategy",
        choices=['snowball', 'avalanche', 'compare'],
        default='compare',
        help="Debt payoff strategy: 'snowball' (smallest first), 'avalanche' (highest APR first), or 'compare' (both)"
    )
    
    parser.add_argument(
        "--show-debts",
        dest="show_debts",
        action="store_true",
        help="Show current debt balances (requires --query-db)"
    )
    
    # Bill tracking arguments
    parser.add_argument(
        "--show-bills",
        dest="show_bills",
        action="store_true",
        help="Show all recurring bills (requires --query-db)"
    )
    
    parser.add_argument(
        "--upcoming-bills",
        dest="upcoming_bills",
        type=int,
        nargs='?',
        const=30,
        help="Show bills due in the next N days (default: 30, requires --query-db)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )
    
    return parser.parse_args()


def validate_input_path(input_path: str, cli: CLIView) -> Tuple[bool, bool, str]:
    """Validate input path (file or directory).
    
    Args:
        input_path: Input file or directory path
        cli: CLI view instance for output
        
    Returns:
        tuple: (is_valid, is_file, resolved_path)
    """
    if not os.path.exists(input_path):
        cli.print(f"Input path '{input_path}' not found.", MessageLevel.ERROR)
        return False, False, input_path
    
    if os.path.isfile(input_path):
        return True, True, os.path.abspath(input_path)
    elif os.path.isdir(input_path):
        return True, False, os.path.abspath(input_path)
    else:
        cli.print(f"Input path '{input_path}' is neither a file nor a directory.", MessageLevel.ERROR)
        return False, False, input_path


def ensure_output_directory(output_dir: str, cli: CLIView) -> bool:
    """Ensure output directory exists.
    
    Args:
        output_dir: Output directory path
        cli: CLI view instance for output
        
    Returns:
        bool: True if directory is valid/created, False otherwise
    """
    if not os.path.exists(output_dir):
        if not cli.dry_run:
            try:
                os.makedirs(output_dir)
                cli.print(f"Created output directory: {output_dir}", MessageLevel.SUCCESS)
            except Exception as e:
                cli.print(f"Failed to create output directory '{output_dir}': {e}", MessageLevel.ERROR)
                return False
        else:
            cli.print(f"Would create output directory: {output_dir}", MessageLevel.INFO)
    
    return True


def sanitize_single_file(file_path: str, output_dir: str, cli: CLIView, include_metadata: bool = True, db_exporter: DatabaseExporter = None, force_reimport: bool = False):
    """Sanitize a single file.
    
    Args:
        file_path: Path to the file to sanitize
        output_dir: Directory to save sanitized file
        cli: CLI view instance for output
        include_metadata: Whether to include AI-friendly metadata headers
    """
    sanitizer = Sanitizer()
    pdf_handler = PDFHandler()
    txt_handler = TXTHandler()
    csv_handler = CSVHandler()
    excel_handler = ExcelHandler()
    metadata_gen = MetadataGenerator(include_metadata=include_metadata)
    
    base_name, ext = os.path.splitext(file_path)
    sanitized_filename = f"{os.path.basename(base_name)}-sanitized{ext}"
    sanitized_file_path = os.path.join(output_dir, sanitized_filename)
    
    cli.print_file_info(file_path, "Processing")
    
    # Variables for database export
    sanitized_text = None
    sanitized_rows = None
    sanitized_df = None
    
    try:
        if ext.lower() == '.pdf':
            if cli.verbose:
                cli.print("  Extracting text from PDF...", MessageLevel.DEBUG)
            text_content = pdf_handler.extract_text(file_path)
            if text_content is None:
                cli.print(f"  Failed to extract text from PDF", MessageLevel.ERROR)
                cli.files_failed += 1
                return
            
            if cli.verbose:
                cli.print(f"  Extracted {len(text_content)} characters", MessageLevel.DEBUG)
                cli.print("  Sanitizing content...", MessageLevel.DEBUG)
            sanitized_text, detected_patterns = sanitizer.sanitize_text(text_content, track_patterns=True)
            
            # Generate metadata
            metadata_header = metadata_gen.generate_header(detected_patterns)
            metadata_footer = metadata_gen.generate_footer()
            
            if cli.verbose:
                cli.print("  Creating sanitized PDF...", MessageLevel.DEBUG)
            success = pdf_handler.create_sanitized_pdf(file_path, sanitized_text, sanitized_file_path,
                                                      metadata_header, metadata_footer)
            
        elif ext.lower() == '.txt':
            if cli.verbose:
                cli.print("  Reading text file...", MessageLevel.DEBUG)
            text_content = txt_handler.read_text(file_path)
            if text_content is None:
                cli.print(f"  Failed to read text file", MessageLevel.ERROR)
                cli.files_failed += 1
                return
            
            if cli.verbose:
                cli.print(f"  Read {len(text_content)} characters", MessageLevel.DEBUG)
                cli.print("  Sanitizing content...", MessageLevel.DEBUG)
            sanitized_text, detected_patterns = sanitizer.sanitize_text(text_content, track_patterns=True)
            
            # Generate metadata
            metadata_header = metadata_gen.generate_header(detected_patterns)
            metadata_footer = metadata_gen.generate_footer()
            
            if cli.verbose:
                cli.print("  Saving sanitized file...", MessageLevel.DEBUG)
            success = txt_handler.save_sanitized_text(sanitized_text, sanitized_file_path, 
                                                     metadata_header, metadata_footer)
            # Store for database export
            sanitized_text = sanitized_text
        
        elif ext.lower() == '.csv':
            if cli.verbose:
                cli.print("  Reading CSV file...", MessageLevel.DEBUG)
            rows = csv_handler.read_csv(file_path)
            if rows is None:
                cli.print(f"  Failed to read CSV file", MessageLevel.ERROR)
                cli.files_failed += 1
                return
            
            if cli.verbose:
                cli.print(f"  Read {len(rows)} rows", MessageLevel.DEBUG)
                cli.print("  Sanitizing content...", MessageLevel.DEBUG)
            sanitized_rows, detected_patterns = csv_handler.sanitize_csv_data(rows, sanitizer)
            
            # Generate metadata
            metadata_header = metadata_gen.generate_header(detected_patterns)
            metadata_footer = metadata_gen.generate_footer()
            
            if cli.verbose:
                cli.print("  Saving sanitized CSV...", MessageLevel.DEBUG)
            success = csv_handler.save_sanitized_csv(sanitized_rows, sanitized_file_path,
                                                    metadata_header, metadata_footer)
            # Store for database export
            sanitized_rows = sanitized_rows
        
        elif ext.lower() in ['.xlsx', '.xls']:
            if cli.verbose:
                cli.print("  Reading Excel file...", MessageLevel.DEBUG)
            df = excel_handler.read_excel(file_path)
            if df is None:
                cli.print(f"  Failed to read Excel file", MessageLevel.ERROR)
                cli.files_failed += 1
                return
            
            if cli.verbose:
                cli.print(f"  Read {len(df)} rows, {len(df.columns)} columns", MessageLevel.DEBUG)
                cli.print("  Sanitizing content...", MessageLevel.DEBUG)
            sanitized_df, detected_patterns = excel_handler.sanitize_excel_data(df, sanitizer)
            
            # Generate metadata
            metadata_header = metadata_gen.generate_header(detected_patterns)
            metadata_footer = metadata_gen.generate_footer()
            
            if cli.verbose:
                cli.print("  Saving sanitized Excel...", MessageLevel.DEBUG)
            success = excel_handler.save_sanitized_excel(sanitized_df, sanitized_file_path,
                                                        metadata_header, metadata_footer)
            # Store for database export
            sanitized_df = sanitized_df
        else:
            cli.print(f"  Unsupported file type: {ext}", MessageLevel.WARNING)
            cli.files_skipped += 1
            return
        
        if success:
            cli.print(f"  ✓ Successfully sanitized: {sanitized_filename}", MessageLevel.SUCCESS)
            cli.files_processed += 1
            
            # Export to database if requested
            if db_exporter:
                try:
                    # Check if file already imported (unless force re-import)
                    if not force_reimport and db_exporter.is_file_imported(file_path):
                        if cli.verbose:
                            cli.print(f"  File already imported to database (use --force-reimport to re-import)", MessageLevel.DEBUG)
                    else:
                        # Delete existing transactions if re-importing
                        if force_reimport and db_exporter.is_file_imported(file_path):
                            deleted = db_exporter.delete_file_transactions(file_path)
                            if cli.verbose:
                                cli.print(f"  Removed {deleted} existing transactions for re-import", MessageLevel.DEBUG)
                        
                        # Try to extract paystub data first (for PDF/TXT files)
                        paystubs = []
                        if ext.lower() in ['.pdf', '.txt']:
                            paystubs = db_exporter.extract_paystub_from_text(sanitized_text, os.path.basename(file_path))
                            if paystubs:
                                inserted_count = 0
                                skipped_count = 0
                                for paystub in paystubs:
                                    inserted = db_exporter.insert_paystub(paystub, skip_duplicates=True)
                                    if inserted:
                                        inserted_count += 1
                                    else:
                                        skipped_count += 1
                                
                                if inserted_count > 0:
                                    if cli.verbose:
                                        cli.print(f"  Extracted {len(paystubs)} paystub(s) - {inserted_count} new, {skipped_count} duplicates", MessageLevel.DEBUG)
                                        for paystub in paystubs[:3]:  # Show first 3
                                            cli.print(f"    Pay Date: {paystub.get('pay_date', 'N/A')}, Net: ${paystub.get('net_pay', 0):.2f}", MessageLevel.DEBUG)
                                        if len(paystubs) > 3:
                                            cli.print(f"    ... and {len(paystubs) - 3} more", MessageLevel.DEBUG)
                                    db_exporter.record_file_import(file_path, 'paystub', inserted_count, f'{len(paystubs)} paystubs extracted')
                                elif skipped_count > 0:
                                    if cli.verbose:
                                        cli.print(f"  All {len(paystubs)} paystub(s) already exist in database", MessageLevel.DEBUG)
                        
                        # Extract balance information (for statements, not paystubs)
                        if not paystubs and ext.lower() in ['.pdf', '.txt']:
                            # Detect account type and bank name first
                            account_type = db_exporter._detect_account_type(sanitized_text, os.path.basename(file_path))
                            bank_name = db_exporter._detect_bank_name(sanitized_text, os.path.basename(file_path))
                            
                            # Extract balance
                            balance = db_exporter.extract_balance_from_text(sanitized_text, os.path.basename(file_path), 
                                                                           account_type, bank_name)
                            if balance:
                                inserted = db_exporter.insert_balance(balance, skip_duplicates=True)
                                if inserted:
                                    if cli.verbose:
                                        balance_info = f"Balance: ${balance.get('balance', 0):,.2f}"
                                        if balance.get('credit_limit'):
                                            balance_info += f", Limit: ${balance.get('credit_limit', 0):,.2f}"
                                        if balance.get('minimum_payment'):
                                            balance_info += f", Min Payment: ${balance.get('minimum_payment', 0):,.2f}"
                                        cli.print(f"  Extracted account balance: {balance_info}", MessageLevel.DEBUG)
                        
                        # Extract transactions (skip if this was a paystub)
                        if not paystubs:
                            if ext.lower() == '.csv':
                                transactions = db_exporter.extract_transactions_from_csv(sanitized_rows, os.path.basename(file_path))
                            elif ext.lower() in ['.xlsx', '.xls']:
                                transactions = db_exporter.extract_transactions_from_dataframe(sanitized_df, os.path.basename(file_path))
                            elif ext.lower() in ['.pdf', '.txt']:
                                transactions = db_exporter.extract_transactions_from_text(sanitized_text, os.path.basename(file_path))
                            else:
                                transactions = []
                            
                            if transactions:
                                result = db_exporter.insert_transactions(transactions, skip_duplicates=True)
                                db_exporter.record_file_import(file_path, ext.lower()[1:], result['inserted'])
                                if cli.verbose:
                                    cli.print(f"  Exported {result['inserted']} transactions to database", MessageLevel.DEBUG)
                                    if result['skipped'] > 0:
                                        cli.print(f"  Skipped {result['skipped']} duplicate transactions", MessageLevel.DEBUG)
                except Exception as e:
                    if cli.verbose:
                        cli.print(f"  Warning: Failed to export to database: {e}", MessageLevel.WARNING)
        else:
            cli.print(f"  ✗ Failed to save sanitized file", MessageLevel.ERROR)
            cli.files_failed += 1
            
    except Exception as e:
        cli.print(f"  ✗ Unexpected error: {e}", MessageLevel.ERROR)
        if cli.verbose:
            import traceback
            cli.print(traceback.format_exc(), MessageLevel.DEBUG)
        cli.files_failed += 1


def sanitize_files(input_dir: str, output_dir: str, cli: CLIView, include_metadata: bool = True, db_exporter: DatabaseExporter = None, force_reimport: bool = False):
    """Main sanitization workflow.
    
    Args:
        input_dir: Directory containing files to sanitize
        output_dir: Directory to save sanitized files
        cli: CLI view instance for output
        include_metadata: Whether to include AI-friendly metadata headers
    """
    # Initialize components
    file_processor = FileProcessor(input_dir, output_dir)
    sanitizer = Sanitizer()
    pdf_handler = PDFHandler()
    txt_handler = TXTHandler()
    csv_handler = CSVHandler()
    excel_handler = ExcelHandler()
    metadata_gen = MetadataGenerator(include_metadata=include_metadata)
    
    # Find files to process
    if cli.verbose:
        cli.print("Scanning directory for files...", MessageLevel.INFO)
    
    files_to_sanitize = file_processor.find_files_to_process()
    
    if not files_to_sanitize:
        cli.print("No new files to sanitize found.", MessageLevel.WARNING)
        return
    
    total_files = len(files_to_sanitize)
    cli.print(f"Found {total_files} file(s) to process.", MessageLevel.INFO)
    
    if cli.dry_run:
        cli.print("\nDry run mode - no files will be modified.", MessageLevel.WARNING)
        for file_path in files_to_sanitize:
            filename = os.path.basename(file_path)
            cli.print(f"Would process: {filename}", MessageLevel.INFO)
        return
    
    # Process each file
    cli.print_header("Processing Files")
    
    for idx, file_path in enumerate(files_to_sanitize, 1):
        cli.print_progress(idx, total_files, os.path.basename(file_path))
        cli.print_file_info(file_path, "Processing")
        
        base_name, ext = os.path.splitext(file_path)
        sanitized_filename = f"{os.path.basename(base_name)}-sanitized{ext}"
        sanitized_file_path = os.path.join(output_dir, sanitized_filename)
        
        success = False
        
        # Variables for database export
        sanitized_text = None
        sanitized_rows = None
        sanitized_df = None
        
        try:
            if ext.lower() == '.pdf':
                if cli.verbose:
                    cli.print("  Extracting text from PDF...", MessageLevel.DEBUG)
                text_content = pdf_handler.extract_text(file_path)
                if text_content is None:
                    cli.print(f"  Failed to extract text from PDF", MessageLevel.ERROR)
                    cli.files_failed += 1
                    continue
                
                if cli.verbose:
                    cli.print(f"  Extracted {len(text_content)} characters", MessageLevel.DEBUG)
                    cli.print("  Sanitizing content...", MessageLevel.DEBUG)
                sanitized_text, detected_patterns = sanitizer.sanitize_text(text_content, track_patterns=True)
                
                # Generate metadata
                metadata_header = metadata_gen.generate_header(detected_patterns)
                metadata_footer = metadata_gen.generate_footer()
                
                if cli.verbose:
                    cli.print("  Creating sanitized PDF...", MessageLevel.DEBUG)
                success = pdf_handler.create_sanitized_pdf(file_path, sanitized_text, sanitized_file_path,
                                                          metadata_header, metadata_footer)
                # Store for database export
                sanitized_text = sanitized_text
                
            elif ext.lower() == '.txt':
                if cli.verbose:
                    cli.print("  Reading text file...", MessageLevel.DEBUG)
                text_content = txt_handler.read_text(file_path)
                if text_content is None:
                    cli.print(f"  Failed to read text file", MessageLevel.ERROR)
                    cli.files_failed += 1
                    continue
                
                if cli.verbose:
                    cli.print(f"  Read {len(text_content)} characters", MessageLevel.DEBUG)
                    cli.print("  Sanitizing content...", MessageLevel.DEBUG)
                sanitized_text, detected_patterns = sanitizer.sanitize_text(text_content, track_patterns=True)
                
                # Generate metadata
                metadata_header = metadata_gen.generate_header(detected_patterns)
                metadata_footer = metadata_gen.generate_footer()
                
                if cli.verbose:
                    cli.print("  Saving sanitized file...", MessageLevel.DEBUG)
                success = txt_handler.save_sanitized_text(sanitized_text, sanitized_file_path, 
                                                         metadata_header, metadata_footer)
                # Store for database export
                sanitized_text = sanitized_text
            
            elif ext.lower() == '.csv':
                if cli.verbose:
                    cli.print("  Reading CSV file...", MessageLevel.DEBUG)
                rows = csv_handler.read_csv(file_path)
                if rows is None:
                    cli.print(f"  Failed to read CSV file", MessageLevel.ERROR)
                    cli.files_failed += 1
                    continue
                
                if cli.verbose:
                    cli.print(f"  Read {len(rows)} rows", MessageLevel.DEBUG)
                    cli.print("  Sanitizing content...", MessageLevel.DEBUG)
                sanitized_rows, detected_patterns = csv_handler.sanitize_csv_data(rows, sanitizer)
                
                # Generate metadata
                metadata_header = metadata_gen.generate_header(detected_patterns)
                metadata_footer = metadata_gen.generate_footer()
                
                if cli.verbose:
                    cli.print("  Saving sanitized CSV...", MessageLevel.DEBUG)
                success = csv_handler.save_sanitized_csv(sanitized_rows, sanitized_file_path,
                                                        metadata_header, metadata_footer)
                # Store for database export
                sanitized_rows = sanitized_rows
            
            elif ext.lower() in ['.xlsx', '.xls']:
                if cli.verbose:
                    cli.print("  Reading Excel file...", MessageLevel.DEBUG)
                df = excel_handler.read_excel(file_path)
                if df is None:
                    cli.print(f"  Failed to read Excel file", MessageLevel.ERROR)
                    cli.files_failed += 1
                    continue
                
                if cli.verbose:
                    cli.print(f"  Read {len(df)} rows, {len(df.columns)} columns", MessageLevel.DEBUG)
                    cli.print("  Sanitizing content...", MessageLevel.DEBUG)
                sanitized_df, detected_patterns = excel_handler.sanitize_excel_data(df, sanitizer)
                
                # Generate metadata
                metadata_header = metadata_gen.generate_header(detected_patterns)
                metadata_footer = metadata_gen.generate_footer()
                
                if cli.verbose:
                    cli.print("  Saving sanitized Excel...", MessageLevel.DEBUG)
                success = excel_handler.save_sanitized_excel(sanitized_df, sanitized_file_path,
                                                            metadata_header, metadata_footer)
                # Store for database export
                sanitized_df = sanitized_df
            else:
                cli.print(f"  Unsupported file type: {ext}", MessageLevel.WARNING)
                cli.files_skipped += 1
                continue
            
            if success:
                cli.print(f"  ✓ Successfully sanitized: {sanitized_filename}", MessageLevel.SUCCESS)
                cli.files_processed += 1
                
                # Export to database if requested
                if db_exporter:
                    try:
                        # Check if file already imported (unless force re-import)
                        if not force_reimport and db_exporter.is_file_imported(file_path):
                            if cli.verbose:
                                cli.print(f"  File already imported to database (use --force-reimport to re-import)", MessageLevel.DEBUG)
                        else:
                            # Delete existing transactions if re-importing
                            if force_reimport and db_exporter.is_file_imported(file_path):
                                deleted = db_exporter.delete_file_transactions(file_path)
                                if cli.verbose:
                                    cli.print(f"  Removed {deleted} existing transactions for re-import", MessageLevel.DEBUG)
                            
                            # Try to extract paystub data first (for PDF/TXT files)
                            paystubs = []
                            if ext.lower() in ['.pdf', '.txt']:
                                paystubs = db_exporter.extract_paystub_from_text(sanitized_text, os.path.basename(file_path))
                                if paystubs:
                                    inserted_count = 0
                                    skipped_count = 0
                                    for paystub in paystubs:
                                        inserted = db_exporter.insert_paystub(paystub, skip_duplicates=True)
                                        if inserted:
                                            inserted_count += 1
                                        else:
                                            skipped_count += 1
                                    
                                    if inserted_count > 0:
                                        if cli.verbose:
                                            cli.print(f"  Extracted {len(paystubs)} paystub(s) - {inserted_count} new, {skipped_count} duplicates", MessageLevel.DEBUG)
                                            for paystub in paystubs[:3]:  # Show first 3
                                                cli.print(f"    Pay Date: {paystub.get('pay_date', 'N/A')}, Net: ${paystub.get('net_pay', 0):.2f}", MessageLevel.DEBUG)
                                            if len(paystubs) > 3:
                                                cli.print(f"    ... and {len(paystubs) - 3} more", MessageLevel.DEBUG)
                                        db_exporter.record_file_import(file_path, 'paystub', inserted_count, f'{len(paystubs)} paystubs extracted')
                                    elif skipped_count > 0:
                                        if cli.verbose:
                                            cli.print(f"  All {len(paystubs)} paystub(s) already exist in database", MessageLevel.DEBUG)
                            
                            # Extract balance information (for statements, not paystubs)
                            if not paystubs and ext.lower() in ['.pdf', '.txt']:
                                # Detect account type and bank name first
                                account_type = db_exporter._detect_account_type(sanitized_text, os.path.basename(file_path))
                                bank_name = db_exporter._detect_bank_name(sanitized_text, os.path.basename(file_path))
                                
                                # Extract balance
                                balance = db_exporter.extract_balance_from_text(sanitized_text, os.path.basename(file_path), 
                                                                               account_type, bank_name)
                                if balance:
                                    inserted = db_exporter.insert_balance(balance, skip_duplicates=True)
                                    if inserted:
                                        if cli.verbose:
                                            balance_info = f"Balance: ${balance.get('balance', 0):,.2f}"
                                            if balance.get('credit_limit'):
                                                balance_info += f", Limit: ${balance.get('credit_limit', 0):,.2f}"
                                            if balance.get('minimum_payment'):
                                                balance_info += f", Min Payment: ${balance.get('minimum_payment', 0):,.2f}"
                                            cli.print(f"  Extracted account balance: {balance_info}", MessageLevel.DEBUG)
                            
                            # Extract transactions (skip if this was a paystub)
                            if not paystubs:
                                if ext.lower() == '.csv':
                                    transactions = db_exporter.extract_transactions_from_csv(sanitized_rows, os.path.basename(file_path))
                                elif ext.lower() in ['.xlsx', '.xls']:
                                    transactions = db_exporter.extract_transactions_from_dataframe(sanitized_df, os.path.basename(file_path))
                                elif ext.lower() in ['.pdf', '.txt']:
                                    transactions = db_exporter.extract_transactions_from_text(sanitized_text, os.path.basename(file_path))
                                else:
                                    transactions = []
                                
                                if transactions:
                                    result = db_exporter.insert_transactions(transactions, skip_duplicates=True)
                                    db_exporter.record_file_import(file_path, ext.lower()[1:], result['inserted'])
                                    if cli.verbose:
                                        cli.print(f"  Exported {result['inserted']} transactions to database", MessageLevel.DEBUG)
                                        if result['skipped'] > 0:
                                            cli.print(f"  Skipped {result['skipped']} duplicate transactions", MessageLevel.DEBUG)
                    except Exception as e:
                        if cli.verbose:
                            cli.print(f"  Warning: Failed to export to database: {e}", MessageLevel.WARNING)
            else:
                cli.print(f"  ✗ Failed to save sanitized file", MessageLevel.ERROR)
                cli.files_failed += 1
                
        except Exception as e:
            cli.print(f"  ✗ Unexpected error: {e}", MessageLevel.ERROR)
            if cli.verbose:
                import traceback
                cli.print(traceback.format_exc(), MessageLevel.DEBUG)
            cli.files_failed += 1


def parse_date_range(date_range_str: str) -> Tuple[str, str]:
    """Parse date range string into tuple.
    
    Args:
        date_range_str: Date range in format "YYYY-MM-DD:YYYY-MM-DD"
        
    Returns:
        Tuple of (start_date, end_date)
    """
    try:
        start_date, end_date = date_range_str.split(':')
        return start_date.strip(), end_date.strip()
    except ValueError:
        raise ValueError("Date range must be in format YYYY-MM-DD:YYYY-MM-DD")


def handle_query_mode(args, cli: CLIView):
    """Handle database query mode.
    
    Args:
        args: Parsed command-line arguments
        cli: CLI view instance
    """
    if not args.query_db:
        cli.print("Error: --query-db is required for query mode", MessageLevel.ERROR)
        sys.exit(1)
    
    db_path = os.path.abspath(args.query_db)
    if not os.path.exists(db_path):
        cli.print(f"Error: Database file not found: {db_path}", MessageLevel.ERROR)
        sys.exit(1)
    
    db_exporter = DatabaseExporter(db_path)
    if not db_exporter.connect():
        cli.print("Error: Failed to connect to database", MessageLevel.ERROR)
        sys.exit(1)
    
    # Parse date range if provided
    date_range = None
    if args.date_range:
        try:
            date_range = parse_date_range(args.date_range)
        except ValueError as e:
            cli.print(f"Error: {e}", MessageLevel.ERROR)
            sys.exit(1)
    
    # Handle show debts
    if args.show_debts:
        cli.print_header("Current Debt Balances")
        debts = db_exporter.get_current_debts()
        
        if not debts:
            cli.print("No debt found in database.", MessageLevel.INFO)
        else:
            total_debt = sum(d.get('balance', 0) for d in debts)
            cli.print(f"Total Debt: ${total_debt:,.2f}", MessageLevel.INFO)
            cli.print("", MessageLevel.INFO)
            
            for i, debt in enumerate(debts, 1):
                cli.print(f"{i}. {debt.get('bank_name', 'Unknown'):<25} ${debt.get('balance', 0):>12,.2f}", MessageLevel.INFO)
                if debt.get('apr'):
                    cli.print(f"   APR: {debt.get('apr', 0):.2f}%", MessageLevel.DEBUG)
                if debt.get('minimum_payment'):
                    cli.print(f"   Min Payment: ${debt.get('minimum_payment', 0):,.2f}", MessageLevel.DEBUG)
                if debt.get('payment_due_date'):
                    cli.print(f"   Due Date: {debt.get('payment_due_date', 'N/A')}", MessageLevel.DEBUG)
        
        db_exporter.close()
        return
    
    # Handle debt payoff calculation
    if args.debt_payoff:
        cli.print_header("Debt Payoff Strategy")
        result = db_exporter.calculate_debt_payoff(args.debt_payoff, args.payoff_strategy)
        
        if 'error' in result:
            cli.print(result['error'], MessageLevel.ERROR)
            db_exporter.close()
            return
        
        if args.payoff_strategy == 'compare':
            # Show comparison
            snowball = result.get('snowball', {})
            avalanche = result.get('avalanche', {})
            recommendation = result.get('recommendation', '')
            
            cli.print("", MessageLevel.INFO)
            cli.print("SNOWBALL STRATEGY (Pay smallest balance first):", MessageLevel.INFO)
            cli.print(f"  Total Debt: ${snowball.get('total_debt', 0):,.2f}", MessageLevel.INFO)
            cli.print(f"  Total Interest: ${snowball.get('total_interest', 0):,.2f}", MessageLevel.INFO)
            cli.print(f"  Months to Payoff: {snowball.get('months_to_payoff', 0)}", MessageLevel.INFO)
            cli.print(f"  Payoff Date: {snowball.get('payoff_date', 'N/A')}", MessageLevel.INFO)
            cli.print(f"  Total Paid: ${snowball.get('total_paid', 0):,.2f}", MessageLevel.INFO)
            
            cli.print("", MessageLevel.INFO)
            cli.print("AVALANCHE STRATEGY (Pay highest APR first):", MessageLevel.INFO)
            cli.print(f"  Total Debt: ${avalanche.get('total_debt', 0):,.2f}", MessageLevel.INFO)
            cli.print(f"  Total Interest: ${avalanche.get('total_interest', 0):,.2f}", MessageLevel.INFO)
            cli.print(f"  Months to Payoff: {avalanche.get('months_to_payoff', 0)}", MessageLevel.INFO)
            cli.print(f"  Payoff Date: {avalanche.get('payoff_date', 'N/A')}", MessageLevel.INFO)
            cli.print(f"  Total Paid: ${avalanche.get('total_paid', 0):,.2f}", MessageLevel.INFO)
            
            cli.print("", MessageLevel.INFO)
            cli.print(f"RECOMMENDATION: {recommendation}", MessageLevel.SUCCESS)
            
            # Show payoff plan for recommended strategy
            if avalanche.get('total_interest', 0) < snowball.get('total_interest', 0):
                plan = avalanche.get('payoff_plan', [])
            else:
                plan = snowball.get('payoff_plan', [])
        else:
            # Show single strategy
            strategy_name = result.get('strategy', '').upper()
            cli.print(f"{strategy_name} STRATEGY:", MessageLevel.INFO)
            cli.print(f"  Total Debt: ${result.get('total_debt', 0):,.2f}", MessageLevel.INFO)
            cli.print(f"  Total Interest: ${result.get('total_interest', 0):,.2f}", MessageLevel.INFO)
            cli.print(f"  Months to Payoff: {result.get('months_to_payoff', 0)}", MessageLevel.INFO)
            cli.print(f"  Payoff Date: {result.get('payoff_date', 'N/A')}", MessageLevel.INFO)
            cli.print(f"  Total Paid: ${result.get('total_paid', 0):,.2f}", MessageLevel.INFO)
            
            plan = result.get('payoff_plan', [])
        
        if plan:
            cli.print("", MessageLevel.INFO)
            cli.print("PAYOFF PLAN:", MessageLevel.INFO)
            for i, debt_plan in enumerate(plan, 1):
                cli.print(f"{i}. {debt_plan.get('bank_name', 'Unknown'):<25} "
                         f"${debt_plan.get('starting_balance', 0):>12,.2f} → "
                         f"{debt_plan.get('months_to_payoff', 0)} months, "
                         f"${debt_plan.get('total_interest', 0):,.2f} interest", MessageLevel.INFO)
        
        db_exporter.close()
        return
    
    # Handle show bills
    if args.show_bills:
        cli.print_header("Recurring Bills")
        bills = db_exporter.get_all_bills()
        
        if not bills:
            cli.print("No recurring bills found. Run transaction import to detect bills.", MessageLevel.INFO)
        else:
            total_monthly = sum(b.get('amount', 0) for b in bills)
            cli.print(f"Total Monthly Bills: ${total_monthly:,.2f}", MessageLevel.INFO)
            cli.print("", MessageLevel.INFO)
            
            for i, bill in enumerate(bills, 1):
                cli.print(f"{i}. {bill.get('merchant_name', 'Unknown'):<30} ${bill.get('amount', 0):>10,.2f}/mo", MessageLevel.INFO)
                if bill.get('category'):
                    cli.print(f"   Category: {bill.get('category')}", MessageLevel.DEBUG)
                if bill.get('last_paid_date'):
                    cli.print(f"   Last Paid: {bill.get('last_paid_date')}", MessageLevel.DEBUG)
                if bill.get('payment_count'):
                    cli.print(f"   Payments: {bill.get('payment_count')}", MessageLevel.DEBUG)
        
        db_exporter.close()
        return
    
    # Handle upcoming bills
    if args.upcoming_bills is not None:
        days = args.upcoming_bills
        cli.print_header(f"Bills Due in Next {days} Days")
        bills = db_exporter.get_upcoming_bills(days_ahead=days)
        
        if not bills:
            cli.print(f"No bills due in the next {days} days.", MessageLevel.INFO)
        else:
            total_due = sum(b.get('amount', 0) for b in bills)
            cli.print(f"Total Due: ${total_due:,.2f}", MessageLevel.INFO)
            cli.print("", MessageLevel.INFO)
            
            for i, bill in enumerate(bills, 1):
                due_date = bill.get('next_due_date') or bill.get('due_date') or 'Unknown'
                cli.print(f"{i}. {bill.get('merchant_name', 'Unknown'):<30} "
                         f"${bill.get('amount', 0):>10,.2f}  Due: {due_date}", MessageLevel.INFO)
        
        db_exporter.close()
        return
    
    # Handle list recurring transactions
    if args.list_recurring:
        cli.print_header("Recurring Transactions")
        recurring = db_exporter.get_recurring_transactions()
        
        if not recurring:
            cli.print("No recurring transactions found.", MessageLevel.INFO)
        else:
            for item in recurring:
                cli.print(f"\n{item['merchant_name']}", MessageLevel.INFO)
                cli.print(f"  Transactions: {item['transaction_count']}", MessageLevel.DEBUG)
                cli.print(f"  Average Amount: ${item['average_amount']:,.2f}", MessageLevel.DEBUG)
                cli.print(f"  Total Amount: ${item['total_amount']:,.2f}", MessageLevel.DEBUG)
                cli.print(f"  First: {item['first_transaction']} | Last: {item['last_transaction']}", MessageLevel.DEBUG)
        
        db_exporter.close()
        return
    
    # Handle spending analytics
    if args.spending_report or args.top_categories or args.top_merchants:
        analytics = SpendingAnalytics(db_exporter.conn)
        
        if args.spending_report:
            cli.print_header("Generating Spending Report")
            report_path = os.path.abspath(args.spending_report)
            if analytics.generate_spending_report(report_path, year=args.report_year):
                cli.print(f"\n✓ Spending report generated: {report_path}", MessageLevel.SUCCESS)
                cli.print("  Comprehensive spending analysis with monthly trends and category breakdowns.", MessageLevel.INFO)
            else:
                cli.print(f"✗ Failed to generate spending report", MessageLevel.ERROR)
        
        if args.top_categories:
            cli.print_header(f"Top {args.top_categories} Spending Categories")
            categories = analytics.get_category_breakdown()
            for i, cat in enumerate(categories[:args.top_categories], 1):
                cli.print(f"{i}. {cat['category']:<25} ${abs(cat['total_spending']):>12,.2f} "
                         f"({cat['percentage']:.1f}%) - {cat['transaction_count']} transactions", MessageLevel.INFO)
        
        if args.top_merchants:
            cli.print_header(f"Top {args.top_merchants} Merchants by Spending")
            merchants = analytics.get_top_merchants(limit=args.top_merchants)
            for i, merch in enumerate(merchants, 1):
                cli.print(f"{i}. {merch['merchant']:<30} ${abs(merch['total_spending']):>12,.2f} "
                         f"- {merch['transaction_count']} transactions", MessageLevel.INFO)
        
        db_exporter.close()
        return
    
    # Query transactions
    cli.print_header("Query Results")
    
    transactions = db_exporter.query_transactions(
        category=args.query_category,
        merchant=args.query_merchant,
        min_amount=args.query_min_amount,
        max_amount=args.query_max_amount,
        date_range=date_range,
        is_recurring=args.query_recurring if args.query_recurring else None,
        limit=args.query_limit
    )
    
    if not transactions:
        cli.print("No transactions found matching the criteria.", MessageLevel.INFO)
    else:
        cli.print(f"Found {len(transactions)} transaction(s):\n", MessageLevel.INFO)
        
        for trans in transactions:
            amount_str = f"${trans['amount']:,.2f}" if trans['amount'] else "N/A"
            merchant_str = f" | {trans['merchant_name']}" if trans['merchant_name'] else ""
            category_str = f" | {trans['category']}" if trans['category'] else ""
            recurring_str = " [RECURRING]" if trans['is_recurring'] else ""
            
            cli.print(f"{trans['transaction_date']} | {amount_str}{merchant_str}{category_str}{recurring_str}", MessageLevel.INFO)
            if trans['description']:
                cli.print(f"  {trans['description'][:80]}", MessageLevel.DEBUG)
    
    db_exporter.close()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Initialize CLI view
    cli = CLIView(verbose=args.verbose, quiet=args.quiet, dry_run=args.dry_run)
    
    # Handle query mode (if --query-db is specified)
    if args.query_db or args.list_recurring or args.spending_report or args.top_categories or args.top_merchants or args.debt_payoff or args.show_debts or args.show_bills or args.upcoming_bills:
        handle_query_mode(args, cli)
        sys.exit(0)
    
    # Validate input path (file or directory) - required for sanitization mode
    if not args.input_path:
        cli.print("Error: input_path is required for sanitization mode", MessageLevel.ERROR)
        cli.print("  Use --query-db for query mode, or provide input_path for sanitization", MessageLevel.INFO)
        sys.exit(1)
    
    is_valid, is_file, input_path = validate_input_path(args.input_path, cli)
    if not is_valid:
        sys.exit(1)
    
    # Determine output directory
    if is_file:
        # For single file, output to specified directory or same directory as file
        if args.output_dir:
            output_directory = os.path.abspath(args.output_dir)
        else:
            output_directory = os.path.dirname(input_path)
    else:
        # For directory, output to specified directory or same as input
        output_directory = os.path.abspath(args.output_dir) if args.output_dir else input_path
    
    # Ensure output directory exists
    if not ensure_output_directory(output_directory, cli):
        sys.exit(1)
    
    # Print configuration
    include_metadata = not args.no_metadata
    if not cli.quiet:
        cli.print_banner()
        print()
        # Configuration table
        input_label = "Input File" if is_file else "Input Directory"
        config_items = [
            (input_label, input_path),
            ("Output Directory", output_directory),
        ]
        
        if include_metadata:
            config_items.append(("AI Metadata", "Enabled (AI tool compatible)"))
        else:
            config_items.append(("AI Metadata", "Disabled"))
            
        if cli.verbose:
            config_items.append(("Verbose Mode", "Enabled"))
        if cli.dry_run:
            config_items.append(("Dry Run Mode", "Enabled"))
        
        # Print configuration in a clean format
        max_label_len = max(len(label) for label, _ in config_items)
        for label, value in config_items:
            label_text = cli._colorize(f"{label:.<{max_label_len}}", Colors.DIM)
            value_text = cli._colorize(value, Colors.BRIGHT_CYAN)
            print(f"  {label_text} {value_text}")
        print()
    
    # Initialize database exporter if requested
    db_exporter = None
    if args.export_db:
        db_path = os.path.abspath(args.export_db)
        db_exporter = DatabaseExporter(db_path)
        if db_exporter.connect():
            db_exporter.create_schema()
            cli.print(f"Database export enabled: {db_path}", MessageLevel.INFO)
        else:
            cli.print(f"Failed to initialize database. Continuing without database export.", MessageLevel.WARNING)
            db_exporter = None
    
    # Run sanitization
    try:
        if is_file:
            cli.print_header("Processing File")
            sanitize_single_file(input_path, output_directory, cli, include_metadata=include_metadata, db_exporter=db_exporter, force_reimport=args.force_reimport)
        else:
            sanitize_files(input_path, output_directory, cli, include_metadata=include_metadata, db_exporter=db_exporter, force_reimport=args.force_reimport)
        cli.print_summary()
        
        # Show database statistics if export was used
        if db_exporter:
            stats = db_exporter.get_statistics()
            cli.print_header("Database Statistics")
            cli.print(f"Total Transactions: {stats['total_transactions']}", MessageLevel.INFO)
            cli.print(f"Files Imported: {stats['files_imported']}", MessageLevel.INFO)
            if stats['date_range']['min']:
                cli.print(f"Date Range: {stats['date_range']['min']} to {stats['date_range']['max']}", MessageLevel.INFO)
            if stats['total_amount']:
                cli.print(f"Total Amount: ${stats['total_amount']:,.2f}", MessageLevel.INFO)
            
            # Paystub statistics
            if stats['paystubs']['total_paystubs'] > 0:
                cli.print("", MessageLevel.INFO)  # Blank line
                cli.print_header("Income Statistics")
                cli.print(f"Total Paystubs: {stats['paystubs']['total_paystubs']}", MessageLevel.INFO)
                cli.print(f"Total Gross Income: ${stats['paystubs']['total_gross']:,.2f}", MessageLevel.INFO)
                cli.print(f"Total Net Income: ${stats['paystubs']['total_net']:,.2f}", MessageLevel.INFO)
                cli.print(f"Average Net Pay: ${stats['paystubs']['average_net']:,.2f}", MessageLevel.INFO)
                if stats['paystubs']['first_pay_date']:
                    cli.print(f"Pay Period: {stats['paystubs']['first_pay_date']} to {stats['paystubs']['last_pay_date']}", MessageLevel.INFO)
                if stats['paystubs']['employers']:
                    cli.print(f"Employers: {', '.join([e['name'] for e in stats['paystubs']['employers']])}", MessageLevel.INFO)
            
            # Account type statistics
            if stats['accounts']['total_accounts'] > 0:
                cli.print("", MessageLevel.INFO)  # Blank line
                cli.print_header("Account Type Breakdown")
                for account in stats['accounts']['accounts']:
                    cli.print(f"{account['account_type']:<15} {account['transaction_count']:>6} transactions, "
                             f"${account['total_amount']:>12,.2f} total", MessageLevel.INFO)
            
            # Bank/issuer statistics
            if stats['banks']['total_banks'] > 0:
                cli.print("", MessageLevel.INFO)  # Blank line
                cli.print_header("Bank/Issuer Breakdown")
                for bank in stats['banks']['banks']:
                    cli.print(f"{bank['bank_name']:<25} {bank['account_type']:<12} "
                             f"{bank['transaction_count']:>6} transactions, ${bank['total_amount']:>12,.2f} total", MessageLevel.INFO)
            
            # Parse date range if provided
            date_range = None
            if args.date_range:
                try:
                    date_range = parse_date_range(args.date_range)
                    cli.print(f"Date range filter: {date_range[0]} to {date_range[1]}", MessageLevel.INFO)
                except ValueError as e:
                    cli.print(f"Warning: Invalid date range format: {e}", MessageLevel.WARNING)
            
            # Export to CSV if requested
            if args.export_csv:
                csv_path = os.path.abspath(args.export_csv)
                if db_exporter.export_to_csv(csv_path, date_range=date_range):
                    cli.print(f"\n✓ Exported transactions to CSV: {csv_path}", MessageLevel.SUCCESS)
                    cli.print("  This file is ready to upload to NotebookLM for analysis.", MessageLevel.INFO)
                else:
                    cli.print(f"✗ Failed to export CSV", MessageLevel.ERROR)
            
            # Export summary report if requested
            if args.export_report:
                report_path = os.path.abspath(args.export_report)
                if db_exporter.export_summary_report(report_path):
                    cli.print(f"\n✓ Exported summary report: {report_path}", MessageLevel.SUCCESS)
                    cli.print("  This report is ready to upload to NotebookLM for analysis.", MessageLevel.INFO)
                else:
                    cli.print(f"✗ Failed to export report", MessageLevel.ERROR)
            
            # Export to JSON if requested
            if args.export_json:
                json_path = os.path.abspath(args.export_json)
                if db_exporter.export_to_json(json_path, date_range=date_range):
                    cli.print(f"\n✓ Exported transactions to JSON: {json_path}", MessageLevel.SUCCESS)
                    cli.print("  This file is ready for programmatic access.", MessageLevel.INFO)
                else:
                    cli.print(f"✗ Failed to export JSON", MessageLevel.ERROR)
            
            # Generate spending report if requested
            if args.spending_report:
                analytics = SpendingAnalytics(db_exporter.conn)
                report_path = os.path.abspath(args.spending_report)
                if analytics.generate_spending_report(report_path, year=args.report_year):
                    cli.print(f"\n✓ Spending report generated: {report_path}", MessageLevel.SUCCESS)
                    cli.print("  Comprehensive spending analysis with monthly trends and category breakdowns.", MessageLevel.INFO)
                else:
                    cli.print(f"✗ Failed to generate spending report", MessageLevel.ERROR)
            
            db_exporter.close()
        
        # Exit with appropriate code
        if cli.files_failed > 0:
            sys.exit(1)
        elif cli.files_processed == 0 and cli.files_skipped == 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        cli.print("\n\nOperation cancelled by user.", MessageLevel.WARNING)
        sys.exit(130)
    except Exception as e:
        cli.print(f"\nUnexpected error: {e}", MessageLevel.ERROR)
        if cli.verbose:
            import traceback
            cli.print(traceback.format_exc(), MessageLevel.DEBUG)
        sys.exit(1)


if __name__ == "__main__":
    main()

