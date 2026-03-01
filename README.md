# StockAdvisor
StockAdvisor is an intelligent financial advisory system designed to analyze individual stock portfolios through seamless integration with the Saxo API. By combining market data, quantitative analysis, and risk assessment, it delivers high-quality, personalized investment insights to support smarter decision-making.

## Pull current positions and watchlist for filtering
Run:

```bash
python -m stockbot.cli.try_saxo
```

This collects:
- current positions (`/port/v1/positions/me`)
- watchlists (`/port/v1/watchlists` and `/port/v1/watchlists/{id}`)

and stores a combined filter universe in:

- `reports/filter_universe.json`
## Scope
This project is now scoped to Saxo positions + watchlists for filtering only.
Legacy instrument-search and price-visualization helpers have been removed.

