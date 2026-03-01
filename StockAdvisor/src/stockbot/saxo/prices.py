from stockbot.saxo.client import SaxoClient

def get_chart_data(client: SaxoClient, uic: int, horizon_minutes: int = 1440, AssetType: str = "Stock", count: int = 365):
    return client.get(
        "/chart/v3/charts", 
        params={
            "AssetType": AssetType,
            "Uic": uic,
            "Horizon": horizon_minutes,
            "Count": count,
            "Mode": "UpTo",
        },
    )