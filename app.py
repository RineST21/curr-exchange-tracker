import sqlite3
import requests
import json
from flask import Flask, render_template, jsonify, g, request
from datetime import datetime, timedelta

app = Flask(__name__)

# Database setup
DATABASE = 'currency_rates.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Cryptocurrency API (CoinGecko - free tier)
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"

def fetch_nbp_data_by_date_range(start_date, end_date, table='C'):
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
                chunk_rates = fetch_nbp_data_by_date_range(current_start, current_end, table)
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
            first_half = fetch_nbp_data_by_date_range(start_date, mid_date, table)
            second_half = fetch_nbp_data_by_date_range(mid_date + timedelta(days=1), end_date, table)
            return (first_half or []) + (second_half or [])
    return []

def check_and_fetch_missing_data():
    """Check if we have enough data and fetch only missing data if needed"""
    db = get_db()
    cursor = db.cursor()
    
    # List of currencies we want to maintain
    required_currencies = ['USD', 'EUR', 'GBP', 'CHF']
    
    # Check data availability for each currency
    today = datetime.now().date()
    
    missing_data_found = False
    total_stored = 0
    
    for currency in required_currencies:
        # First check if we have any data at all for this currency
        cursor.execute("""
            SELECT COUNT(*) FROM rates 
            WHERE currency_code = ?
        """, (currency,))
        total_count = cursor.fetchone()[0]
        
        # Check if we have recent data (last 7 days)
        recent_period = today - timedelta(days=7)
        cursor.execute("""
            SELECT COUNT(*) FROM rates 
            WHERE currency_code = ? AND date >= ?
        """, (currency, recent_period.strftime('%Y-%m-%d')))
        recent_count = cursor.fetchone()[0]
        
        # Only fetch data if we have very little data overall (less than 50 records) 
        # OR if we have no recent data and less than 500 total records
        should_fetch = (total_count < 50) or (recent_count == 0 and total_count < 500)
        
        if should_fetch:
            print(f"Fetching data for {currency}: {total_count} total records, {recent_count} recent records")
            missing_data_found = True
            
            # Get the latest date we have for this currency
            cursor.execute("""
                SELECT MAX(date) FROM rates WHERE currency_code = ?
            """, (currency,))
            latest_date_row = cursor.fetchone()
            
            if latest_date_row and latest_date_row[0]:
                latest_date = datetime.strptime(latest_date_row[0], '%Y-%m-%d').date()
                start_date = latest_date + timedelta(days=1)  # Start from day after latest
            else:
                # If no data, start from 1 year ago instead of 5 years
                start_date = today - timedelta(days=365)
            
            # Only fetch if there's a gap to fill
            if start_date <= today:
                print(f"Fetching {currency} data from {start_date} to {today}")
                historical_data = fetch_nbp_data_by_date_range(start_date, today, 'C')
                
                # Store only the data for our required currency
                for rates, effective_date in historical_data:
                    if rates and effective_date:
                        # Find the specific currency in the rates
                        currency_data = next((rate for rate in rates if rate['code'] == currency), None)
                        if currency_data:
                            cursor.execute("SELECT 1 FROM rates WHERE currency_code = ? AND date = ? LIMIT 1", 
                                         (currency, effective_date))
                            if not cursor.fetchone():
                                cursor.execute('''
                                    INSERT INTO rates (currency_code, currency_name, mid_rate, bid_rate, ask_rate, date)
                                    VALUES (?, ?, NULL, ?, ?, ?)
                                ''', (currency_data['code'], currency_data['currency'], 
                                     currency_data['bid'], currency_data['ask'], effective_date))
                                total_stored += 1
                
                db.commit()
    
    if missing_data_found:
        return jsonify({
            "message": f"Missing data detected and updated: Stored {total_stored} new records.",
            "status": "updated"
        }), 200
    else:
        return jsonify({
            "message": "All currencies have sufficient historical data.",
            "status": "complete"
        }), 200

@app.route('/check_and_fetch_data')
def check_and_fetch_data():
    """Check if we have enough data and fetch only missing data if needed"""
    return check_and_fetch_missing_data()

@app.route('/api/rates')
def api_rates():
    """Return currency rates data in JSON format"""
    db = get_db()
    cursor = db.cursor()
    
    # Get query parameters
    currency_code = request.args.get('currency')
    limit = request.args.get('limit', type=int, default=30)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build query
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
    rates = cursor.fetchall()
    
    # Convert to list of dictionaries
    rates_list = []
    for rate in rates:
        rates_list.append({
            'id': rate['id'] if 'id' in rate.keys() else None,
            'currency_code': rate['currency_code'],
            'currency_name': rate['currency_name'],
            'mid_rate': rate['mid_rate'],
            'bid_rate': rate['bid_rate'],
            'ask_rate': rate['ask_rate'],
            'date': rate['date']
        })
    
    return jsonify({
        'status': 'success',
        'count': len(rates_list),
        'data': rates_list
    })

@app.route('/cryptocurrencies')
def cryptocurrencies():
    """Display top cryptocurrencies"""
    crypto_data = fetch_cryptocurrency_data(10)
    
    if not crypto_data:
        return render_template('crypto.html', 
                             crypto_data=[],
                             error_message="Nie udało się pobrać danych o kryptowalutach")
    
    return render_template('crypto.html', crypto_data=crypto_data)

@app.route('/')
@app.route('/currencies')
def index():
    db = get_db()
    cursor = db.cursor()
      # Automatically check and fetch missing data (only if not explicitly skipped)
    init_skip = request.args.get('init', '') == 'skip'
    if not init_skip:
        # Check if we have recent data for each required currency
        required_currencies = ['USD', 'EUR', 'GBP', 'CHF']
        today = datetime.now().date()
        recent_period = today - timedelta(days=7)  # Check only last 7 days instead of 5 years
        
        data_needs_update = False
        for currency in required_currencies:
            # Check if we have any data from the last 7 days
            cursor.execute("""
                SELECT COUNT(*) FROM rates 
                WHERE currency_code = ? AND date >= ?
            """, (currency, recent_period.strftime('%Y-%m-%d')))
            recent_count = cursor.fetchone()[0]
            
            # Also check if we have any data at all for this currency
            cursor.execute("""
                SELECT COUNT(*) FROM rates 
                WHERE currency_code = ?
            """, (currency,))
            total_count = cursor.fetchone()[0]
            
            # Only trigger update if we have no recent data AND less than 100 total records
            if recent_count == 0 and total_count < 100:
                data_needs_update = True
                print(f"Auto-checking: {currency} has no recent data ({recent_count} recent, {total_count} total), will fetch missing data")
                break
        
        # If data needs update, do it silently in background
        if data_needs_update:
            try:
                check_and_fetch_missing_data()
                print("Auto-update completed successfully")
            except Exception as e:
                print(f"Auto-update failed: {e}")
      # Check if we need to show initialization message
    show_init_message = False
    try:
        cursor.execute("SELECT COUNT(*) FROM rates")
        result = cursor.fetchone()
        count = result[0] if result else 0
        
        if count < 10:  # If almost no data, show a message
            show_init_message = True
    except Exception as e:
        print(f"Error checking database: {e}")
        show_init_message = True
        count = 0
    
    # Check for initialization status from query parameter (already handled above)
    if init_skip:
        show_init_message = False  # Hide initialization message if explicitly skipped

    popular_currencies = ('USD', 'EUR', 'GBP', 'CHF')
    selected_currency = request.args.get('currency', popular_currencies[0]) # Default to first currency
    selected_period = request.args.get('period', '1month')  # Default to 1 month
    
    if selected_currency not in popular_currencies:
        selected_currency = popular_currencies[0] # Fallback if invalid currency is provided    # Define time periods
    time_periods = {
        '7days': '7 Dni',
        '1month': '1 Miesiąc', 
        '6months': '6 Miesięcy',
        '1year': '1 Rok'
    }
      # Calculate date filter based on selected period
    today = datetime.now().date()
    date_filter_start = None
    date_filter_end = today

    if selected_period == '7days':
        date_filter_start = today - timedelta(days=7)
    elif selected_period == '1year':
        date_filter_start = today - timedelta(days=365)
    elif selected_period == '1month':
        date_filter_start = today - timedelta(days=30)
    elif selected_period == '6months':
        date_filter_start = today - timedelta(days=180)
      # Fetch historical data for the selected currency with date filter
    query_params = [selected_currency]
    sql_query = f"""
        SELECT date, mid_rate, bid_rate, ask_rate FROM rates
        WHERE currency_code = ?
    """
    if date_filter_start:
        sql_query += " AND date >= ?"
        query_params.append(date_filter_start.strftime('%Y-%m-%d'))
    
    sql_query += " ORDER BY date ASC"
    
    cursor.execute(sql_query, tuple(query_params))
    rates_history = cursor.fetchall()    # Fetch the first rate of the period for change calculation
    first_rate_of_period = None
    if rates_history and date_filter_start:
        cursor.execute("""
            SELECT mid_rate FROM rates
            WHERE currency_code = ? AND date = (
                SELECT MIN(date) FROM rates WHERE currency_code = ? AND date >= ?
            )        """, (selected_currency, selected_currency, date_filter_start.strftime('%Y-%m-%d')))
        first_rate_row = cursor.fetchone()
        if first_rate_row:
            first_rate_of_period = first_rate_row['mid_rate']

    if not rates_history:
        return render_template('index.html',
                               chart_data=json.dumps({"dates": [], "mid": [], "bid": [], "ask": []}),
                               date_info=f"Brak danych historycznych dla {selected_currency} w wybranym okresie.",
                               popular_currencies=popular_currencies,
                               selected_currency=selected_currency,
                               time_periods=time_periods,
                               selected_period=selected_period,
                               show_init_message=True,
                               error_message=f"Nie znaleziono danych dla {selected_currency} w wybranym okresie czasu.")

    # Prepare arrays for chart data
    dates_str = [row['date'] for row in rates_history]
    
    # Handle None values properly for chart data
    values_mid = [float(row['mid_rate']) if row['mid_rate'] is not None else None for row in rates_history]
    values_bid = [float(row['bid_rate']) if row['bid_rate'] is not None else None for row in rates_history]
    values_ask = [float(row['ask_rate']) if row['ask_rate'] is not None else None for row in rates_history]

    # Prepare data for Plotly.js, ensuring we have valid arrays
    chart_data = {
        'dates': dates_str,
        'mid': values_mid,
        'bid': values_bid,
        'ask': values_ask,
        'currency': selected_currency
    }

    # Remove matplotlib plot generation and all references to 'values', 'dates_dt', etc.
    # Use only chart_data for frontend interactive chart.

    # For summary info, prefer mid if available, else bid/ask average
    def get_last_valid(lst):
        for v in reversed(lst):
            if v is not None:
                return v
        return None
    data_points = len(rates_history)
    current_rate = get_last_valid(values_mid)
    if current_rate is None:
        # fallback to average of bid/ask
        bid = get_last_valid(values_bid)
        ask = get_last_valid(values_ask)
        if bid is not None and ask is not None:
            current_rate = (bid + ask) / 2
        else:
            current_rate = 0    # Calculate change and change_percent based on mid, else bid/ask
    change = 0
    change_percent = 0
    if data_points > 1:
        prev_rate = None
        # Use first valid mid, else avg(bid,ask)
        for i in range(data_points-1):
            if values_mid[i] is not None:
                prev_rate = values_mid[i]
                break
        if prev_rate is None:
            bid = values_bid[0]
            ask = values_ask[0]
            if bid is not None and ask is not None:
                prev_rate = (bid + ask) / 2
        if prev_rate is not None and prev_rate != 0:
            change = current_rate - prev_rate
            change_percent = (change / prev_rate) * 100

    if data_points > 0:
        date_range = f"Od {dates_str[0]} do {dates_str[-1]} ({data_points} punktów danych)"
    else:
        date_range = "Brak dostępnych danych dla wybranego okresu."
        current_rate = 0

    return render_template('index.html',
                           chart_data=json.dumps(chart_data),
                           date_info=date_range,
                           popular_currencies=popular_currencies,
                           selected_currency=selected_currency,
                           time_periods=time_periods,
                           selected_period=selected_period,
                           current_rate=current_rate,
                           change=change,
                           change_percent=change_percent,
                           current_bid=get_last_valid(values_bid),
                           current_ask=get_last_valid(values_ask),
                           show_init_message=show_init_message)

def fetch_cryptocurrency_data(limit=10):
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

# Placeholder for gunicorn or other WSGI server in production
# from flask import g

if __name__ == '__main__':
    # from flask import g # Removed g import from here
    init_db() # Initialize DB schema if it doesn't exist
    app.run(debug=True)
