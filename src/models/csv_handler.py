"""
CSV File Handler
Handles reading and sanitizing CSV bank statement files.
"""

import csv
import os
from src.models.sanitizer import Sanitizer


class CSVHandler:
    """Handler for CSV bank statement files."""
    
    def __init__(self):
        pass
    
    def read_csv(self, csv_path):
        """Read CSV file and return as list of dictionaries.
        
        Args:
            csv_path: Path to the CSV file to read
            
        Returns:
            list: List of dictionaries representing rows, or None if error
        """
        print(f"Reading CSV file: {csv_path}")
        try:
            rows = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(f, delimiter=delimiter)
                for row in reader:
                    rows.append(row)
            return rows
        except FileNotFoundError:
            print(f"Error: CSV file not found: {csv_path}")
            return None
        except PermissionError:
            print(f"Error: Permission denied when reading CSV: {csv_path}")
            return None
        except Exception as e:
            print(f"Error reading CSV file {csv_path}: {e}")
            return None
    
    def sanitize_csv_data(self, rows, sanitizer):
        """Sanitize CSV data by redacting sensitive information in all fields.
        
        Args:
            rows: List of dictionaries representing CSV rows
            sanitizer: Sanitizer instance to use
            
        Returns:
            tuple: (sanitized_rows, detected_patterns)
        """
        if not rows:
            return [], set()
        
        sanitized_rows = []
        all_detected_patterns = set()
        
        for row in rows:
            sanitized_row = {}
            for key, value in row.items():
                if value:
                    # Sanitize the value
                    sanitized_value, detected_patterns = sanitizer.sanitize_text(
                        str(value), track_patterns=True
                    )
                    all_detected_patterns.update(detected_patterns)
                    sanitized_row[key] = sanitized_value
                else:
                    sanitized_row[key] = value
            sanitized_rows.append(sanitized_row)
        
        return sanitized_rows, all_detected_patterns
    
    def save_sanitized_csv(self, sanitized_rows, output_path, metadata_header="", metadata_footer=""):
        """Save sanitized CSV data to a file.
        
        Args:
            sanitized_rows: List of sanitized row dictionaries
            output_path: Path where the sanitized CSV should be saved
            metadata_header: Optional header text to prepend
            metadata_footer: Optional footer text to append
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Saving sanitized CSV to: {output_path}")
        try:
            if not sanitized_rows:
                print("Warning: No data to save")
                return False
            
            # Get fieldnames from first row
            fieldnames = list(sanitized_rows[0].keys())
            
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                # Write metadata header as comments if provided
                if metadata_header:
                    for line in metadata_header.split('\n'):
                        if line.strip():
                            f.write(f"# {line}\n")
                    f.write("\n")
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(sanitized_rows)
                
                # Write metadata footer as comments if provided
                if metadata_footer:
                    f.write("\n")
                    for line in metadata_footer.split('\n'):
                        if line.strip():
                            f.write(f"# {line}\n")
            
            return True
        except PermissionError:
            print(f"Error: Permission denied when writing to: {output_path}")
            return False
        except OSError as e:
            print(f"Error: Unable to write to {output_path}: {e}")
            return False
        except Exception as e:
            print(f"Error saving sanitized CSV to {output_path}: {e}")
            return False

