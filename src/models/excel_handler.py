"""
Excel File Handler
Handles reading and sanitizing Excel/XLSX bank statement files.
"""

import pandas as pd
import os
from src.models.sanitizer import Sanitizer


class ExcelHandler:
    """Handler for Excel/XLSX bank statement files."""
    
    def __init__(self):
        pass
    
    def read_excel(self, excel_path, sheet_name=0):
        """Read Excel file and return as pandas DataFrame.
        
        Args:
            excel_path: Path to the Excel file to read
            sheet_name: Sheet name or index to read (default: first sheet)
            
        Returns:
            pandas.DataFrame: DataFrame containing the data, or None if error
        """
        print(f"Reading Excel file: {excel_path}")
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            return df
        except FileNotFoundError:
            print(f"Error: Excel file not found: {excel_path}")
            return None
        except PermissionError:
            print(f"Error: Permission denied when reading Excel: {excel_path}")
            return None
        except Exception as e:
            print(f"Error reading Excel file {excel_path}: {e}")
            return None
    
    def sanitize_excel_data(self, df, sanitizer):
        """Sanitize Excel data by redacting sensitive information in all columns.
        
        Args:
            df: pandas DataFrame containing the data
            sanitizer: Sanitizer instance to use
            
        Returns:
            tuple: (sanitized_df, detected_patterns)
        """
        if df is None or df.empty:
            return df, set()
        
        sanitized_df = df.copy()
        all_detected_patterns = set()
        
        # Sanitize all string columns
        for column in sanitized_df.columns:
            if sanitized_df[column].dtype == 'object':  # String/object columns
                for idx in sanitized_df.index:
                    value = sanitized_df.at[idx, column]
                    if pd.notna(value) and value:
                        sanitized_value, detected_patterns = sanitizer.sanitize_text(
                            str(value), track_patterns=True
                        )
                        all_detected_patterns.update(detected_patterns)
                        sanitized_df.at[idx, column] = sanitized_value
        
        return sanitized_df, all_detected_patterns
    
    def save_sanitized_excel(self, sanitized_df, output_path, metadata_header="", metadata_footer=""):
        """Save sanitized Excel data to a file.
        
        Args:
            sanitized_df: Sanitized pandas DataFrame
            output_path: Path where the sanitized Excel file should be saved
            metadata_header: Optional header text (saved as comment in first row)
            metadata_footer: Optional footer text (saved as comment in last row)
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Saving sanitized Excel to: {output_path}")
        try:
            if sanitized_df is None or sanitized_df.empty:
                print("Warning: No data to save")
                return False
            
            # Create a new Excel writer
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                sanitized_df.to_excel(writer, sheet_name='Sanitized Data', index=False)
                
                # Add metadata as a separate sheet if provided
                if metadata_header or metadata_footer:
                    metadata_rows = []
                    if metadata_header:
                        for line in metadata_header.split('\n'):
                            if line.strip():
                                metadata_rows.append([line])
                        metadata_rows.append([])  # Empty row separator
                    if metadata_footer:
                        for line in metadata_footer.split('\n'):
                            if line.strip():
                                metadata_rows.append([line])
                    
                    metadata_df = pd.DataFrame(metadata_rows, columns=['Metadata'])
                    metadata_df.to_excel(writer, sheet_name='Sanitization Info', index=False)
            
            return True
        except PermissionError:
            print(f"Error: Permission denied when writing to: {output_path}")
            return False
        except OSError as e:
            print(f"Error: Unable to write to {output_path}: {e}")
            return False
        except Exception as e:
            print(f"Error saving sanitized Excel to {output_path}: {e}")
            return False


