# Currency Exchange Rate Tracker Application

An advanced Flask web application for monitoring and analyzing currency exchange rates from the National Bank of Poland (NBP) API. The application allows tracking historical exchange rates with interactive charts and automatic data management.

## Main Features

- **Data retrieval from NBP API**: Automatic download of current and historical exchange rates
- **Support for NBP tables A and C**:
  - Table A: average exchange rates
  - Table C: buy and sell rates (bid/ask)
- **Interactive charts**: Dynamic charts using Plotly.js
- **Selection of time periods**: 7 days, 1 month, 6 months, 1 year, all data
- **Automatic data management**: Intelligent checking and downloading of missing data
- **Support for popular currencies**: USD, EUR, GBP, CHF
- **Responsive interface**: Modern design adapted to mobile devices
- **Storage in SQLite**: Efficient storage of historical data

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

## Project Structure

```
├── app.py                 # Main Flask application file
├── schema.sql            # SQLite database schema
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation (Polish)
├── README_eng.md        # Project documentation (English)
├── check_db.py          # Script to check database content
├── debug_check.py       # Helper file for debugging
├── currency_rates.db    # SQLite database (created automatically)
└── templates/
    └── index.html       # HTML template with interactive interface
```

## Available API Endpoints

- `/` - Main page with currency exchange rate charts
- `/update_rates` - Update average exchange rates (NBP table A)
- `/update_rates_bid_ask` - Update buy/sell rates (NBP table C)
- `/update_historical_rates` - Download historical data (last 30 days)
- `/update_historical_rates_bid_ask` - Download historical bid/ask rates
- `/check_and_fetch_data` - Check and download missing data

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
