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
from src.models.metadata import MetadataGenerator
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
        help="Path to a file or directory containing bank statements to sanitize"
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


def sanitize_single_file(file_path: str, output_dir: str, cli: CLIView, include_metadata: bool = True):
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
    metadata_gen = MetadataGenerator(include_metadata=include_metadata)
    
    base_name, ext = os.path.splitext(file_path)
    sanitized_filename = f"{os.path.basename(base_name)}-sanitized{ext}"
    sanitized_file_path = os.path.join(output_dir, sanitized_filename)
    
    cli.print_file_info(file_path, "Processing")
    
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
        else:
            cli.print(f"  Unsupported file type: {ext}", MessageLevel.WARNING)
            cli.files_skipped += 1
            return
        
        if success:
            cli.print(f"  ✓ Successfully sanitized: {sanitized_filename}", MessageLevel.SUCCESS)
            cli.files_processed += 1
        else:
            cli.print(f"  ✗ Failed to save sanitized file", MessageLevel.ERROR)
            cli.files_failed += 1
            
    except Exception as e:
        cli.print(f"  ✗ Unexpected error: {e}", MessageLevel.ERROR)
        if cli.verbose:
            import traceback
            cli.print(traceback.format_exc(), MessageLevel.DEBUG)
        cli.files_failed += 1


def sanitize_files(input_dir: str, output_dir: str, cli: CLIView, include_metadata: bool = True):
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
            else:
                cli.print(f"  Unsupported file type: {ext}", MessageLevel.WARNING)
                cli.files_skipped += 1
                continue
            
            if success:
                cli.print(f"  ✓ Successfully sanitized: {sanitized_filename}", MessageLevel.SUCCESS)
                cli.files_processed += 1
            else:
                cli.print(f"  ✗ Failed to save sanitized file", MessageLevel.ERROR)
                cli.files_failed += 1
                
        except Exception as e:
            cli.print(f"  ✗ Unexpected error: {e}", MessageLevel.ERROR)
            if cli.verbose:
                import traceback
                cli.print(traceback.format_exc(), MessageLevel.DEBUG)
            cli.files_failed += 1


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Initialize CLI view
    cli = CLIView(verbose=args.verbose, quiet=args.quiet, dry_run=args.dry_run)
    
    # Validate input path (file or directory)
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
    
    # Run sanitization
    try:
        if is_file:
            cli.print_header("Processing File")
            sanitize_single_file(input_path, output_directory, cli, include_metadata=include_metadata)
        else:
            sanitize_files(input_path, output_directory, cli, include_metadata=include_metadata)
        cli.print_summary()
        
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

