import sqlite3

conn = sqlite3.connect('currency_rates.db')
cursor = conn.cursor()

# Updated currency list - JPY removed
currencies = ['USD', 'EUR', 'GBP', 'CHF']
for curr in currencies:
    cursor.execute('SELECT COUNT(*) FROM rates WHERE currency_code = ?', (curr,))
    count = cursor.fetchone()[0]
    print(f'{curr}: {count} records')

# Check all available currencies
cursor.execute('SELECT DISTINCT currency_code FROM rates ORDER BY currency_code')
all_currencies = cursor.fetchall()
print(f'\nAll available currencies: {[c[0] for c in all_currencies]}')

conn.close()
