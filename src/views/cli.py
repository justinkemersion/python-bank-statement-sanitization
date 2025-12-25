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


class Colors:
    """ANSI color codes for professional CLI output."""
    # Reset
    RESET = "\033[0m"
    
    # Text colors - brighter, more professional
    BRIGHT_BLUE = "\033[94m"      # Info/headers
    BRIGHT_GREEN = "\033[92m"     # Success
    BRIGHT_YELLOW = "\033[93m"    # Warning
    BRIGHT_RED = "\033[91m"       # Error
    BRIGHT_CYAN = "\033[96m"      # Debug/verbose
    BRIGHT_MAGENTA = "\033[95m"   # Accent
    
    # Dimmed colors for secondary text
    DIM = "\033[2m"
    DIM_BLUE = "\033[2;34m"
    DIM_GRAY = "\033[2;37m"
    
    # Background colors
    BG_BLUE = "\033[44m"
    BG_GREEN = "\033[42m"
    BG_RED = "\033[41m"
    
    # Text styles
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    @staticmethod
    def supports_color() -> bool:
        """Check if terminal supports colors."""
        return (
            hasattr(sys.stdout, 'isatty') and sys.stdout.isatty() and
            os.getenv('TERM') != 'dumb' and
            os.getenv('NO_COLOR') is None
        )


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
        self.use_colors = Colors.supports_color()
        
    def _colorize(self, text: str, color_code: str) -> str:
        """Apply color to text if colors are supported.
        
        Args:
            text: Text to colorize
            color_code: ANSI color code
            
        Returns:
            str: Colorized text or original text
        """
        if self.use_colors and color_code:
            return f"{color_code}{text}{Colors.RESET}"
        return text
        
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
            
        # Professional color scheme
        color_map = {
            MessageLevel.INFO: Colors.BRIGHT_BLUE,
            MessageLevel.SUCCESS: Colors.BRIGHT_GREEN,
            MessageLevel.WARNING: Colors.BRIGHT_YELLOW,
            MessageLevel.ERROR: Colors.BRIGHT_RED,
            MessageLevel.DEBUG: Colors.BRIGHT_CYAN,
        }
        
        # Professional icons/symbols
        prefix_map = {
            MessageLevel.SUCCESS: "✓",
            MessageLevel.WARNING: "⚠",
            MessageLevel.ERROR: "✗",
            MessageLevel.DEBUG: "●",
        }
        
        color = color_map.get(level, "")
        prefix = prefix_map.get(level, "")
        
        if prefix:
            # Format: [COLOR][PREFIX] message
            prefix_text = self._colorize(prefix, color)
            formatted_message = f"{prefix_text} {message}"
        else:
            formatted_message = self._colorize(message, color)
        
        print(formatted_message, end=end, file=sys.stdout if level != MessageLevel.ERROR else sys.stderr)
        
    def print_banner(self):
        """Print an ASCII art banner."""
        if self.quiet:
            return
            
        banner = f"""
{self._colorize('╔══════════════════════════════════════════════════════════════╗', Colors.BRIGHT_BLUE)}
{self._colorize('║', Colors.BRIGHT_BLUE)}  {self._colorize('Bank Statement Sanitizer', Colors.BOLD + Colors.BRIGHT_CYAN)}                              {self._colorize('║', Colors.BRIGHT_BLUE)}
{self._colorize('║', Colors.BRIGHT_BLUE)}  {self._colorize('Privacy Protection for Financial Documents', Colors.DIM)}              {self._colorize('║', Colors.BRIGHT_BLUE)}
{self._colorize('╚══════════════════════════════════════════════════════════════╝', Colors.BRIGHT_BLUE)}
"""
        print(banner)
    
    def print_header(self, title: str):
        """Print a section header with professional styling.
        
        Args:
            title: The header text
        """
        if not self.quiet:
            width = 70
            border = "═" * (width - 4)
            title_text = self._colorize(title.upper(), Colors.BOLD + Colors.BRIGHT_BLUE)
            print(f"\n{self._colorize('╔' + border + '╗', Colors.BRIGHT_BLUE)}")
            print(f"{self._colorize('║', Colors.BRIGHT_BLUE)}  {title_text:<{width-6}}  {self._colorize('║', Colors.BRIGHT_BLUE)}")
            print(f"{self._colorize('╚' + border + '╝', Colors.BRIGHT_BLUE)}\n")
    
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
        """Print progress information with professional styling.
        
        Args:
            current: Current file number
            total: Total number of files
            filename: Optional filename being processed
        """
        if not self.quiet:
            percentage = (current / total * 100) if total > 0 else 0
            progress_bar_length = 40
            filled = int(progress_bar_length * current / total) if total > 0 else 0
            empty = progress_bar_length - filled
            
            # Professional progress bar with gradient effect
            if self.use_colors:
                # Use different shades for filled portion
                filled_bar = self._colorize("█" * filled, Colors.BRIGHT_GREEN)
                empty_bar = self._colorize("░" * empty, Colors.DIM_GRAY)
            else:
                filled_bar = "█" * filled
                empty_bar = "░" * empty
            
            bar = f"{filled_bar}{empty_bar}"
            percentage_text = self._colorize(f"{percentage:.1f}%", Colors.BRIGHT_CYAN)
            count_text = self._colorize(f"{current}/{total}", Colors.DIM)
            
            file_info = ""
            if filename and self.verbose:
                file_info = f" {self._colorize('→', Colors.DIM)} {self._colorize(filename, Colors.DIM_BLUE)}"
            
            progress_line = f"\r{self._colorize('│', Colors.BRIGHT_BLUE)} {bar} {self._colorize('│', Colors.BRIGHT_BLUE)} {percentage_text} {count_text}{file_info}"
            print(progress_line, end="", flush=True)
            
            if current == total:
                print()  # Newline when complete
    
    def print_summary(self):
        """Print a professional summary table of the sanitization process."""
        if self.quiet:
            return
            
        self.print_header("Summary")
        
        # Create a table-like summary
        stats = [
            ("Files Processed", self.files_processed, MessageLevel.SUCCESS),
            ("Files Skipped", self.files_skipped, MessageLevel.WARNING),
            ("Files Failed", self.files_failed, MessageLevel.ERROR),
        ]
        
        # Print statistics in a table format
        for label, count, level in stats:
            if count > 0 or label == "Files Processed":
                # Format: "Label: count" with appropriate color
                color = {
                    MessageLevel.SUCCESS: Colors.BRIGHT_GREEN,
                    MessageLevel.WARNING: Colors.BRIGHT_YELLOW,
                    MessageLevel.ERROR: Colors.BRIGHT_RED,
                }.get(level, Colors.BRIGHT_BLUE)
                
                label_text = self._colorize(f"{label:.<20}", Colors.DIM)
                count_text = self._colorize(f"{count:>4}", color)
                print(f"  {label_text} {count_text}")
        
        # Total line
        total = self.files_processed + self.files_skipped + self.files_failed
        if total > 0:
            total_label = self._colorize("Total Files", Colors.BOLD)
            total_count = self._colorize(f"{total:>4}", Colors.BRIGHT_CYAN)
            print(f"  {self._colorize('─' * 25, Colors.DIM)}")
            print(f"  {total_label:.<20} {total_count}")
        
        if self.dry_run:
            print()
            self.print("This was a dry run. No files were actually modified.", MessageLevel.WARNING)
        
        # Success message
        if self.files_processed > 0 and self.files_failed == 0:
            print()
            self.print("Sanitization completed successfully!", MessageLevel.SUCCESS)
    
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

