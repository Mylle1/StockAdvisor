from stockbot.config.settings import settings
from stockbot.fundamentals.fmp_provider import FMPFundamentalsProvider

print("Testing FMPFundamentalsProvider with new /stable/ endpoints...")
print()

provider = FMPFundamentalsProvider(api_key=settings.fmp_api_key)

try:
    fundamentals = provider.get_fundamentals("AAPL")
    print("✅ SUCCESS! FMP integration virker nu!")
    print()
    print(f"Ticker: {fundamentals.ticker}")
    print(f"Revenue (last year): ${fundamentals.revenue_last_year:,.0f}")
    print(f"Shares outstanding: {fundamentals.shares_outstanding:,.0f}")
    print(f"Net debt: ${fundamentals.net_debt:,.0f}")
    if fundamentals.revenue_growth_5y:
        print(f"Revenue growth (5y): {fundamentals.revenue_growth_5y:.2%}")
    if fundamentals.fcf_margin:
        print(f"FCF margin: {fundamentals.fcf_margin:.2%}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
