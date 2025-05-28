import sqlite3
import requests
import json
from flask import Flask, render_template, jsonify, g, request # Added request
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web applications
import matplotlib.pyplot as plt
import matplotlib.dates as mdates # For formatting dates on the plot
import io
import base64

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

# API for currency rates (example: NBP API - Polish National Bank)
# Please replace with a more general public API if needed, as NBP provides mainly PLN exchange rates.
# For a wider range of currencies, consider APIs like exchangerate-api.com or openexchangerates.org (may require API key)
NBP_API_URL = "http://api.nbp.pl/api/exchangerates/tables/A/?format=json"
NBP_HISTORICAL_URL = "http://api.nbp.pl/api/exchangerates/tables/A/last/30/?format=json"  # Last 30 days

# NBP Table C for bid/ask rates
NBP_API_URL_C = "http://api.nbp.pl/api/exchangerates/tables/C/?format=json"
NBP_HISTORICAL_URL_C = "http://api.nbp.pl/api/exchangerates/tables/C/last/30/?format=json"

def fetch_currency_rates():
    try:
        response = requests.get(NBP_API_URL)
        response.raise_for_status()  # Raise an exception for HTTP errors
        rates_data = response.json()
        if rates_data and isinstance(rates_data, list) and rates_data[0].get('rates'):
            return rates_data[0]['rates'], rates_data[0].get('effectiveDate')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching currency rates: {e}")
    return None, None

def fetch_currency_rates_with_bid_ask():
    try:
        response = requests.get(NBP_API_URL_C)
        response.raise_for_status()
        rates_data = response.json()
        if rates_data and isinstance(rates_data, list) and rates_data[0].get('rates'):
            return rates_data[0]['rates'], rates_data[0].get('effectiveDate')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching currency rates (Table C): {e}")
    return None, None

def fetch_historical_currency_rates(days=30):
    """Fetch historical currency rates for the last 'days' days"""
    try:
        url = f"http://api.nbp.pl/api/exchangerates/tables/A/last/{days}/?format=json"
        response = requests.get(url)
        response.raise_for_status()
        historical_data = response.json()
        
        all_rates = []
        if historical_data and isinstance(historical_data, list):
            for day_data in historical_data:
                if day_data.get('rates') and day_data.get('effectiveDate'):
                    all_rates.append((day_data['rates'], day_data['effectiveDate']))
        
        return all_rates
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical currency rates: {e}")
    return []

def fetch_historical_currency_rates_with_bid_ask(days=30):
    try:
        url = f"http://api.nbp.pl/api/exchangerates/tables/C/last/{days}/?format=json"
        response = requests.get(url)
        response.raise_for_status()
        historical_data = response.json()
        all_rates = []
        if historical_data and isinstance(historical_data, list):
            for day_data in historical_data:
                if day_data.get('rates') and day_data.get('effectiveDate'):
                    all_rates.append((day_data['rates'], day_data['effectiveDate']))
        return all_rates
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical currency rates (Table C): {e}")
    return []

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

def store_rates(rates, effective_date):
    if not rates or not effective_date:
        return

    db = get_db()
    cursor = db.cursor()
    # Check if data for this date already exists
    cursor.execute("SELECT 1 FROM rates WHERE date = ?", (effective_date,))
    if cursor.fetchone():
        print(f"Data for {effective_date} already exists. Skipping insertion.")
        return

    for rate in rates:
        try:
            cursor.execute('''
                INSERT INTO rates (currency_code, currency_name, mid_rate, date)
                VALUES (?, ?, ?, ?)
            ''', (rate['code'], rate['currency'], rate['mid'], effective_date))
        except sqlite3.IntegrityError:
            print(f"Record for {rate['code']} on {effective_date} might already exist or other integrity constraint failed.")
        except KeyError as e:
            print(f"Missing key in rate data: {e} - Data: {rate}")

    db.commit()
    print(f"Successfully stored rates for {effective_date}")

def store_rates_bid_ask(rates, effective_date):
    if not rates or not effective_date:
        return
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT 1 FROM rates WHERE date = ?", (effective_date,))
    if cursor.fetchone():
        print(f"Data for {effective_date} already exists. Skipping insertion.")
        return
    for rate in rates:
        try:
            cursor.execute('''
                INSERT INTO rates (currency_code, currency_name, mid_rate, bid_rate, ask_rate, date)
                VALUES (?, ?, NULL, ?, ?, ?)
            ''', (rate['code'], rate['currency'], rate['bid'], rate['ask'], effective_date))
        except sqlite3.IntegrityError:
            print(f"Record for {rate['code']} on {effective_date} might already exist or other integrity constraint failed.")
        except KeyError as e:
            print(f"Missing key in rate data: {e} - Data: {rate}")
    db.commit()
    print(f"Successfully stored bid/ask rates for {effective_date}")

@app.route('/update_rates')
def update_rates_route():
    rates, effective_date = fetch_currency_rates()
    if rates and effective_date:
        store_rates(rates, effective_date)
        return jsonify({"message": "Rates updated successfully for " + effective_date}), 200
    return jsonify({"message": "Failed to fetch or store rates"}), 500

@app.route('/update_rates_bid_ask')
def update_rates_bid_ask_route():
    rates, effective_date = fetch_currency_rates_with_bid_ask()
    if rates and effective_date:
        store_rates_bid_ask(rates, effective_date)
        return jsonify({"message": "Bid/Ask rates updated successfully for " + effective_date}), 200
    return jsonify({"message": "Failed to fetch or store bid/ask rates"}), 500

@app.route('/update_historical_rates')
def update_historical_rates_route():
    """Update with historical data from the last 30 days"""
    historical_data = fetch_historical_currency_rates(30)
    
    if not historical_data:
        return jsonify({"message": "Failed to fetch historical rates"}), 500
    
    stored_count = 0
    for rates, effective_date in historical_data:
        if rates and effective_date:
            # Check if data already exists before storing
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT 1 FROM rates WHERE date = ? LIMIT 1", (effective_date,))
            if not cursor.fetchone():
                store_rates(rates, effective_date)
                stored_count += 1
    
    return jsonify({
        "message": f"Historical rates updated successfully. Stored {stored_count} new days of data.",
        "total_days_processed": len(historical_data)
    }), 200

@app.route('/update_historical_rates_bid_ask')
def update_historical_rates_bid_ask_route():
    days = request.args.get('days', default=30, type=int)
    historical_data = fetch_historical_currency_rates_with_bid_ask(days)
    if not historical_data:
        return jsonify({"message": "Failed to fetch historical bid/ask rates"}), 500
    stored_count = 0
    for rates, effective_date in historical_data:
        if rates and effective_date:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT 1 FROM rates WHERE date = ? LIMIT 1", (effective_date,))
            if not cursor.fetchone():
                store_rates_bid_ask(rates, effective_date)
                stored_count += 1
    return jsonify({
        "message": f"Historical bid/ask rates updated successfully. Stored {stored_count} new days of data.",
        "total_days_processed": len(historical_data)
    }), 200

def check_and_fetch_missing_data():
    """Check if we have enough data and fetch only missing data if needed"""
    db = get_db()
    cursor = db.cursor()
    
    # List of currencies we want to maintain
    required_currencies = ['USD', 'EUR', 'GBP', 'CHF']
    
    # Check data availability for each currency
    today = datetime.now().date()
    five_years_ago = today - timedelta(days=5*365)
    
    missing_data_found = False
    total_stored = 0
    
    for currency in required_currencies:
        # Check if we have recent data for this currency
        cursor.execute("""
            SELECT COUNT(*) FROM rates 
            WHERE currency_code = ? AND date >= ?
        """, (currency, five_years_ago.strftime('%Y-%m-%d')))
        count = cursor.fetchone()[0]
        
        if count < 30:  # If we have less than 30 days of data
            print(f"Insufficient data for {currency}: {count} records. Fetching missing data...")
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
                start_date = five_years_ago  # If no data, start from 5 years ago
            
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

@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    
    # Automatically check and fetch missing data (only if not explicitly skipped)
    init_skip = request.args.get('init', '') == 'skip'
    if not init_skip:
        # Check if we have sufficient data for each required currency
        required_currencies = ['USD', 'EUR', 'GBP', 'CHF']
        today = datetime.now().date()
        five_years_ago = today - timedelta(days=5*365)
        
        data_needs_update = False
        for currency in required_currencies:
            cursor.execute("""
                SELECT COUNT(*) FROM rates 
                WHERE currency_code = ? AND date >= ?
            """, (currency, five_years_ago.strftime('%Y-%m-%d')))
            count = cursor.fetchone()[0]
            
            if count < 30:  # If we have less than 30 days of recent data
                data_needs_update = True
                print(f"Auto-checking: {currency} has only {count} recent records, will fetch missing data")
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
        selected_currency = popular_currencies[0] # Fallback if invalid currency is provided
    
    # Define time periods
    time_periods = {
        '7days': '7 Dni',
        '1month': '1 Miesiąc', 
        '6months': '6 Miesięcy',
        '1year': '1 Rok',        'all': 'Wszystkie dane'
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
    elif selected_period == 'all':
        date_filter_start = None  # No date filter for all data
    
    # Fetch historical data for the selected currency with date filter
    query_params = [selected_currency]
    sql_query = f"""
        SELECT date, mid_rate, bid_rate, ask_rate FROM rates
        WHERE currency_code = ?
    """
    if date_filter_start and selected_period != 'all':
        sql_query += " AND date >= ?"
        query_params.append(date_filter_start.strftime('%Y-%m-%d'))
    
    sql_query += " ORDER BY date ASC"
    
    cursor.execute(sql_query, tuple(query_params))
    rates_history = cursor.fetchall()

    # Fetch the first rate of the period for change calculation if not 'all'
    first_rate_of_period = None
    if rates_history and selected_period != 'all' and date_filter_start:
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

# Placeholder for gunicorn or other WSGI server in production
# from flask import g

if __name__ == '__main__':
    # from flask import g # Removed g import from here
    init_db() # Initialize DB schema if it doesn't exist
    app.run(debug=True)
