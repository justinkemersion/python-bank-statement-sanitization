"""
Tax Document Extractor
Extracts structured data from tax documents (1099-INT, 1099-DIV, 1099-B, W-2).
"""

import re
from datetime import datetime
from typing import Dict, Optional, Any, List


class TaxDocumentExtractor:
    """Extracts tax document data from PDFs and text files."""
    
    def __init__(self):
        """Initialize the tax document extractor."""
        # Patterns for document type detection
        self.document_patterns = {
            '1099-INT': [
                r'form\s+1099[-\s]?int',
                r'1099[-\s]?int',
                r'interest\s+income',
            ],
            '1099-DIV': [
                r'form\s+1099[-\s]?div',
                r'1099[-\s]?div',
                r'dividend\s+income',
            ],
            '1099-B': [
                r'form\s+1099[-\s]?b',
                r'1099[-\s]?b',
                r'proceeds\s+from\s+broker',
                r'broker\s+transactions',
            ],
            'W-2': [
                r'form\s+w[-\s]?2',
                r'\bw[-\s]?2\b',
                r'wage\s+and\s+tax\s+statement',
            ],
        }
        
        # Patterns for 1099-INT (Interest Income)
        self.int_patterns = {
            'payer_name': [
                r'payer[:\s]+([A-Z][A-Za-z0-9\s&,\.]+)',
                r'payer\'s\s+name[:\s]+([A-Z][A-Za-z0-9\s&,\.]+)',
            ],
            'interest_income': [
                r'interest\s+income[:\s]+\$?([\d,]+\.?\d*)',
                r'total\s+interest[:\s]+\$?([\d,]+\.?\d*)',
                r'1[:\s]+\$?([\d,]+\.?\d*)',  # Box 1
            ],
            'federal_tax_withheld': [
                r'federal\s+tax\s+withheld[:\s]+\$?([\d,]+\.?\d*)',
                r'4[:\s]+\$?([\d,]+\.?\d*)',  # Box 4
            ],
            'tax_year': [
                r'calendar\s+year[:\s]+(\d{4})',
                r'year[:\s]+(\d{4})',
            ],
        }
        
        # Patterns for 1099-DIV (Dividends)
        self.div_patterns = {
            'payer_name': [
                r'payer[:\s]+([A-Z][A-Za-z0-9\s&,\.]+)',
                r'payer\'s\s+name[:\s]+([A-Z][A-Za-z0-9\s&,\.]+)',
            ],
            'ordinary_dividends': [
                r'ordinary\s+dividends[:\s]+\$?([\d,]+\.?\d*)',
                r'1a[:\s]+\$?([\d,]+\.?\d*)',  # Box 1a
            ],
            'qualified_dividends': [
                r'qualified\s+dividends[:\s]+\$?([\d,]+\.?\d*)',
                r'1b[:\s]+\$?([\d,]+\.?\d*)',  # Box 1b
            ],
            'total_capital_gain': [
                r'total\s+capital\s+gain[:\s]+\$?([\d,]+\.?\d*)',
                r'2a[:\s]+\$?([\d,]+\.?\d*)',  # Box 2a
            ],
            'federal_tax_withheld': [
                r'federal\s+tax\s+withheld[:\s]+\$?([\d,]+\.?\d*)',
                r'4[:\s]+\$?([\d,]+\.?\d*)',  # Box 4
            ],
            'tax_year': [
                r'calendar\s+year[:\s]+(\d{4})',
                r'year[:\s]+(\d{4})',
            ],
        }
        
        # Patterns for 1099-B (Broker Transactions)
        self.b_patterns = {
            'payer_name': [
                r'payer[:\s]+([A-Z][A-Za-z0-9\s&,\.]+)',
                r'broker[:\s]+([A-Z][A-Za-z0-9\s&,\.]+)',
            ],
            'proceeds': [
                r'proceeds[:\s]+\$?([\d,]+\.?\d*)',
                r'total\s+proceeds[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'cost_basis': [
                r'cost\s+basis[:\s]+\$?([\d,]+\.?\d*)',
                r'basis[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'gain_loss': [
                r'gain[:\s]+\$?([\d,]+\.?\d*)',
                r'loss[:\s]+\$?([\d,]+\.?\d*)',
                r'net\s+gain[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'tax_year': [
                r'calendar\s+year[:\s]+(\d{4})',
                r'year[:\s]+(\d{4})',
            ],
        }
        
        # Patterns for W-2 (Wage Statement)
        self.w2_patterns = {
            'employer_name': [
                r'employer[:\s]+([A-Z][A-Za-z0-9\s&,\.]+)',
                r'employer\'s\s+name[:\s]+([A-Z][A-Za-z0-9\s&,\.]+)',
            ],
            'wages': [
                r'wages[:\s]+\$?([\d,]+\.?\d*)',
                r'box\s+1[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'federal_tax_withheld': [
                r'federal\s+income\s+tax[:\s]+\$?([\d,]+\.?\d*)',
                r'box\s+2[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'social_security_wages': [
                r'social\s+security\s+wages[:\s]+\$?([\d,]+\.?\d*)',
                r'box\s+3[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'social_security_tax': [
                r'social\s+security\s+tax[:\s]+\$?([\d,]+\.?\d*)',
                r'box\s+4[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'medicare_wages': [
                r'medicare\s+wages[:\s]+\$?([\d,]+\.?\d*)',
                r'box\s+5[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'medicare_tax': [
                r'medicare\s+tax[:\s]+\$?([\d,]+\.?\d*)',
                r'box\s+6[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'tax_year': [
                r'calendar\s+year[:\s]+(\d{4})',
                r'year[:\s]+(\d{4})',
            ],
        }
        
        # Compile patterns
        self.compiled_doc_patterns = {}
        for doc_type, pattern_list in self.document_patterns.items():
            self.compiled_doc_patterns[doc_type] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                for pattern in pattern_list
            ]
    
    def detect_document_type(self, text: str, source_file: str) -> Optional[str]:
        """Detect tax document type from text.
        
        Args:
            text: Document text content
            source_file: Source file name
            
        Returns:
            Document type string (1099-INT, 1099-DIV, 1099-B, W-2) or None
        """
        text_lower = text.lower()
        filename_lower = source_file.lower()
        
        # Check filename first
        for doc_type, patterns in self.compiled_doc_patterns.items():
            for pattern in patterns:
                if pattern.search(filename_lower):
                    return doc_type
        
        # Check text content
        for doc_type, patterns in self.compiled_doc_patterns.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    return doc_type
        
        return None
    
    def is_tax_document(self, text: str, source_file: str) -> bool:
        """Check if document is a tax form.
        
        Args:
            text: Document text content
            source_file: Source file name
            
        Returns:
            True if this appears to be a tax document
        """
        return self.detect_document_type(text, source_file) is not None
    
    def extract_1099_int(self, text: str) -> Dict[str, Any]:
        """Extract data from 1099-INT form.
        
        Args:
            text: Document text content
            
        Returns:
            Dictionary with 1099-INT data
        """
        data = {'document_type': '1099-INT'}
        
        for field, patterns in self.int_patterns.items():
            for pattern_str in patterns:
                pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
                match = pattern.search(text)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    # Clean up value
                    if field in ['interest_income', 'federal_tax_withheld']:
                        value = value.replace(',', '').replace('$', '')
                        try:
                            data[field] = float(value)
                        except ValueError:
                            pass
                    elif field == 'tax_year':
                        try:
                            data[field] = int(value)
                        except ValueError:
                            pass
                    else:
                        data[field] = value.strip()
                    break
        
        return data
    
    def extract_1099_div(self, text: str) -> Dict[str, Any]:
        """Extract data from 1099-DIV form.
        
        Args:
            text: Document text content
            
        Returns:
            Dictionary with 1099-DIV data
        """
        data = {'document_type': '1099-DIV'}
        
        for field, patterns in self.div_patterns.items():
            for pattern_str in patterns:
                pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
                match = pattern.search(text)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    # Clean up value
                    if field in ['ordinary_dividends', 'qualified_dividends', 'total_capital_gain', 'federal_tax_withheld']:
                        value = value.replace(',', '').replace('$', '')
                        try:
                            data[field] = float(value)
                        except ValueError:
                            pass
                    elif field == 'tax_year':
                        try:
                            data[field] = int(value)
                        except ValueError:
                            pass
                    else:
                        data[field] = value.strip()
                    break
        
        return data
    
    def extract_1099_b(self, text: str) -> Dict[str, Any]:
        """Extract data from 1099-B form.
        
        Args:
            text: Document text content
            
        Returns:
            Dictionary with 1099-B data
        """
        data = {'document_type': '1099-B'}
        
        for field, patterns in self.b_patterns.items():
            for pattern_str in patterns:
                pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
                match = pattern.search(text)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    # Clean up value
                    if field in ['proceeds', 'cost_basis', 'gain_loss']:
                        value = value.replace(',', '').replace('$', '')
                        try:
                            data[field] = float(value)
                        except ValueError:
                            pass
                    elif field == 'tax_year':
                        try:
                            data[field] = int(value)
                        except ValueError:
                            pass
                    else:
                        data[field] = value.strip()
                    break
        
        return data
    
    def extract_w2(self, text: str) -> Dict[str, Any]:
        """Extract data from W-2 form.
        
        Args:
            text: Document text content
            
        Returns:
            Dictionary with W-2 data
        """
        data = {'document_type': 'W-2'}
        
        for field, patterns in self.w2_patterns.items():
            for pattern_str in patterns:
                pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
                match = pattern.search(text)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    # Clean up value
                    if field in ['wages', 'federal_tax_withheld', 'social_security_wages', 
                                'social_security_tax', 'medicare_wages', 'medicare_tax']:
                        value = value.replace(',', '').replace('$', '')
                        try:
                            data[field] = float(value)
                        except ValueError:
                            pass
                    elif field == 'tax_year':
                        try:
                            data[field] = int(value)
                        except ValueError:
                            pass
                    else:
                        data[field] = value.strip()
                    break
        
        return data
    
    def extract(self, text: str, source_file: str) -> Optional[Dict[str, Any]]:
        """Extract tax document data from text.
        
        Args:
            text: Document text content
            source_file: Source file name
            
        Returns:
            Dictionary with tax document data, or None if not a tax document
        """
        if not text:
            return None
        
        # Detect document type
        doc_type = self.detect_document_type(text, source_file)
        if not doc_type:
            return None
        
        # Extract based on document type
        if doc_type == '1099-INT':
            data = self.extract_1099_int(text)
        elif doc_type == '1099-DIV':
            data = self.extract_1099_div(text)
        elif doc_type == '1099-B':
            data = self.extract_1099_b(text)
        elif doc_type == 'W-2':
            data = self.extract_w2(text)
        else:
            return None
        
        # Add source file
        data['source_file'] = source_file
        
        # Add tax year if not found (try to infer from filename or current year)
        if 'tax_year' not in data or not data.get('tax_year'):
            # Try to extract from filename
            year_match = re.search(r'(\d{4})', source_file)
            if year_match:
                try:
                    data['tax_year'] = int(year_match.group(1))
                except ValueError:
                    pass
            
            # Default to current year if still not found
            if 'tax_year' not in data or not data.get('tax_year'):
                data['tax_year'] = datetime.now().year
        
        return data

