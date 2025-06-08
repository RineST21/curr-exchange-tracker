"""
Data Layer - Database models and operations
Handles all database interactions and data persistence
"""

import sqlite3
from flask import g
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

# Database configuration
DATABASE = 'currency_rates.db'

class DatabaseManager:
    """Handles database connections and operations"""
    
    @staticmethod
    def get_db():
        """Get database connection with row factory"""
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect(DATABASE)
            db.row_factory = sqlite3.Row
        return db
    
    @staticmethod
    def close_connection(exception):
        """Close database connection"""
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()
    
    @staticmethod
    def init_db(app):
        """Initialize database schema"""
        with app.app_context():
            db = DatabaseManager.get_db()
            with app.open_resource('schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()

class CurrencyRatesModel:
    """Model for currency rates data operations"""
    
    @staticmethod
    def get_rates_count(currency_code: str = None) -> int:
        """Get total count of rates for a currency"""
        db = DatabaseManager.get_db()
        cursor = db.cursor()
        
        if currency_code:
            cursor.execute("SELECT COUNT(*) FROM rates WHERE currency_code = ?", (currency_code,))
        else:
            cursor.execute("SELECT COUNT(*) FROM rates")
        
        result = cursor.fetchone()
        return result[0] if result else 0
    
    @staticmethod
    def get_recent_rates_count(currency_code: str, days: int = 7) -> int:
        """Get count of recent rates for a currency"""
        db = DatabaseManager.get_db()
        cursor = db.cursor()
        
        recent_period = (datetime.now().date() - timedelta(days=days)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) FROM rates 
            WHERE currency_code = ? AND date >= ?
        """, (currency_code, recent_period))
        
        result = cursor.fetchone()
        return result[0] if result else 0
    
    @staticmethod
    def get_latest_date(currency_code: str) -> Optional[datetime]:
        """Get the latest date for a currency"""
        db = DatabaseManager.get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT MAX(date) FROM rates WHERE currency_code = ?
        """, (currency_code,))
        
        latest_date_row = cursor.fetchone()
        if latest_date_row and latest_date_row[0]:
            return datetime.strptime(latest_date_row[0], '%Y-%m-%d').date()
        return None
    
    @staticmethod
    def rate_exists(currency_code: str, date: str) -> bool:
        """Check if rate exists for given currency and date"""
        db = DatabaseManager.get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT 1 FROM rates WHERE currency_code = ? AND date = ? LIMIT 1
        """, (currency_code, date))
        
        return cursor.fetchone() is not None
    
    @staticmethod
    def insert_rate(currency_code: str, currency_name: str, bid_rate: float, ask_rate: float, date: str) -> None:
        """Insert a new currency rate"""
        db = DatabaseManager.get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT INTO rates (currency_code, currency_name, mid_rate, bid_rate, ask_rate, date)
            VALUES (?, ?, NULL, ?, ?, ?)
        ''', (currency_code, currency_name, bid_rate, ask_rate, date))
    
    @staticmethod
    def get_rates_with_filters(currency_code: str = None, limit: int = 30, 
                              start_date: str = None, end_date: str = None) -> List[sqlite3.Row]:
        """Get rates with optional filters"""
        db = DatabaseManager.get_db()
        cursor = db.cursor()
        
        query = "SELECT * FROM rates WHERE 1=1"
        params = []
        
        if currency_code:
            query += " AND currency_code = ?"
            params.append(currency_code.upper())
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        return cursor.fetchall()
    
    @staticmethod
    def get_historical_rates(currency_code: str, start_date: str = None) -> List[sqlite3.Row]:
        """Get historical rates for a currency"""
        db = DatabaseManager.get_db()
        cursor = db.cursor()
        
        query_params = [currency_code]
        sql_query = """
            SELECT date, mid_rate, bid_rate, ask_rate FROM rates
            WHERE currency_code = ?
        """
        
        if start_date:
            sql_query += " AND date >= ?"
            query_params.append(start_date)
        
        sql_query += " ORDER BY date ASC"
        
        cursor.execute(sql_query, tuple(query_params))
        return cursor.fetchall()
    
    @staticmethod
    def get_first_rate_of_period(currency_code: str, start_date: str) -> Optional[float]:
        """Get the first rate of a specific period"""
        db = DatabaseManager.get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT mid_rate FROM rates
            WHERE currency_code = ? AND date = (
                SELECT MIN(date) FROM rates WHERE currency_code = ? AND date >= ?
            )
        """, (currency_code, currency_code, start_date))
        
        first_rate_row = cursor.fetchone()
        if first_rate_row:
            return first_rate_row['mid_rate']
        return None
    
    @staticmethod
    def commit_changes():
        """Commit database changes"""
        db = DatabaseManager.get_db()
        db.commit()
