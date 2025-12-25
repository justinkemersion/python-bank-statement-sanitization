"""
Paystub Extractor
Extracts structured data from paystub documents (PDF, TXT).
"""

import re
from datetime import datetime
from typing import Dict, Optional, Any, List
import json


class PaystubExtractor:
    """Extracts paystub data from sanitized text content."""
    
    def __init__(self):
        """Initialize the paystub extractor."""
        # Common patterns for paystub fields
        self.patterns = {
            # Pay dates
            'pay_date': [
                r'pay\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'pay\s+date[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
                r'date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            'pay_period': [
                r'pay\s+period[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*[-–]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'period[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*[-–]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            # Earnings
            'gross_pay': [
                r'gross\s+pay[:\s]+\$?([\d,]+\.?\d*)',
                r'gross\s+earnings[:\s]+\$?([\d,]+\.?\d*)',
                r'total\s+gross[:\s]+\$?([\d,]+\.?\d*)',
                r'gross[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'regular_hours': [
                r'regular\s+hours?[:\s]+([\d,]+\.?\d*)',
                r'reg\s+hours?[:\s]+([\d,]+\.?\d*)',
            ],
            'overtime_hours': [
                r'overtime\s+hours?[:\s]+([\d,]+\.?\d*)',
                r'ot\s+hours?[:\s]+([\d,]+\.?\d*)',
            ],
            'regular_rate': [
                r'regular\s+rate[:\s]+\$?([\d,]+\.?\d*)',
                r'hourly\s+rate[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'overtime_rate': [
                r'overtime\s+rate[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'bonus': [
                r'bonus[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'commission': [
                r'commission[:\s]+\$?([\d,]+\.?\d*)',
            ],
            # Deductions
            'federal_tax': [
                r'federal\s+tax[:\s]+\$?([\d,]+\.?\d*)',
                r'fed\s+tax[:\s]+\$?([\d,]+\.?\d*)',
                r'federal\s+withholding[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'state_tax': [
                r'state\s+tax[:\s]+\$?([\d,]+\.?\d*)',
                r'state\s+withholding[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'local_tax': [
                r'local\s+tax[:\s]+\$?([\d,]+\.?\d*)',
                r'local\s+withholding[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'social_security': [
                r'social\s+security[:\s]+\$?([\d,]+\.?\d*)',
                r'ss\s+tax[:\s]+\$?([\d,]+\.?\d*)',
                r'fica[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'medicare': [
                r'medicare[:\s]+\$?([\d,]+\.?\d*)',
                r'med[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'health_insurance': [
                r'health\s+insurance[:\s]+\$?([\d,]+\.?\d*)',
                r'medical[:\s]+\$?([\d,]+\.?\d*)',
                r'health\s+care[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'dental_insurance': [
                r'dental[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'vision_insurance': [
                r'vision[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'retirement_401k': [
                r'401\(?k\)?[:\s]+\$?([\d,]+\.?\d*)',
                r'retirement[:\s]+\$?([\d,]+\.?\d*)',
                r'401k[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'hsa': [
                r'hsa[:\s]+\$?([\d,]+\.?\d*)',
                r'health\s+savings[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'fsa': [
                r'fsa[:\s]+\$?([\d,]+\.?\d*)',
                r'flexible\s+spending[:\s]+\$?([\d,]+\.?\d*)',
            ],
            # Totals
            'total_deductions': [
                r'total\s+deductions?[:\s]+\$?([\d,]+\.?\d*)',
                r'deductions?\s+total[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'net_pay': [
                r'net\s+pay[:\s]+\$?([\d,]+\.?\d*)',
                r'take\s+home[:\s]+\$?([\d,]+\.?\d*)',
                r'net[:\s]+\$?([\d,]+\.?\d*)',
            ],
            # Employer
            'employer_name': [
                r'employer[:\s]+([A-Z][A-Za-z\s&,\.]+)',
                r'company[:\s]+([A-Z][A-Za-z\s&,\.]+)',
            ],
            # YTD
            'ytd_gross': [
                r'ytd\s+gross[:\s]+\$?([\d,]+\.?\d*)',
                r'year\s+to\s+date\s+gross[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'ytd_net': [
                r'ytd\s+net[:\s]+\$?([\d,]+\.?\d*)',
                r'year\s+to\s+date\s+net[:\s]+\$?([\d,]+\.?\d*)',
            ],
            'ytd_taxes': [
                r'ytd\s+taxes?[:\s]+\$?([\d,]+\.?\d*)',
                r'year\s+to\s+date\s+taxes?[:\s]+\$?([\d,]+\.?\d*)',
            ],
        }
        
        # Compile patterns for efficiency
        self.compiled_patterns = {}
        for field, pattern_list in self.patterns.items():
            self.compiled_patterns[field] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                for pattern in pattern_list
            ]
    
    def _extract_value(self, text: str, field: str) -> Optional[float]:
        """Extract a numeric value for a field.
        
        Args:
            text: Text to search
            field: Field name to extract
            
        Returns:
            Extracted value as float, or None if not found
        """
        if field not in self.compiled_patterns:
            return None
        
        for pattern in self.compiled_patterns[field]:
            match = pattern.search(text)
            if match:
                try:
                    # Handle multiple groups (e.g., pay period dates)
                    value_str = match.group(1) if match.groups() else match.group(0)
                    # Remove commas and convert to float
                    value_str = value_str.replace(',', '')
                    return float(value_str)
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_text_value(self, text: str, field: str) -> Optional[str]:
        """Extract a text value for a field.
        
        Args:
            text: Text to search
            field: Field name to extract
            
        Returns:
            Extracted text value, or None if not found
        """
        if field not in self.compiled_patterns:
            return None
        
        for pattern in self.compiled_patterns[field]:
            match = pattern.search(text)
            if match:
                try:
                    value = match.group(1) if match.groups() else match.group(0)
                    return value.strip()
                except (IndexError):
                    continue
        return None
    
    def _extract_pay_period(self, text: str) -> tuple:
        """Extract pay period start and end dates.
        
        Args:
            text: Text to search
            
        Returns:
            Tuple of (start_date, end_date) or (None, None)
        """
        for pattern in self.compiled_patterns['pay_period']:
            match = pattern.search(text)
            if match and len(match.groups()) >= 2:
                return (match.group(1), match.group(2))
        return (None, None)
    
    def extract(self, text: str, source_file: str) -> Optional[Dict[str, Any]]:
        """Extract paystub data from text.
        
        Args:
            text: Sanitized text content from paystub
            source_file: Source file name
            
        Returns:
            Dictionary with paystub data, or None if extraction fails
        """
        if not text:
            return None
        
        # Normalize text - remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Extract basic fields
        pay_date = self._extract_text_value(text, 'pay_date')
        pay_period_start, pay_period_end = self._extract_pay_period(text)
        
        # Extract earnings
        gross_pay = self._extract_value(text, 'gross_pay')
        regular_hours = self._extract_value(text, 'regular_hours')
        overtime_hours = self._extract_value(text, 'overtime_hours')
        regular_rate = self._extract_value(text, 'regular_rate')
        overtime_rate = self._extract_value(text, 'overtime_rate')
        bonus = self._extract_value(text, 'bonus')
        commission = self._extract_value(text, 'commission')
        
        # Extract deductions
        federal_tax = self._extract_value(text, 'federal_tax')
        state_tax = self._extract_value(text, 'state_tax')
        local_tax = self._extract_value(text, 'local_tax')
        social_security = self._extract_value(text, 'social_security')
        medicare = self._extract_value(text, 'medicare')
        health_insurance = self._extract_value(text, 'health_insurance')
        dental_insurance = self._extract_value(text, 'dental_insurance')
        vision_insurance = self._extract_value(text, 'vision_insurance')
        retirement_401k = self._extract_value(text, 'retirement_401k')
        hsa = self._extract_value(text, 'hsa')
        fsa = self._extract_value(text, 'fsa')
        
        # Extract totals
        total_deductions = self._extract_value(text, 'total_deductions')
        net_pay = self._extract_value(text, 'net_pay')
        
        # Extract employer
        employer_name = self._extract_text_value(text, 'employer_name')
        
        # Extract YTD
        ytd_gross = self._extract_value(text, 'ytd_gross')
        ytd_net = self._extract_value(text, 'ytd_net')
        ytd_taxes = self._extract_value(text, 'ytd_taxes')
        
        # Build deductions dictionary
        deductions = {}
        if federal_tax is not None:
            deductions['federal_tax'] = federal_tax
        if state_tax is not None:
            deductions['state_tax'] = state_tax
        if local_tax is not None:
            deductions['local_tax'] = local_tax
        if social_security is not None:
            deductions['social_security'] = social_security
        if medicare is not None:
            deductions['medicare'] = medicare
        if health_insurance is not None:
            deductions['health_insurance'] = health_insurance
        if dental_insurance is not None:
            deductions['dental_insurance'] = dental_insurance
        if vision_insurance is not None:
            deductions['vision_insurance'] = vision_insurance
        if retirement_401k is not None:
            deductions['retirement_401k'] = retirement_401k
        if hsa is not None:
            deductions['hsa'] = hsa
        if fsa is not None:
            deductions['fsa'] = fsa
        
        # Calculate total deductions if not provided
        if total_deductions is None and deductions:
            total_deductions = sum(deductions.values())
        
        # Validate that we extracted at least some key data
        if not pay_date and not gross_pay and not net_pay:
            return None  # Not a valid paystub
        
        return {
            'source_file': source_file,
            'pay_date': pay_date,
            'pay_period_start': pay_period_start,
            'pay_period_end': pay_period_end,
            'employer_name': employer_name,
            'gross_pay': gross_pay,
            'regular_hours': regular_hours,
            'overtime_hours': overtime_hours,
            'regular_rate': regular_rate,
            'overtime_rate': overtime_rate,
            'bonus': bonus,
            'commission': commission,
            'deductions_json': json.dumps(deductions) if deductions else None,
            'total_deductions': total_deductions,
            'net_pay': net_pay,
            'ytd_gross': ytd_gross,
            'ytd_net': ytd_net,
            'ytd_taxes': ytd_taxes,
        }
    
    def is_paystub(self, text: str) -> bool:
        """Check if text appears to be a paystub.
        
        Args:
            text: Text content to check
            
        Returns:
            True if text appears to be a paystub
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Look for paystub indicators
        paystub_keywords = [
            'pay stub',
            'paystub',
            'pay statement',
            'earnings statement',
            'payroll',
            'gross pay',
            'net pay',
            'take home',
            'pay period',
            'federal tax',
            'social security',
            'medicare',
        ]
        
        # Check if at least 3 keywords are present
        keyword_count = sum(1 for keyword in paystub_keywords if keyword in text_lower)
        return keyword_count >= 3

