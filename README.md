# Aplikacja Kursów Walut

Zaawansowana aplikacja webowa Flask do monitorowania i analizowania kursów walut z API Narodowego Banku Polskiego (NBP). Aplikacja pozwala na śledzenie historycznych kursów walut z interaktywnymi wykresami i automatycznym zarządzaniem danymi.

## Funkcjonalności

- **Kursy Walut** - Monitorowanie kursów walut względem PLN z interaktywnymi wykresami
- **Śledzenie Kryptowalut** - Przegląd top 10 kryptowalut z danymi rynkowymi w czasie rzeczywistym
- **Wieloźródłowe Dane**:
  - API NBP: Narodowy Bank Polski dla kursów walut (Tabele A i C)
  - API CoinGecko: Dane rynkowe kryptowalut
- **Interaktywna Nawigacja** - Łatwe przełączanie między walutami a kryptowalutami
- **Endpointy JSON API** - RESTful API do dostępu do przechowywanych danych walutowych
- **Responsywny Design** - Nowoczesny interfejs zoptymalizowany na desktop i urządzenia mobilne
- **Automatyczne Zarządzanie Danymi** - Inteligentne pobieranie i przechowywanie brakujących danych historycznych
- **Wybór Okresów Czasowych** - 7 dni, 1 miesiąc, 6 miesięcy, 1 rok lub wszystkie dostępne dane
- **Zewnętrzne Style CSS** - Czysta, łatwa w utrzymaniu architektura kodu

## Instalacja

### Wymagania

- Python 3.7+
- pip (menedżer pakietów Python)

### Konfiguracja

1. **Sklonuj repozytorium lub pobierz pliki projektu**

2. **Utwórz środowisko wirtualne (zalecane):**
   ```bash
   python -m venv venv
   ```

3. **Aktywuj środowisko wirtualne:**
   ```bash
   # Windows
   .\venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Zainstaluj zależności:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Uruchom aplikację:**
   ```bash
   python app.py
   ```
   
   Serwer uruchomi się na `http://127.0.0.1:5000/`

6. **Inicjalizacja danych:**
   - Baza danych (`currency_rates.db`) zostanie utworzona automatycznie
   - Aplikacja automatycznie sprawdzi i pobierze brakujące dane przy pierwszym uruchomieniu
   - Możesz również ręcznie zaktualizować dane używając odpowiednich endpointów

## Dokumentacja API

### Interfejs Webowy

- **`/` lub `/currencies`** - Główny panel kursów walut
- **`/cryptocurrencies`** - Top 10 kryptowalut z danymi rynkowymi

### Endpointy REST API

#### Pobieranie Kursów Walut
```
GET /api/rates
```

**Parametry zapytania:**
- `currency` - Filtruj według kodu waluty (np. USD, EUR)
- `limit` - Maksymalna liczba rekordów (domyślnie: 30)
- `start_date` - Filtruj od daty (format YYYY-MM-DD)
- `end_date` - Filtruj do daty (format YYYY-MM-DD)

**Przykład:**
```
GET /api/rates?currency=USD&limit=10
```

#### Ręczna Aktualizacja Danych
```
GET /check_and_fetch_data
```

### Źródła Danych

- **API NBP** - Kursy walut Narodowego Banku Polskiego
  - Tabela A: Kursy średnie
  - Tabela C: Kursy kupna/sprzedaży (bid/ask)
- **API CoinGecko** - Dane rynkowe kryptowalut (darmowy poziom)

## Struktura Projektu

```
curr-exchange-tracker/
├── app.py                # Główna aplikacja Flask
├── schema.sql            # Schemat bazy danych
├── requirements.txt      # Zależności Python
├── check_db.py           # Skrypt do sprawdzania zawartości bazy danych
├── currency_rates.db     # Baza SQLite (tworzona automatycznie)
├── static/
│   └── style.css         # Zewnętrzne style CSS
├── templates/
│   ├── index.html        # Strona kursów walut
│   └── crypto.html       # Strona kryptowalut
├── README.md             # Dokumentacja polska
└── README_eng.md         # Dokumentacja angielska
```

## Obsługiwane Waluty

Aplikacja obsługuje wszystkie waluty dostępne w API NBP, z domyślnym fokusem na:

- **USD** - Dolar amerykański
- **EUR** - Euro
- **GBP** - Funt brytyjski  
- **CHF** - Frank szwajcarski

## Stos Technologiczny

- **Backend:** Flask (Python)
- **Frontend:** HTML5, CSS3, JavaScript
- **Wykresy:** Plotly.js
- **Baza danych:** SQLite
- **API:** NBP Web API, CoinGecko API
- **Styling:** CSS z responsywnym designem

## Integracja z API NBP

Aplikacja wykorzystuje oficjalne [NBP Web API](http://api.nbp.pl/):

- **Tabela A** - Kursy średnie walut obcych
- **Tabela C** - Kursy kupna i sprzedaży walut obcych

API NBP jest darmowe i nie wymaga klucza dostępu. Dostarcza aktualne i historyczne kursy walut względem PLN.

## Konfiguracja

### Zmiana Wyświetlanych Walut

Edytuj zmienną `popular_currencies` w funkcji `index()` w pliku `app.py`:

```python
popular_currencies = ('USD', 'EUR', 'GBP', 'CHF', 'JPY')  # Dodaj więcej walut
```

### Modyfikacja Okresów Czasowych

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

### Dostosowanie Interfejsu

Modyfikuj CSS w `static/style.css` lub szablony HTML w katalogu `templates/`.

## Funkcje Zaawansowane

- **Automatyczne Zarządzanie Danymi** - Aplikacja sprawdza dostępność danych i automatycznie pobiera brakujące informacje
- **Obsługa Dużych Zakresów Dat** - Inteligentne dzielenie zapytań API na mniejsze części
- **Obsługa Błędów** - Zabezpieczenia przed błędami API i bazą danych
- **Responsywny Design** - Interfejs dostosowany do różnych rozmiarów ekranów

## Rozwiązywanie Problemów

### Brak Danych Po Uruchomieniu

Aplikacja automatycznie pobierze dane przy pierwszym uruchomieniu. Jeśli nie, ręcznie wywołaj:

```
http://127.0.0.1:5000/check_and_fetch_data
```

### Błędy Połączenia z API

- Sprawdź połączenie internetowe
- Zweryfikuj dostępność API NBP pod adresem: http://api.nbp.pl/

### Problemy z Bazą Danych

Usuń plik `currency_rates.db` - zostanie utworzony ponownie przy następnym uruchomieniu.

## Licencja

Projekt wykorzystuje dane z publicznego API NBP zgodnie z regulaminem NBP.
