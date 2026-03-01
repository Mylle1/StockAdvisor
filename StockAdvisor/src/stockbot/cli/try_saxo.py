from stockbot.saxo.client import SaxoClient
from stockbot.saxo.instruments import search_instruments


def main():
    client = SaxoClient()
    # Search for an instrument
    result = search_instruments(client, "Novo Nordisk")
    print(result)

if __name__ == "__main__":
    main()
