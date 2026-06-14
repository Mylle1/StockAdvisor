# StockAdvisor frontend prototype

This folder contains the first React and TypeScript prototype for the
StockAdvisor web interface. It is intentionally front-end only and uses mock
valuation output so the UI can later be connected to the existing Python
valuation backend.

## Structure

- `src/App.tsx` controls the page navigation and selected stock state.
- `src/data/mockValuations.ts` contains mock valuation output based on the
  current CLI rows.
- `src/types.ts` defines the valuation data shape expected by the UI.
- `src/components/PortfolioTable.tsx` renders the portfolio valuation table.
- `src/components/StockDetail.tsx` renders model-specific assumptions and
  valuation output for the selected stock.
- `src/components/CsvUpload.tsx` provides the Nordnet CSV upload placeholder.
- `src/components/AnalysisHistory.tsx` provides the future history placeholder.
- `src/utils/formatters.ts` centralizes number, percentage, and model labels.
- `src/styles.css` contains the minimal professional styling.

## Local development

```bash
npm install
npm run dev
```

The current version does not process uploaded CSV files. CSV processing will be
connected to the Python backend later.
