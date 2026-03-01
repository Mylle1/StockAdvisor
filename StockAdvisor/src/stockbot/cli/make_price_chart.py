from stockbot.saxo.client import SaxoClient
from stockbot.viz.price_chart import build_price_chart_html


def main():
    client = SaxoClient()

    # Novo Nordisk B (CSE)
    uic = 15629
    out = build_price_chart_html(
        client,
        uic=uic,
        title="Novo Nordisk B (UIC 15629) — Dayli Price (last 365 days)",
        out_path="reports/novo_15629_price.html",
        horizon=1440,  # 1 day in minutes
        count=365,     # last 365 days
    )
    print(f"Wrote: {out}")


if __name__ == "__main__":
    main()
