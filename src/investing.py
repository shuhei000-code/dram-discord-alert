from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import requests


@dataclass(frozen=True)
class PriceResult:
    symbol: str
    price: Decimal
    currency: str
    source_url: str


class InvestingPriceError(RuntimeError):
    """Raised when the price cannot be fetched or parsed."""


def fetch_dram_price(url: str, symbol: str = "DRAM") -> PriceResult:
    """Fetch DRAM price from Yahoo Finance.

    The `url` argument is kept for compatibility with main.py/config.py,
    but this function uses Yahoo Finance from the start.
    """
    yahoo_symbol = symbol.upper()
    yahoo_api_url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{yahoo_symbol}?range=1d&interval=1m"
    )

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }

    try:
        response = requests.get(yahoo_api_url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise InvestingPriceError(f"Failed to fetch Yahoo Finance data: {exc}") from exc
    except ValueError as exc:
        raise InvestingPriceError(f"Failed to parse Yahoo Finance JSON: {exc}") from exc

    try:
        chart = data["chart"]
        result = chart["result"][0]
        meta = result["meta"]

        raw_price = meta.get("regularMarketPrice")

        if raw_price is None:
            raw_price = meta.get("previousClose")

        if raw_price is None:
            closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
            valid_closes = [price for price in closes if price is not None]
            if valid_closes:
                raw_price = valid_closes[-1]

        if raw_price is None:
            raise KeyError("regularMarketPrice / previousClose / close not found")

        currency = meta.get("currency", "USD")

    except (KeyError, IndexError, TypeError) as exc:
        raise InvestingPriceError(f"Could not extract DRAM price from Yahoo Finance data: {exc}") from exc

    return PriceResult(
        symbol=yahoo_symbol,
        price=Decimal(str(raw_price)),
        currency=currency,
        source_url=f"https://finance.yahoo.com/quote/{yahoo_symbol}",
    )
