from stockbot.saxo.client import SaxoClient
from stockbot.saxo.universe import build_filter_universe


def main():
    client = SaxoClient()
    universe = build_filter_universe(client)
    print(
        {
            "positions": len(universe["positions"]),
            "watchlist": len(universe["watchlist"]),
            "filter_universe": len(universe["filter_universe"]),
        }
    )


if __name__ == "__main__":
    main()
