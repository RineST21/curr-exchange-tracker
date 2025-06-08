"""
Presentation Layer - Flask routes and user interface
Handles HTTP requests, routing, and template rendering
"""

import json
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta

# Import our custom modules
from models import DatabaseManager, CurrencyRatesModel
from services import CurrencyDataService, CryptocurrencyService, ChartDataService

app = Flask(__name__)

# Setup database teardown
@app.teardown_appcontext
def close_connection(exception):
    DatabaseManager.close_connection(exception)

@app.route('/check_and_fetch_data')
def check_and_fetch_data():
    """Check if we have enough data and fetch only missing data if needed"""
    result = CurrencyDataService.check_and_fetch_missing_data()
    return jsonify(result), 200

@app.route('/api/rates')
def api_rates():
    """Return currency rates data in JSON format"""
    # Get query parameters
    currency_code = request.args.get('currency')
    limit = request.args.get('limit', type=int, default=30)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Get rates using model
    rates = CurrencyRatesModel.get_rates_with_filters(currency_code, limit, start_date, end_date)
    
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
    crypto_data = CryptocurrencyService.fetch_data(10)
    
    if not crypto_data:
        return render_template('crypto.html', 
                             crypto_data=[],
                             error_message="Nie udało się pobrać danych o kryptowalutach")
    
    return render_template('crypto.html', crypto_data=crypto_data)

@app.route('/')
@app.route('/currencies')
def index():
    # Automatically check and fetch missing data (only if not explicitly skipped)
    init_skip = request.args.get('init', '') == 'skip'
    if not init_skip:
        # If data needs update, do it silently in background
        if CurrencyDataService.check_data_needs_update():
            try:
                CurrencyDataService.check_and_fetch_missing_data()
                print("Auto-update completed successfully")
            except Exception as e:
                print(f"Auto-update failed: {e}")
    
    # Check if we need to show initialization message
    show_init_message = False
    try:
        count = CurrencyRatesModel.get_rates_count()
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
    selected_currency = request.args.get('currency', popular_currencies[0])  # Default to first currency
    selected_period = request.args.get('period', '1month')  # Default to 1 month
    
    if selected_currency not in popular_currencies:
        selected_currency = popular_currencies[0]  # Fallback if invalid currency is provided
    
    # Define time periods
    time_periods = {
        '7days': '7 Dni',
        '1month': '1 Miesiąc', 
        '6months': '6 Miesięcy',
        '1year': '1 Rok'
    }
    
    # Calculate date filter based on selected period
    today = datetime.now().date()
    date_filter_start = None
    
    if selected_period == '7days':
        date_filter_start = today - timedelta(days=7)
    elif selected_period == '1year':
        date_filter_start = today - timedelta(days=365)
    elif selected_period == '1month':
        date_filter_start = today - timedelta(days=30)
    elif selected_period == '6months':
        date_filter_start = today - timedelta(days=180)
    
    # Fetch historical data for the selected currency with date filter
    start_date_str = date_filter_start.strftime('%Y-%m-%d') if date_filter_start else None
    rates_history = CurrencyRatesModel.get_historical_rates(selected_currency, start_date_str)

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

    # Prepare chart data using service
    chart_data = ChartDataService.prepare_chart_data(rates_history, selected_currency)
    
    # Calculate rates and changes
    current_rate, change, change_percent = ChartDataService.calculate_rate_changes(
        chart_data['mid'], chart_data['bid'], chart_data['ask']
    )
    
    # Get current bid/ask values
    current_bid = ChartDataService.get_last_valid_value(chart_data['bid'])
    current_ask = ChartDataService.get_last_valid_value(chart_data['ask'])
    
    # Prepare date info
    data_points = len(rates_history)
    if data_points > 0:
        date_range = f"Od {chart_data['dates'][0]} do {chart_data['dates'][-1]} ({data_points} punktów danych)"
    else:
        date_range = "Brak dostępnych danych dla wybranego okresu."

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
                           current_bid=current_bid,
                           current_ask=current_ask,
                           show_init_message=show_init_message)

# Application initialization and startup
def init_db():
    """Initialize database schema"""
    DatabaseManager.init_db(app)

if __name__ == '__main__':
    init_db()  # Initialize DB schema if it doesn't exist
    app.run(debug=True)
