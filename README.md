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


## FMP fundamentals provider (external API)
Set your FMP API key as an environment variable:

```bash
export FMP_API_KEY="your_api_key_here"
```

CLI-style usage example:

```bash
cd StockAdvisor
python -c "import os; from stockbot.fundamentals.fmp_provider import FMPFundamentalsProvider; f = FMPFundamentalsProvider(os.environ['FMP_API_KEY']).get_fundamentals('AAPL'); print(f)"
```

## Valuation pipeline example (model selection + automatic WACC)

```python
from stockbot.valuation.dcf import two_stage_dcf
from stockbot.valuation.model_selector import estimate_wacc, select_valuation_model
from stockbot.valuation.reverse_dcf import reverse_dcf_implied_growth


def run_valuation_pipeline(current_price: float, fundamentals: dict, dcf_params: dict, reverse_dcf_params: dict) -> dict:
    """Select valuation model, estimate WACC for DCF path, and return valuation output."""
    model = select_valuation_model(
        revenue_growth_5y=fundamentals.get("revenue_growth_5y"),
        fcf_margin=fundamentals.get("fcf_margin"),
    )

    if model == "dcf":
        revenue_growth_5y = fundamentals.get("revenue_growth_5y") or 0.0
        wacc = estimate_wacc(revenue_growth_5y)
        return two_stage_dcf(
            current_price=current_price,
            revenue_last_year=fundamentals["revenue_last_year"],
            revenue_growth=dcf_params["revenue_growth"],
            target_fcf_margin=dcf_params["target_fcf_margin"],
            wacc=wacc,
            terminal_growth=dcf_params["terminal_growth"],
            forecast_years=dcf_params.get("forecast_years", 10),
            net_debt=fundamentals["net_debt"],
            shares_outstanding=fundamentals["shares_outstanding"],
        )

    return reverse_dcf_implied_growth(
        current_price=current_price,
        shares_outstanding=fundamentals["shares_outstanding"],
        revenue_last_year=fundamentals["revenue_last_year"],
        target_fcf_margin=reverse_dcf_params["target_fcf_margin"],
        wacc=reverse_dcf_params["wacc"],
        terminal_growth=reverse_dcf_params["terminal_growth"],
        forecast_years=reverse_dcf_params.get("forecast_years", 10),
        net_debt=fundamentals["net_debt"],
    )
```
