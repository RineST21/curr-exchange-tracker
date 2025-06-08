"""
Business Logic Layer - Services and API interactions
Handles external API calls, data processing, and business logic
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from models import CurrencyRatesModel

# API Configuration
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"

class NBPService:
    """Service for handling NBP API interactions"""
    
    @staticmethod
    def fetch_data_by_date_range(start_date: datetime, end_date: datetime, table: str = 'C') -> List[Tuple]:
        """Fetch NBP data for a specific date range using Table C (for bid/ask) or A (for mid)"""
        try:
            # Format dates for API
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # NBP API allows max 367 days per request, so we might need to split
            if (end_date - start_date).days > 366:
                # Split into smaller chunks
                current_start = start_date
                all_rates = []
                
                while current_start < end_date:
                    current_end = min(current_start + timedelta(days=366), end_date)
                    chunk_rates = NBPService.fetch_data_by_date_range(current_start, current_end, table)
                    if chunk_rates:
                        all_rates.extend(chunk_rates)
                    current_start = current_end + timedelta(days=1)
                
                return all_rates
                
            url = f"http://api.nbp.pl/api/exchangerates/tables/{table}/{start_str}/{end_str}/?format=json"
            print(f"Fetching data from: {url}")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            all_rates = []
            if data and isinstance(data, list):
                for day_data in data:
                    if day_data.get('rates') and day_data.get('effectiveDate'):
                        all_rates.append((day_data['rates'], day_data['effectiveDate']))
            
            return all_rates
        except requests.exceptions.RequestException as e:
            print(f"Error fetching NBP data for range {start_str} to {end_str}: {e}")
            # Try with a smaller range or return whatever we have
            if (end_date - start_date).days > 30:
                mid_date = start_date + (end_date - start_date) // 2
                first_half = NBPService.fetch_data_by_date_range(start_date, mid_date, table)
                second_half = NBPService.fetch_data_by_date_range(mid_date + timedelta(days=1), end_date, table)
                return (first_half or []) + (second_half or [])
        return []

class CryptocurrencyService:
    """Service for handling cryptocurrency API interactions"""
    
    @staticmethod
    def fetch_data(limit: int = 10) -> List[Dict]:
        """Fetch top cryptocurrencies data from CoinGecko API"""
        try:
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h,7d'
            }
            
            response = requests.get(CRYPTO_API_URL, params=params)
            response.raise_for_status()
            crypto_data = response.json()
            
            if crypto_data and isinstance(crypto_data, list):
                return crypto_data
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching cryptocurrency data: {e}")
        return []

class CurrencyDataService:
    """Service for managing currency data operations"""
    
    REQUIRED_CURRENCIES = ['USD', 'EUR', 'GBP', 'CHF']
    
    @staticmethod
    def check_and_fetch_missing_data() -> Dict:
        """Check if we have enough data and fetch only missing data if needed"""
        missing_data_found = False
        total_stored = 0
        today = datetime.now().date()
        
        for currency in CurrencyDataService.REQUIRED_CURRENCIES:
            # First check if we have any data at all for this currency
            total_count = CurrencyRatesModel.get_rates_count(currency)
            
            # Check if we have recent data (last 7 days)
            recent_count = CurrencyRatesModel.get_recent_rates_count(currency, 7)
            
            # Only fetch data if we have very little data overall (less than 50 records) 
            # OR if we have no recent data and less than 500 total records
            should_fetch = (total_count < 50) or (recent_count == 0 and total_count < 500)
            
            if should_fetch:
                print(f"Fetching data for {currency}: {total_count} total records, {recent_count} recent records")
                missing_data_found = True
                
                # Get the latest date we have for this currency
                latest_date = CurrencyRatesModel.get_latest_date(currency)
                
                if latest_date:
                    start_date = latest_date + timedelta(days=1)  # Start from day after latest
                else:
                    # If no data, start from 1 year ago instead of 5 years
                    start_date = today - timedelta(days=365)
                
                # Only fetch if there's a gap to fill
                if start_date <= today:
                    print(f"Fetching {currency} data from {start_date} to {today}")
                    historical_data = NBPService.fetch_data_by_date_range(start_date, today, 'C')
                    
                    # Store only the data for our required currency
                    for rates, effective_date in historical_data:
                        if rates and effective_date:
                            # Find the specific currency in the rates
                            currency_data = next((rate for rate in rates if rate['code'] == currency), None)
                            if currency_data:
                                if not CurrencyRatesModel.rate_exists(currency, effective_date):
                                    CurrencyRatesModel.insert_rate(
                                        currency_data['code'], 
                                        currency_data['currency'],
                                        currency_data['bid'], 
                                        currency_data['ask'], 
                                        effective_date
                                    )
                                    total_stored += 1
                    
                    CurrencyRatesModel.commit_changes()
        
        if missing_data_found:
            return {
                "message": f"Missing data detected and updated: Stored {total_stored} new records.",
                "status": "updated"
            }
        else:
            return {
                "message": "All currencies have sufficient historical data.",
                "status": "complete"
            }
    
    @staticmethod
    def check_data_needs_update() -> bool:
        """Check if data needs to be updated"""
        today = datetime.now().date()
        recent_period = today - timedelta(days=7)
        
        for currency in CurrencyDataService.REQUIRED_CURRENCIES:
            # Check if we have any data from the last 7 days
            recent_count = CurrencyRatesModel.get_recent_rates_count(currency, 7)
            
            # Also check if we have any data at all for this currency
            total_count = CurrencyRatesModel.get_rates_count(currency)
            
            # Only trigger update if we have no recent data AND less than 100 total records
            if recent_count == 0 and total_count < 100:
                print(f"Auto-checking: {currency} has no recent data ({recent_count} recent, {total_count} total), will fetch missing data")
                return True
        
        return False

class ChartDataService:
    """Service for preparing chart data"""
    
    @staticmethod
    def prepare_chart_data(rates_history: List, currency_code: str) -> Dict:
        """Prepare data for frontend charts"""
        if not rates_history:
            return {"dates": [], "mid": [], "bid": [], "ask": [], "currency": currency_code}
        
        # Prepare arrays for chart data
        dates_str = [row['date'] for row in rates_history]
        
        # Handle None values properly for chart data
        values_mid = [float(row['mid_rate']) if row['mid_rate'] is not None else None for row in rates_history]
        values_bid = [float(row['bid_rate']) if row['bid_rate'] is not None else None for row in rates_history]
        values_ask = [float(row['ask_rate']) if row['ask_rate'] is not None else None for row in rates_history]
        
        return {
            'dates': dates_str,
            'mid': values_mid,
            'bid': values_bid,
            'ask': values_ask,
            'currency': currency_code
        }
    
    @staticmethod
    def get_last_valid_value(values_list: List) -> Optional[float]:
        """Get the last valid (non-None) value from a list"""
        for v in reversed(values_list):
            if v is not None:
                return v
        return None
    
    @staticmethod
    def calculate_rate_changes(values_mid: List, values_bid: List, values_ask: List) -> Tuple[float, float, float]:
        """Calculate current rate, change, and change percentage"""
        if not values_mid and not values_bid:
            return 0, 0, 0
        
        # Get current rate
        current_rate = ChartDataService.get_last_valid_value(values_mid)
        if current_rate is None:
            # fallback to average of bid/ask
            bid = ChartDataService.get_last_valid_value(values_bid)
            ask = ChartDataService.get_last_valid_value(values_ask)
            if bid is not None and ask is not None:
                current_rate = (bid + ask) / 2
            else:
                current_rate = 0
        
        # Calculate change
        change = 0
        change_percent = 0
        data_points = len(values_mid) if values_mid else len(values_bid)
        
        if data_points > 1:
            prev_rate = None
            # Use first valid mid, else avg(bid,ask)
            for i in range(data_points-1):
                if values_mid and values_mid[i] is not None:
                    prev_rate = values_mid[i]
                    break
            
            if prev_rate is None and values_bid and values_ask:
                bid = values_bid[0] if values_bid[0] is not None else 0
                ask = values_ask[0] if values_ask[0] is not None else 0
                if bid and ask:
                    prev_rate = (bid + ask) / 2
            
            if prev_rate is not None and prev_rate != 0:
                change = current_rate - prev_rate
                change_percent = (change / prev_rate) * 100
        
        return current_rate, change, change_percent
