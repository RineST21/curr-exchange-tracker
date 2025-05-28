# Aplikacja Kursów Walut - Currency Exchange Rate Tracker

Zaawansowana aplikacja webowa Flask do monitorowania i analizowania kursów walut z API Narodowego Banku Polskiego (NBP). Aplikacja pozwala na śledzenie historycznych kursów walut z interaktywnymi wykresami i automatycznym zarządzaniem danymi.

## Główne Funkcjonalności

- **Pobieranie danych z API NBP**: Automatyczne pobieranie aktualnych i historycznych kursów walut
- **Wsparcie dla tabel A i C NBP**: 
  - Tabela A: kursy średnie
  - Tabela C: kursy kupna i sprzedaży (bid/ask)
- **Interaktywne wykresy**: Dynamiczne wykresy z użyciem Plotly.js
- **Wybór okresów czasowych**: 7 dni, 1 miesiąc, 6 miesięcy, 1 rok, wszystkie dane
- **Automatyczne zarządzanie danymi**: Inteligentne sprawdzanie i pobieranie brakujących danych
- **Wsparcie dla popularnych walut**: USD, EUR, GBP, CHF
- **Responsywny interfejs**: Nowoczesny design dostosowany do urządzeń mobilnych
- **Przechowywanie w SQLite**: Efektywne przechowywanie danych historycznych

## Instalacja i Uruchomienie

### Wymagania
- Python 3.7+
- pip (menedżer pakietów Python)

### Kroki instalacji

1. **Sklonuj repozytorium lub pobierz pliki projektu**

2. **Utwórz środowisko wirtualne (zalecane):**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Zainstaluj zależności:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Uruchom aplikację:**
   ```bash
   python app.py
   ```
   Serwer uruchomi się na `http://127.0.0.1:5000/`

5. **Inicjalizacja danych:**
   - Baza danych (`currency_rates.db`) zostanie utworzona automatycznie
   - Aplikacja automatycznie sprawdzi i pobierze brakujące dane przy pierwszym uruchomieniu
   - Możesz również ręcznie zaktualizować dane używając odpowiednich endpointów

## Struktura Projektu

```
├── app.py                 # Główny plik aplikacji Flask
├── schema.sql            # Schemat bazy danych SQLite
├── requirements.txt      # Zależności Python
├── README.md            # Dokumentacja projektu
├── check_db.py          # Skrypt do sprawdzania zawartości bazy danych
├── debug_check.py       # Plik pomocniczy do debugowania
├── currency_rates.db    # Baza danych SQLite (tworzona automatycznie)
└── templates/
    └── index.html       # Szablon HTML z interaktywnym interfejsem
```

## Dostępne Endpointy API

- `/` - Główna strona z wykresami kursów walut
- `/update_rates` - Aktualizacja kursów średnich (tabela A NBP)
- `/update_rates_bid_ask` - Aktualizacja kursów kupna/sprzedaży (tabela C NBP)
- `/update_historical_rates` - Pobieranie danych historycznych (ostatnie 30 dni)
- `/update_historical_rates_bid_ask` - Pobieranie historycznych kursów bid/ask
- `/check_and_fetch_data` - Sprawdzenie i pobranie brakujących danych

## Obsługiwane Waluty

Aplikacja obsługuje wszystkie waluty dostępne w API NBP, z domyślnym fokusem na:
- **USD** - Dolar amerykański
- **EUR** - Euro
- **GBP** - Funt brytyjski  
- **CHF** - Frank szwajcarski

## Technologie

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Wykresy**: Plotly.js
- **Baza danych**: SQLite
- **API**: NBP Web API
- **Styling**: CSS z responsywnym designem

## API Narodowego Banku Polskiego

Aplikacja wykorzystuje oficjalne [NBP Web API](http://api.nbp.pl/):
- **Tabela A**: Kursy średnie walut obcych
- **Tabela C**: Kursy kupna i sprzedaży walut obcych

API NBP jest darmowe i nie wymaga klucza dostępu. Dostarcza aktualne i historyczne kursy walut względem PLN.

## Konfiguracja i Dostosowanie

### Zmiana wyświetlanych walut
Edytuj zmienną `popular_currencies` w funkcji `index()` w pliku `app.py`:
```python
popular_currencies = ('USD', 'EUR', 'GBP', 'CHF', 'JPY')  # Dodaj więcej walut
```

### Zmiana okresów czasowych
Modyfikuj słownik `time_periods` w funkcji `index()`:
```python
time_periods = {
    '7days': '7 Dni',
    '1month': '1 Miesiąc', 
    '3months': '3 Miesiące',  # Nowy okres
    '6months': '6 Miesięcy',
    '1year': '1 Rok',
    'all': 'Wszystkie dane'
}
```

### Stylizacja interfejsu
Modyfikuj plik `templates/index.html` aby dostosować wygląd aplikacji.

## Funkcje Zaawansowane

- **Automatyczne zarządzanie danymi**: Aplikacja sprawdza dostępność danych i automatycznie pobiera brakujące informacje
- **Obsługa dużych zakresów dat**: Inteligentne dzielenie zapytań API na mniejsze części
- **Obsługa błędów**: Zabezpieczenia przed błędami API i bazą danych
- **Responsywny design**: Interfejs dostosowany do różnych rozmiarów ekranów

## Rozwiązywanie Problemów

### Brak danych po uruchomieniu
Aplikacja automatycznie pobierze dane przy pierwszym uruchomieniu. Jeśli nie, użyj:
```
http://127.0.0.1:5000/check_and_fetch_data
```

### Błędy połączenia z API
Sprawdź połączenie internetowe i dostępność API NBP pod adresem: http://api.nbp.pl/

### Problemy z bazą danych
Usuń plik `currency_rates.db` - zostanie utworzony ponownie przy następnym uruchomieniu.

## Licencja

Projekt wykorzystuje dane z publicznego API NBP zgodnie z regulaminem NBP.
