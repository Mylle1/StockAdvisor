# StockAdvisor frontend

This folder contains the React and TypeScript frontend for StockAdvisor. It
connects to the local FastAPI backend for Nordnet CSV upload, ticker search,
manual ticker mapping, and valuation results.

## Structure

- `src/App.tsx` controls the page navigation and selected stock state.
- `src/api.ts` contains the backend API calls.
- `src/types.ts` defines the valuation data shape expected by the UI.
- `src/components/PortfolioTable.tsx` renders the portfolio valuation table.
- `src/components/StockDetail.tsx` renders model-specific assumptions and
  valuation output for the selected stock.
- `src/components/CsvUpload.tsx` provides upload, ticker search, manual ticker mapping, and
  valuation controls.
- `src/components/AnalysisHistory.tsx` shows saved valuation runs from local history.
- `src/utils/formatters.ts` centralizes number, percentage, and model labels.
- `src/styles.css` contains the minimal professional styling.

## Local development

Start the Python backend from the project root first:

```powershell
.\.venv\Scripts\python -m uvicorn stockbot.api:app --reload --host 127.0.0.1 --port 8001
```

Then start the frontend:

```bash
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

The frontend uses `http://localhost:8001` by default. To override it:

```powershell
$env:VITE_API_BASE_URL = "http://127.0.0.1:8001"
npm run dev -- --host 127.0.0.1 --port 5173
```

Ticker mapping can be entered manually or selected from yfinance search
candidates. When valuation is run, the backend generates
`../data/fundamentals.json` from yfinance before using the existing valuation
engine.
