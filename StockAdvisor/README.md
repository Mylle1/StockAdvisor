# StockAdvisor

StockAdvisor imports Nordnet holdings, lets you map each holding to a yfinance-compatible ticker, and runs the existing Python valuation flow.

## Backend

From the project root:

```powershell
.\.venv\Scripts\python -m uvicorn stockbot.api:app --reload --host 127.0.0.1 --port 8001
```

The API will be available at `http://127.0.0.1:8001`.

Useful endpoints:

- `GET /api/health`
- `POST /api/uploads/nordnet`
- `POST /api/ticker-mappings`
- `POST /api/valuations/run`

Uploading a Nordnet report writes normalized holdings to `data/holdings_raw.json`. Confirming tickers creates or updates `data/ticker_mapping.json` and writes mapped holdings to `data/holdings_mapped.json`. Running valuation fetches fundamentals from yfinance, writes `data/fundamentals.json`, then passes those generated fundamentals into the existing valuation engine.

Manual ticker input is the mapping workflow.

## Frontend

In a second terminal:

```powershell
cd frontend
$env:VITE_API_BASE_URL = "http://127.0.0.1:8001"
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`.

## Local Flow

1. Start the backend.
2. Start the frontend.
3. Upload the Nordnet CSV report.
4. Review the imported stock holdings.
5. Enter or edit each yfinance-compatible ticker manually.
6. Save mappings or run the valuation. The run generates fundamentals from yfinance.
7. Review valuation outputs and model parameters in the portfolio view.

The UI is designed as decision support and does not produce buy/sell recommendations.
