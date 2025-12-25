"""
Debt Payoff Calculator
Calculates debt payoff strategies (snowball, avalanche) and timelines.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import math


class DebtCalculator:
    """Calculates debt payoff strategies and timelines."""
    
    def __init__(self):
        """Initialize the debt calculator."""
        pass
    
    def calculate_snowball_strategy(self, debts: List[Dict[str, Any]], 
                                    monthly_payment: float) -> Dict[str, Any]:
        """Calculate debt snowball payoff strategy (pay smallest balance first).
        
        Args:
            debts: List of debt dictionaries with 'bank_name', 'balance', 'apr', 'minimum_payment'
            monthly_payment: Total monthly payment available for debt
        
        Returns:
            Dictionary with payoff strategy details
        """
        # Sort by balance (smallest first)
        sorted_debts = sorted(debts, key=lambda x: x.get('balance', 0))
        
        return self._calculate_payoff_strategy(sorted_debts, monthly_payment, 'snowball')
    
    def calculate_avalanche_strategy(self, debts: List[Dict[str, Any]], 
                                     monthly_payment: float) -> Dict[str, Any]:
        """Calculate debt avalanche payoff strategy (pay highest APR first).
        
        Args:
            debts: List of debt dictionaries with 'bank_name', 'balance', 'apr', 'minimum_payment'
            monthly_payment: Total monthly payment available for debt
        
        Returns:
            Dictionary with payoff strategy details
        """
        # Sort by APR (highest first), then by balance if APR is same
        sorted_debts = sorted(debts, key=lambda x: (x.get('apr', 0) or 0, -x.get('balance', 0)), reverse=True)
        
        return self._calculate_payoff_strategy(sorted_debts, monthly_payment, 'avalanche')
    
    def _calculate_payoff_strategy(self, debts: List[Dict[str, Any]], 
                                   monthly_payment: float, strategy_name: str) -> Dict[str, Any]:
        """Calculate payoff strategy for ordered list of debts.
        
        Args:
            debts: Ordered list of debts
            monthly_payment: Total monthly payment available
            strategy_name: Name of strategy ('snowball' or 'avalanche')
        
        Returns:
            Dictionary with strategy details
        """
        if not debts or monthly_payment <= 0:
            return {
                'strategy': strategy_name,
                'total_debt': 0,
                'total_interest': 0,
                'months_to_payoff': 0,
                'payoff_date': None,
                'payoff_plan': []
            }
        
        total_debt = sum(d.get('balance', 0) for d in debts)
        remaining_payment = monthly_payment
        payoff_plan = []
        total_interest = 0
        current_date = datetime.now()
        
        for debt in debts:
            bank_name = debt.get('bank_name', 'Unknown')
            balance = debt.get('balance', 0)
            apr = debt.get('apr', 0) or 0
            min_payment = debt.get('minimum_payment', 0) or 0
            
            if balance <= 0:
                continue
            
            # Calculate monthly interest rate
            monthly_rate = (apr / 100) / 12 if apr > 0 else 0
            
            # Track this debt's payoff
            debt_balance = balance
            debt_interest = 0
            months = 0
            payments = []
            
            while debt_balance > 0.01:  # Continue until paid off
                # Calculate interest for this month
                interest_this_month = debt_balance * monthly_rate if monthly_rate > 0 else 0
                debt_interest += interest_this_month
                total_interest += interest_this_month
                
                # Calculate payment for this debt
                # Use minimum payment if other debts still exist, otherwise use all remaining
                if any(d.get('balance', 0) > 0.01 for d in debts if d.get('bank_name') != bank_name):
                    # Other debts exist - pay minimum on this one
                    payment = min(min_payment, debt_balance + interest_this_month)
                else:
                    # Last debt - use all remaining payment
                    payment = min(remaining_payment, debt_balance + interest_this_month)
                
                # Apply payment
                debt_balance = debt_balance + interest_this_month - payment
                if debt_balance < 0:
                    debt_balance = 0
                
                months += 1
                payments.append({
                    'month': months,
                    'balance_before': debt_balance + payment - interest_this_month,
                    'interest': interest_this_month,
                    'payment': payment,
                    'balance_after': debt_balance
                })
                
                # Once this debt is paid, add its minimum payment to remaining payment
                if debt_balance <= 0.01:
                    remaining_payment += min_payment
                    break
            
            payoff_plan.append({
                'bank_name': bank_name,
                'starting_balance': balance,
                'months_to_payoff': months,
                'total_interest': debt_interest,
                'payoff_date': (current_date + timedelta(days=months * 30)).strftime('%Y-%m-%d'),
                'monthly_payments': payments[-3:] if len(payments) > 3 else payments  # Last 3 payments
            })
            
            # Update current date for next debt
            current_date += timedelta(days=months * 30)
        
        # Calculate total months
        total_months = sum(p.get('months_to_payoff', 0) for p in payoff_plan)
        payoff_date = (datetime.now() + timedelta(days=total_months * 30)).strftime('%Y-%m-%d')
        
        return {
            'strategy': strategy_name,
            'total_debt': total_debt,
            'total_interest': total_interest,
            'months_to_payoff': total_months,
            'payoff_date': payoff_date,
            'total_paid': total_debt + total_interest,
            'payoff_plan': payoff_plan
        }
    
    def compare_strategies(self, debts: List[Dict[str, Any]], 
                          monthly_payment: float) -> Dict[str, Any]:
        """Compare snowball vs avalanche strategies.
        
        Args:
            debts: List of debt dictionaries
            monthly_payment: Total monthly payment available
        
        Returns:
            Dictionary comparing both strategies
        """
        snowball = self.calculate_snowball_strategy(debts, monthly_payment)
        avalanche = self.calculate_avalanche_strategy(debts, monthly_payment)
        
        return {
            'snowball': snowball,
            'avalanche': avalanche,
            'recommendation': self._recommend_strategy(snowball, avalanche)
        }
    
    def _recommend_strategy(self, snowball: Dict[str, Any], 
                            avalanche: Dict[str, Any]) -> str:
        """Recommend which strategy is better.
        
        Args:
            snowball: Snowball strategy results
            avalanche: Avalanche strategy results
        
        Returns:
            Recommendation string
        """
        snowball_months = snowball.get('months_to_payoff', 0)
        avalanche_months = avalanche.get('months_to_payoff', 0)
        snowball_interest = snowball.get('total_interest', 0)
        avalanche_interest = avalanche.get('total_interest', 0)
        
        if avalanche_months < snowball_months and avalanche_interest < snowball_interest:
            return "Avalanche strategy saves more time and money"
        elif snowball_months < avalanche_months:
            return "Snowball strategy pays off faster (psychological benefit)"
        elif avalanche_interest < snowball_interest:
            return "Avalanche strategy saves more money in interest"
        else:
            return "Both strategies are similar - choose based on preference"

