# Currency Exchange Rate Tracker

An advanced Flask web application for monitoring and analyzing currency exchange rates from the National Bank of Poland (NBP) API. The application allows tracking historical exchange rates with interactive charts and automatic data management.

## Features

- **Currency Exchange Rates** - Monitor PLN exchange rates with interactive charts
- **Cryptocurrency Tracking** - View top 10 cryptocurrencies with real-time market data
- **Multiple Data Sources**:
  - NBP API: Polish National Bank for currency exchange rates (Tables A and C)
  - CoinGecko API: Cryptocurrency market data
- **Interactive Navigation** - Easy switching between currencies and cryptocurrencies
- **JSON API Endpoints** - RESTful API for accessing stored currency data
- **Responsive Design** - Modern UI optimized for desktop and mobile devices
- **Automatic Data Management** - Smart fetching and storage of missing historical data
- **Time Period Selection** - 7 days, 1 month, 6 months, 1 year, or all available data
- **External CSS Styling** - Clean, maintainable code architecture

## Installation

### Requirements

- Python 3.7+
- pip (Python package manager)

### Setup

1. **Clone the repository or download the project files**

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   ```bash
   # Windows
   .\venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```
   
   The server will start at `http://127.0.0.1:5000/`

6. **Data initialization:**
   - The database (`currency_rates.db`) will be created automatically
   - The application will automatically check and download missing data on first run
   - You can also manually update data using the appropriate endpoints

## API Documentation

### Web Interface

- **`/` or `/currencies`** - Main currency exchange rates dashboard
- **`/cryptocurrencies`** - Top 10 cryptocurrencies with market data

### REST API Endpoints

#### Get Currency Rates
```
GET /api/rates
```

**Query Parameters:**
- `currency` - Filter by currency code (e.g., USD, EUR)
- `limit` - Maximum number of records (default: 30)
- `start_date` - Filter from date (YYYY-MM-DD format)
- `end_date` - Filter to date (YYYY-MM-DD format)

**Example:**
```
GET /api/rates?currency=USD&limit=10
```

#### Manual Data Update
```
GET /check_and_fetch_data
```

### Data Sources

- **NBP API** - Polish National Bank exchange rates
  - Table A: Average exchange rates
  - Table C: Bid/Ask rates for buying and selling
- **CoinGecko API** - Cryptocurrency market data (free tier)

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

## Technology Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML5, CSS3, JavaScript
- **Charts:** Plotly.js
- **Database:** SQLite
- **APIs:** NBP Web API, CoinGecko API
- **Styling:** CSS with responsive design

## NBP API Integration

The application uses the official [NBP Web API](http://api.nbp.pl/):

- **Table A** - Average exchange rates of foreign currencies
- **Table C** - Buy and sell rates of foreign currencies

The NBP API is free and does not require an access key. It provides current and historical exchange rates against PLN.

## Configuration

### Changing Displayed Currencies

Edit the `popular_currencies` variable in the `index()` function in `app.py`:

```python
popular_currencies = ('USD', 'EUR', 'GBP', 'CHF', 'JPY') 
```

### Modifying Time Periods

Modify the `time_periods` dictionary in the `index()` function:

```python
time_periods = {
    '7days': '7 Days',
    '1month': '1 Month', 
    '3months': '3 Months', 
    '6months': '6 Months',
    '1year': '1 Year',
}
```

### Customizing Interface

Modify the CSS in `static/style.css` or HTML templates in the `templates/` directory.

## Advanced Features

- **Automatic Data Management** - The application checks data availability and automatically downloads missing information
- **Large Date Range Handling** - Intelligent splitting of API queries into smaller parts
- **Error Handling** - Safeguards against API and database errors
- **Responsive Design** - Interface adapted to different screen sizes

## Troubleshooting

### No Data After Startup

The application will automatically download data on first run. If not, manually trigger:

```
http://127.0.0.1:5000/check_and_fetch_data
```

### API Connection Errors

- Check your internet connection
- Verify NBP API availability at: http://api.nbp.pl/

### Database Issues

Delete the `currency_rates.db` file - it will be recreated on the next startup.

## License

This project uses data from the public NBP API in accordance with NBP regulations.
