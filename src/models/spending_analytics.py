"""
Spending Analytics
Provides spending analysis, reports, and insights from transaction data.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict


class SpendingAnalytics:
    """Analyzes spending patterns and generates reports."""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize spending analytics.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
    
    def get_monthly_summary(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get monthly spending summary.
        
        Args:
            year: Optional year to filter (default: all years)
            
        Returns:
            List of monthly summaries with count, total, and average
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                COUNT(*) as count,
                SUM(amount) as total,
                AVG(amount) as average,
                MIN(amount) as min_amount,
                MAX(amount) as max_amount
            FROM transactions
            WHERE transaction_date IS NOT NULL
        """
        
        params = []
        if year:
            query += " AND strftime('%Y', transaction_date) = ?"
            params.append(str(year))
        
        query += " GROUP BY month ORDER BY month"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        monthly_data = []
        for row in rows:
            monthly_data.append({
                'month': row[0],
                'transaction_count': row[1],
                'total_spending': row[2] if row[2] else 0,
                'average_transaction': row[3] if row[3] else 0,
                'min_transaction': row[4] if row[4] else 0,
                'max_transaction': row[5] if row[5] else 0
            })
        
        return monthly_data
    
    def get_category_breakdown(self, date_range: Optional[Tuple[str, str]] = None) -> List[Dict[str, Any]]:
        """Get spending breakdown by category.
        
        Args:
            date_range: Optional tuple of (start_date, end_date) in YYYY-MM-DD format
            
        Returns:
            List of category summaries with count, total, and percentage
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                COALESCE(category, 'Uncategorized') as category,
                COUNT(*) as count,
                SUM(amount) as total,
                AVG(amount) as average
            FROM transactions
            WHERE amount IS NOT NULL
        """
        
        params = []
        if date_range:
            start_date, end_date = date_range
            query += " AND transaction_date >= ? AND transaction_date <= ?"
            params.extend([start_date, end_date])
        
        query += " GROUP BY category ORDER BY ABS(total) DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Calculate total for percentage
        total_spending = sum(abs(row[2]) for row in rows if row[2])
        
        category_data = []
        for row in rows:
            category_total = row[2] if row[2] else 0
            percentage = (abs(category_total) / total_spending * 100) if total_spending > 0 else 0
            
            category_data.append({
                'category': row[0],
                'transaction_count': row[1],
                'total_spending': category_total,
                'average_transaction': row[3] if row[3] else 0,
                'percentage': percentage
            })
        
        return category_data
    
    def get_top_merchants(self, limit: int = 20, date_range: Optional[Tuple[str, str]] = None) -> List[Dict[str, Any]]:
        """Get top merchants by spending.
        
        Args:
            limit: Number of top merchants to return
            date_range: Optional tuple of (start_date, end_date) in YYYY-MM-DD format
            
        Returns:
            List of merchant summaries
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                COALESCE(merchant_name, 'Unknown') as merchant,
                COUNT(*) as count,
                SUM(amount) as total,
                AVG(amount) as average,
                MIN(transaction_date) as first_transaction,
                MAX(transaction_date) as last_transaction
            FROM transactions
            WHERE amount IS NOT NULL
        """
        
        params = []
        if date_range:
            start_date, end_date = date_range
            query += " AND transaction_date >= ? AND transaction_date <= ?"
            params.extend([start_date, end_date])
        
        query += " GROUP BY merchant_name ORDER BY ABS(total) DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        merchants = []
        for row in rows:
            merchants.append({
                'merchant': row[0],
                'transaction_count': row[1],
                'total_spending': row[2] if row[2] else 0,
                'average_transaction': row[3] if row[3] else 0,
                'first_transaction': row[4],
                'last_transaction': row[5]
            })
        
        return merchants
    
    def get_spending_trends(self, category: Optional[str] = None, months: int = 12) -> List[Dict[str, Any]]:
        """Get spending trends over time.
        
        Args:
            category: Optional category to filter
            months: Number of months to analyze (default: 12)
            
        Returns:
            List of monthly spending with trend indicators
        """
        monthly_data = self.get_monthly_summary()
        
        # Get last N months
        if len(monthly_data) > months:
            monthly_data = monthly_data[-months:]
        
        # Calculate trends
        trends = []
        for i, month_data in enumerate(monthly_data):
            trend = None
            if i > 0:
                prev_total = abs(monthly_data[i-1]['total_spending'])
                curr_total = abs(month_data['total_spending'])
                if prev_total > 0:
                    change = ((curr_total - prev_total) / prev_total) * 100
                    trend = {
                        'change_percent': change,
                        'change_amount': curr_total - prev_total,
                        'direction': 'up' if change > 0 else 'down' if change < 0 else 'stable'
                    }
            
            month_info = month_data.copy()
            month_info['trend'] = trend
            trends.append(month_info)
        
        return trends
    
    def get_category_comparison(self, category: str, months: int = 12) -> Dict[str, Any]:
        """Compare category spending across months.
        
        Args:
            category: Category name to analyze
            months: Number of months to compare
            
        Returns:
            Dictionary with monthly breakdown and statistics
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                COUNT(*) as count,
                SUM(amount) as total,
                AVG(amount) as average
            FROM transactions
            WHERE category = ? AND transaction_date IS NOT NULL
            GROUP BY month
            ORDER BY month DESC
            LIMIT ?
        """
        
        cursor.execute(query, (category, months))
        rows = cursor.fetchall()
        
        monthly_breakdown = []
        for row in rows:
            monthly_breakdown.append({
                'month': row[0],
                'transaction_count': row[1],
                'total_spending': row[2] if row[2] else 0,
                'average_transaction': row[3] if row[3] else 0
            })
        
        # Calculate statistics
        totals = [abs(m['total_spending']) for m in monthly_breakdown]
        averages = [m['average_transaction'] for m in monthly_breakdown]
        
        stats = {
            'category': category,
            'months_analyzed': len(monthly_breakdown),
            'average_monthly_spending': sum(totals) / len(totals) if totals else 0,
            'min_monthly_spending': min(totals) if totals else 0,
            'max_monthly_spending': max(totals) if totals else 0,
            'total_spending': sum(totals),
            'average_transaction_size': sum(averages) / len(averages) if averages else 0
        }
        
        return {
            'statistics': stats,
            'monthly_breakdown': monthly_breakdown
        }
    
    def generate_spending_report(self, output_path: str, year: Optional[int] = None) -> bool:
        """Generate comprehensive spending report.
        
        Args:
            output_path: Path where report should be saved
            year: Optional year to filter
            
        Returns:
            bool: True if successful
        """
        try:
            monthly_summary = self.get_monthly_summary(year)
            category_breakdown = self.get_category_breakdown()
            top_merchants = self.get_top_merchants(limit=20)
            spending_trends = self.get_spending_trends(months=12)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("COMPREHENSIVE SPENDING ANALYSIS REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                # Overview
                f.write("OVERVIEW\n")
                f.write("-" * 80 + "\n")
                if monthly_summary:
                    total_spending = sum(abs(m['total_spending']) for m in monthly_summary)
                    avg_monthly = total_spending / len(monthly_summary) if monthly_summary else 0
                    f.write(f"Total Months Analyzed: {len(monthly_summary)}\n")
                    f.write(f"Total Spending: ${total_spending:,.2f}\n")
                    f.write(f"Average Monthly Spending: ${avg_monthly:,.2f}\n")
                    f.write(f"Date Range: {monthly_summary[0]['month']} to {monthly_summary[-1]['month']}\n")
                f.write("\n")
                
                # Monthly Summary
                f.write("MONTHLY SPENDING SUMMARY\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'Month':<12} {'Transactions':<15} {'Total Spending':<20} {'Avg Transaction':<20}\n")
                f.write("-" * 80 + "\n")
                for month in monthly_summary:
                    trend_indicator = ""
                    if month.get('trend'):
                        trend = month['trend']
                        if trend['direction'] == 'up':
                            trend_indicator = f" ↑ {trend['change_percent']:.1f}%"
                        elif trend['direction'] == 'down':
                            trend_indicator = f" ↓ {abs(trend['change_percent']):.1f}%"
                    
                    f.write(f"{month['month']:<12} {month['transaction_count']:<15} "
                           f"${abs(month['total_spending']):>15,.2f}  ${month['average_transaction']:>15,.2f}{trend_indicator}\n")
                f.write("\n")
                
                # Category Breakdown
                f.write("SPENDING BY CATEGORY\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'Category':<25} {'Transactions':<15} {'Total':<20} {'% of Total':<15}\n")
                f.write("-" * 80 + "\n")
                for cat in category_breakdown[:15]:  # Top 15 categories
                    f.write(f"{cat['category']:<25} {cat['transaction_count']:<15} "
                           f"${abs(cat['total_spending']):>15,.2f}  {cat['percentage']:>10.1f}%\n")
                f.write("\n")
                
                # Top Merchants
                f.write("TOP MERCHANTS BY SPENDING\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'Merchant':<30} {'Transactions':<15} {'Total Spending':<20}\n")
                f.write("-" * 80 + "\n")
                for merchant in top_merchants[:15]:  # Top 15 merchants
                    f.write(f"{merchant['merchant']:<30} {merchant['transaction_count']:<15} "
                           f"${abs(merchant['total_spending']):>15,.2f}\n")
                f.write("\n")
                
                # Spending Trends
                f.write("SPENDING TRENDS (Last 12 Months)\n")
                f.write("-" * 80 + "\n")
                f.write("Month-over-month changes:\n")
                for month in spending_trends[-6:]:  # Last 6 months
                    if month.get('trend'):
                        trend = month['trend']
                        direction_symbol = "↑" if trend['direction'] == 'up' else "↓" if trend['direction'] == 'down' else "→"
                        f.write(f"  {month['month']}: {direction_symbol} {abs(trend['change_percent']):.1f}% "
                               f"(${abs(trend['change_amount']):,.2f})\n")
                f.write("\n")
                
                f.write("=" * 80 + "\n")
                f.write("Report generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
                f.write("=" * 80 + "\n")
            
            return True
        except Exception as e:
            print(f"Error generating spending report: {e}")
            return False

