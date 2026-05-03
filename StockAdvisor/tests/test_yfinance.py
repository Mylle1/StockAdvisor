import yfinance as yf

ticker = yf.Ticker("ASML")

# Hent quarterly revenue
revenue = ticker.quarterly_financials.loc["Total Revenue"]

# Filtrer kun 2025
revenue_2025 = revenue[revenue.index.year == 2025]

print(revenue_2025)