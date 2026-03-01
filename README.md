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

## Portfolio summary CLI
Run from the project package directory (`StockAdvisor/` where `pyproject.toml` lives):

```bash
cd StockAdvisor
pip install -e .
python -m stockbot.cli.portfolio_summary
```

Alternative (without editable install):

```bash
cd StockAdvisor/src
python -m stockbot.cli.portfolio_summary
```

Required Saxo environment variables:

- `SAXO_ACCESS_TOKEN` (OAuth access token)
- `SAXO_ENV` (`SIM` for simulation or `LIVE` for production)

The command prints a holdings table with current prices when available. Missing prices are shown as `N/A` and logged.

## Scope
This project is now scoped to Saxo positions + watchlists for filtering only.
Legacy instrument-search and price-visualization helpers have been removed.
