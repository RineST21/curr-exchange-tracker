# Currency Exchange Rate Tracker Application

An advanced Flask web application for monitoring and analyzing currency exchange rates from the National Bank of Poland (NBP) API. The application allows tracking historical exchange rates with interactive charts and automatic data management.

## Main Features

- **Currency Exchange Rates**: Monitor PLN exchange rates with interactive charts
- **Cryptocurrency Tracking**: View top 10 cryptocurrencies with real-time market data
- **Multiple Data Sources**:
  - NBP API: Polish National Bank for currency exchange rates (Tables A and C)
  - CoinGecko API: Cryptocurrency market data
- **Interactive Navigation**: Easy switching between currencies and cryptocurrencies
- **JSON API Endpoints**: RESTful API for accessing stored currency data
- **Responsive Design**: Modern UI optimized for desktop and mobile devices
- **Automatic Data Management**: Smart fetching and storage of missing historical data
- **Time Period Selection**: 7 days, 1 month, 6 months, 1 year, or all available data
- **External CSS Styling**: Clean, maintainable code architecture

## Installation and Startup

### Requirements
- Python 3.7+
- pip (Python package manager)

### Installation Steps

1. **Clone the repository or download the project files**

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```
   The server will start at `http://127.0.0.1:5000/`

5. **Data initialization:**
   - The database (`currency_rates.db`) will be created automatically
   - The application will automatically check and download missing data on first run
   - You can also manually update data using the appropriate endpoints

## Available Endpoints

The application provides several web endpoints and API routes:

### Web Interface
- **`/` or `/currencies`** - Main currency exchange rates dashboard
- **`/cryptocurrencies`** - Top 10 cryptocurrencies with market data

### API Endpoints
- **`/api/rates`** - JSON API for currency data with filtering options
  - Query parameters:
    - `currency` - Filter by currency code (e.g., USD, EUR)
    - `limit` - Maximum number of records (default: 30)
    - `start_date` - Filter from date (YYYY-MM-DD format)
    - `end_date` - Filter to date (YYYY-MM-DD format)
  - Example: `/api/rates?currency=USD&limit=10`

- **`/check_and_fetch_data`** - Manually trigger data update

### API Data Sources
- **NBP API**: Polish National Bank exchange rates
  - Table A: Average exchange rates
  - Table C: Bid/Ask rates for buying and selling
- **CoinGecko API**: Cryptocurrency market data (free tier)

## Project Structure

```
curr-exchange-tracker/
├── app.py                # Main Flask application
├── schema.sql            # Database schema
├── requirements.txt      # Python dependencies
├── currency_rates.db     # SQLite database (auto-created)
├── static/
│   └── style.css         # External CSS styles
├── templates/
│   ├── index.html        # Currency exchange rates page
│   └── crypto.html       # Cryptocurrency page
├── README.md             # Polish documentation
└── README_eng.md         # English documentation
```

## Supported Currencies

The application supports all currencies available in the NBP API, with a default focus on:
- **USD** - US Dollar
- **EUR** - Euro
- **GBP** - British Pound
- **CHF** - Swiss Franc

## Technologies

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Charts**: Plotly.js
- **Database**: SQLite
- **API**: NBP Web API
- **Styling**: CSS with responsive design

## National Bank of Poland API

The application uses the official [NBP Web API](http://api.nbp.pl/):
- **Table A**: Average exchange rates of foreign currencies
- **Table C**: Buy and sell rates of foreign currencies

The NBP API is free and does not require an access key. It provides current and historical exchange rates against PLN.

## Configuration and Customization

### Changing displayed currencies
Edit the `popular_currencies` variable in the `index()` function in `app.py`:
```python
popular_currencies = ('USD', 'EUR', 'GBP', 'CHF', 'JPY')  # Add more currencies
```

### Changing time periods
Modify the `time_periods` dictionary in the `index()` function:
```python
time_periods = {
    '7days': '7 Days',
    '1month': '1 Month', 
    '3months': '3 Months',  # New period
    '6months': '6 Months',
    '1year': '1 Year',
    'all': 'All data'
}
```

### Interface styling
Modify the `templates/index.html` file to customize the application's appearance.

## Advanced Features

- **Automatic data management**: The application checks data availability and automatically downloads missing information
- **Handling large date ranges**: Intelligent splitting of API queries into smaller parts
- **Error handling**: Safeguards against API and database errors
- **Responsive design**: Interface adapted to different screen sizes

## Troubleshooting

### No data after startup
The application will automatically download data on first run. If not, use:
```
http://127.0.0.1:5000/check_and_fetch_data
```

### API connection errors
Check your internet connection and the availability of the NBP API at: http://api.nbp.pl/

### Database problems
Delete the `currency_rates.db` file - it will be recreated on the next startup.

## License

The project uses data from the public NBP API in accordance with NBP regulations.
