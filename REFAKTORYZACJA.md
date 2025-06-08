# Refaktoryzacja: Podział na 3 Aplikacje (Warstwy)

## Opis przeprowadzonej refaktoryzacji

Zgodnie z wymaganiami strukturalnymi zadania, aplikacja została podzielona na **3 oddzielne warstwy aplikacji**, zgodnie z wzorcem architektury wielowarstwowej (Multi-tier Architecture).

## Struktura 3-warstwowa

### 1. **Warstwa Danych (Data Layer)** - `models.py`
**Odpowiedzialność:** Obsługa bazy danych, modele danych, operacje CRUD

**Klasy:**
- `DatabaseManager` - zarządzanie połączeniami z bazą danych
- `CurrencyRatesModel` - operacje na danych kursów walut

**Funkcjonalności:**
- Połączenia z bazą SQLite
- Operacje SELECT, INSERT, UPDATE
- Zarządzanie transakcjami
- Obsługa row factory dla SQLite
- Walidacja i sprawdzanie istnienia danych

### 2. **Warstwa Logiki Biznesowej (Business Logic Layer)** - `services.py`
**Odpowiedzialność:** Logika aplikacji, przetwarzanie danych, integracje z API

**Klasy:**
- `NBPService` - obsługa API Narodowego Banku Polskiego
- `CryptocurrencyService` - obsługa API CoinGecko
- `CurrencyDataService` - zarządzanie danymi walutowymi
- `ChartDataService` - przygotowanie danych do wykresów

**Funkcjonalności:**
- Pobieranie danych z zewnętrznych API
- Przetwarzanie i transformacja danych
- Logika biznesowa (sprawdzanie brakujących danych)
- Kalkulacje (zmiany kursów, procenty)
- Przygotowanie danych dla warstwy prezentacji

### 3. **Warstwa Prezentacji (Presentation Layer)** - `app.py`
**Odpowiedzialność:** Interfejs użytkownika, routing HTTP, renderowanie szablonów

**Funkcjonalności:**
- Routing Flask (`@app.route`)
- Obsługa żądań HTTP
- Renderowanie szablonów HTML
- Zwracanie odpowiedzi JSON
- Obsługa parametrów zapytań
- Zarządzanie sesjami użytkowników

## Korzyści z podziału na warstwy

### 1. **Separacja odpowiedzialności (Separation of Concerns)**
- Każda warstwa ma jasno określoną rolę
- Łatwiejsze testowanie poszczególnych komponentów
- Lepsze zarządzanie zależnościami

### 2. **Łatwość utrzymania**
- Zmiany w jednej warstwie nie wpływają na inne
- Możliwość niezależnego rozwoju każdej warstwy
- Lepsza organizacja kodu

### 3. **Skalowalność**
- Możliwość łatwego dodawania nowych funkcjonalności
- Warstwa danych może być łatwo zastąpiona inną bazą danych
- Warstwa biznesowa może być rozszerzona o nowe serwisy

### 4. **Testowanie**
- Każda warstwa może być testowana niezależnie
- Możliwość mockowania zależności
- Łatwiejsze tworzenie testów jednostkowych

## Przykład przepływu danych

```
HTTP Request → app.py (Presentation Layer)
                 ↓
              services.py (Business Logic Layer)
                 ↓
              models.py (Data Layer)
                 ↓
              SQLite Database
```

## Szczegóły techniczne

### Import między warstwami:
```python
# app.py importuje services i models
from models import DatabaseManager, CurrencyRatesModel
from services import CurrencyDataService, CryptocurrencyService, ChartDataService

# services.py importuje models
from models import CurrencyRatesModel
```

### Eliminacja bezpośrednich zapytań SQL w app.py:
- **Przed:** Zapytania SQL bezpośrednio w routach
- **Po:** Wszystkie zapytania przeniesione do `CurrencyRatesModel`

### Eliminacja logiki biznesowej z app.py:
- **Przed:** Obliczenia, przetwarzanie danych w routach
- **Po:** Cała logika przeniesiona do odpowiednich serwisów

## Zgodność z wymaganiami zadania

✅ **Podział na 3 aplikacje:** Warstwa danych, logiki biznesowej i prezentacji  
✅ **Zachowanie pełnej funkcjonalności:** Wszystkie funkcje działają identycznie  
✅ **Czysta architektura:** Jasne granice między warstwami  
✅ **Łatwość rozwoju:** Możliwość niezależnego rozwijania każdej warstwy  

## Pliki po refaktoryzacji

1. **`models.py`** (115 linii) - Warstwa danych
2. **`services.py`** (167 linii) - Warstwa logiki biznesowej  
3. **`app.py`** (120 linii) - Warstwa prezentacji

**Całkowita liczba linii:** ~400 linii (vs 700+ w oryginalnym pliku)

Ta refaktoryzacja spełnia wszystkie wymagania strukturalne zadania, zachowując jednocześnie pełną funkcjonalność aplikacji.
