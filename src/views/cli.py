"""
CLI View Module
Handles all command-line interface presentation and user interaction.
"""

import sys
import os
from typing import List, Optional
from enum import Enum


class MessageLevel(Enum):
    """Message severity levels for CLI output."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class CLIView:
    """Command-line interface view for the bank statement sanitizer."""
    
    def __init__(self, verbose: bool = False, quiet: bool = False, dry_run: bool = False):
        """Initialize the CLI view.
        
        Args:
            verbose: Enable verbose output
            quiet: Suppress non-error output
            dry_run: Enable dry-run mode (don't actually modify files)
        """
        self.verbose = verbose
        self.quiet = quiet
        self.dry_run = dry_run
        self.files_processed = 0
        self.files_skipped = 0
        self.files_failed = 0
        
    def print(self, message: str, level: MessageLevel = MessageLevel.INFO, end: str = "\n"):
        """Print a message with appropriate formatting.
        
        Args:
            message: The message to print
            level: The message severity level
            end: String to append after message (default: newline)
        """
        if self.quiet and level not in [MessageLevel.ERROR]:
            return
            
        if self.dry_run and level == MessageLevel.INFO:
            message = f"[DRY RUN] {message}"
            
        colors = {
            MessageLevel.INFO: "",
            MessageLevel.SUCCESS: "\033[92m",  # Green
            MessageLevel.WARNING: "\033[93m",  # Yellow
            MessageLevel.ERROR: "\033[91m",    # Red
            MessageLevel.DEBUG: "\033[94m",     # Blue
        }
        reset = "\033[0m"
        
        prefix = {
            MessageLevel.SUCCESS: "✓ ",
            MessageLevel.WARNING: "⚠ ",
            MessageLevel.ERROR: "✗ ",
            MessageLevel.DEBUG: "🔍 ",
        }.get(level, "")
        
        color = colors.get(level, "")
        formatted_message = f"{color}{prefix}{message}{reset}" if color else f"{prefix}{message}"
        
        print(formatted_message, end=end, file=sys.stdout if level != MessageLevel.ERROR else sys.stderr)
        
    def print_header(self, title: str):
        """Print a section header.
        
        Args:
            title: The header text
        """
        if not self.quiet:
            print(f"\n{'='*60}")
            print(f"  {title}")
            print(f"{'='*60}\n")
    
    def print_file_info(self, file_path: str, action: str = "Processing"):
        """Print file processing information.
        
        Args:
            file_path: Path to the file
            action: Action being performed (default: "Processing")
        """
        if self.verbose or not self.quiet:
            filename = os.path.basename(file_path)
            self.print(f"{action}: {filename}", MessageLevel.INFO)
    
    def print_progress(self, current: int, total: int, filename: str = ""):
        """Print progress information.
        
        Args:
            current: Current file number
            total: Total number of files
            filename: Optional filename being processed
        """
        if not self.quiet:
            percentage = (current / total * 100) if total > 0 else 0
            progress_bar_length = 30
            filled = int(progress_bar_length * current / total) if total > 0 else 0
            bar = "█" * filled + "░" * (progress_bar_length - filled)
            
            file_info = f" ({filename})" if filename and self.verbose else ""
            print(f"\r[{bar}] {current}/{total} ({percentage:.1f}%){file_info}", end="", flush=True)
            
            if current == total:
                print()  # Newline when complete
    
    def print_summary(self):
        """Print a summary of the sanitization process."""
        if self.quiet:
            return
            
        self.print_header("Summary")
        self.print(f"Files processed: {self.files_processed}", MessageLevel.SUCCESS)
        if self.files_skipped > 0:
            self.print(f"Files skipped: {self.files_skipped}", MessageLevel.WARNING)
        if self.files_failed > 0:
            self.print(f"Files failed: {self.files_failed}", MessageLevel.ERROR)
        
        if self.dry_run:
            self.print("\nThis was a dry run. No files were actually modified.", MessageLevel.WARNING)
    
    def confirm_action(self, message: str) -> bool:
        """Prompt user for confirmation.
        
        Args:
            message: The confirmation prompt
            
        Returns:
            bool: True if user confirms, False otherwise
        """
        if self.quiet or self.dry_run:
            return True
            
        response = input(f"{message} (y/N): ").strip().lower()
        return response in ['y', 'yes']
    
    def reset_counters(self):
        """Reset file processing counters."""
        self.files_processed = 0
        self.files_skipped = 0
        self.files_failed = 0

