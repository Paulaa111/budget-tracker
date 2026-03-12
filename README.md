# 📊 Budget Tracker – Instrukcja wdrożenia

## Struktura plików

```
budget_tracker/
├── app.py              ← główna aplikacja Streamlit
├── api_connectors.py   ← integracja Google Ads API + Meta Ads API
├── requirements.txt    ← zależności Python
├── .env                ← TWOJE TOKENY (nie wrzucaj do git!)
└── clients_data.json   ← dane klientów i budżetów (auto-generowany)
```

---

## 1. Instalacja

```bash
# Sklonuj / skopiuj folder budget_tracker
cd budget_tracker

# Utwórz środowisko wirtualne (opcjonalnie, ale zalecane)
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Zainstaluj zależności bazowe
pip install -r requirements.txt

# Gdy gotowe do połączenia z API – odkomentuj w requirements.txt i uruchom ponownie:
pip install google-ads facebook-business
```

---

## 2. Uruchomienie

```bash
streamlit run app.py
```

Aplikacja otwiera się pod adresem: **http://localhost:8501**

---

## 3. Konfiguracja API

### Przez interfejs (zalecane)
1. Wejdź w zakładkę **⚙️ Ustawienia API**
2. Wpisz tokeny i zapisz
3. Zrestartuj aplikację

### Ręcznie – plik `.env`
Utwórz plik `.env` w folderze `budget_tracker/`:

```env
# Google Ads
GOOGLE_ADS_DEVELOPER_TOKEN=tu_wpisz_token
GOOGLE_ADS_CLIENT_ID=tu_wpisz_client_id
GOOGLE_ADS_CLIENT_SECRET=tu_wpisz_secret
GOOGLE_ADS_REFRESH_TOKEN=tu_wpisz_refresh_token
GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890  # MCC account ID (opcjonalnie)

# Meta Ads
META_ACCESS_TOKEN=tu_wpisz_token
META_API_VERSION=v19.0
```

---

## 4. Jak uzyskać tokeny?

### Google Ads API
1. Zaloguj się na konto MCC (Manager Account)
2. Wejdź na https://ads.google.com/aw/apicenter → pobierz **Developer Token**
3. W Google Cloud Console utwórz projekt → włącz **Google Ads API**
4. Utwórz OAuth 2.0 credentials (Desktop app) → pobierz `client_id` i `client_secret`
5. Wygeneruj `refresh_token` przez OAuth Playground: https://developers.google.com/oauthplayground

### Meta Ads API
1. Wejdź na https://developers.facebook.com/ → utwórz aplikację **Business**
2. Dodaj produkt **Marketing API**
3. Wygeneruj **Long-lived Access Token** z uprawnieniami: `ads_read`, `ads_management`
4. Account ID znajdziesz w Menedżerze Reklam Meta (format: `act_XXXXXXXXX`)

---

## 5. Wdrożenie dla zespołu

### Opcja A – Streamlit Community Cloud (darmowe)
1. Wrzuć kod na GitHub (bez pliku `.env`!)
2. Wejdź na https://streamlit.io/cloud
3. Połącz repozytorium i wdróż
4. Tokeny API wpisz w **Secrets** w ustawieniach aplikacji

### Opcja B – Lokalny serwer
```bash
# Na serwerze firmowym
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Opcja C – Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## 6. Uwagi

- Dane klientów i budżetów zapisywane są lokalnie w `clients_data.json`
- Przy wdrożeniu na Streamlit Cloud użyj zewnętrznej bazy (np. Supabase) zamiast pliku JSON
- Aplikacja przelicza VAT 23% automatycznie (netto ↔ brutto)
- Dzienny limit = `(budżet - wydano) / liczba pozostałych dni w miesiącu`
