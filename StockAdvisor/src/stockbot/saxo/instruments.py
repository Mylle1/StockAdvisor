from stockbot.saxo.client import SaxoClient


def search_instruments(client: SaxoClient, keyword: str, asset_types: str = "Stock", top: int = 20):
    return client.get(
        "/ref/v1/instruments",
        params={
            "Keywords": keyword,
            "AssetTypes": asset_types,
            "IncludeNonTradable": "true",
            "$top": top,
        },
    )
