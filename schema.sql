DROP TABLE IF EXISTS rates;

CREATE TABLE rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    currency_code TEXT NOT NULL,
    currency_name TEXT NOT NULL,
    mid_rate REAL,
    bid_rate REAL,
    ask_rate REAL,
    date TEXT NOT NULL,
    UNIQUE(currency_code, date)
);
