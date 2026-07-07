from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

import requests


@dataclass(frozen=True)
class PriceResult:
    symbol: str
    price: Decimal
    currency: str
    source_url: str
    previous_close: Decimal | None
    day_change: Decimal | None
    day_change_percent: Decimal | None
    recent_high: Decimal
    recent_high_date: str | None
    drawdown_percent: Decimal
    source_name: str = "Yahoo Finance"


class PriceFetchError(RuntimeError):
    """Raised when the price cannot be fetched or parsed."""


def _to_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _round(value: Decimal, places: str = "0.01") -> Decimal:
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def fetch_dram_price(
    yahoo_symbol: str = "DRAM",
    display_symbol: str = "DRAM",
    lookback_range: str = "3mo",
    timezone: str = "Asia/Tokyo",
) -> PriceResult:
    """Fetch DRAM price and recent high from Yahoo Finance chart API."""
    symbol = yahoo_symbol.upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    params = {
        "range": lookback_range,
        "interval": "1d",
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise PriceFetchError(f"Failed to fetch Yahoo Finance data: {exc}") from exc
    except ValueError as exc:
        raise PriceFetchError(f"Failed to parse Yahoo Finance JSON: {exc}") from exc

    chart = data.get("chart", {})
    if chart.get("error"):
        raise PriceFetchError(f"Yahoo Finance returned an error: {chart['error']}")

    try:
        result = chart["result"][0]
        meta = result["meta"]
        timestamps = result.get("timestamp", [])
        quote = result["indicators"]["quote"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise PriceFetchError(f"Unexpected Yahoo Finance response shape: {exc}") from exc

    current_price = _to_decimal(meta.get("regularMarketPrice"))
    previous_close = _to_decimal(meta.get("previousClose"))

    closes = quote.get("close", []) or []
    valid_closes = [_to_decimal(x) for x in closes if x is not None]
    valid_closes = [x for x in valid_closes if x is not None and x > 0]

    if current_price is None and valid_closes:
        current_price = valid_closes[-1]

    if current_price is None:
        raise PriceFetchError("Could not find current DRAM price from Yahoo Finance.")

    highs = quote.get("high", []) or []
    high_values: list[tuple[Decimal, int]] = []
    for idx, high in enumerate(highs):
        parsed = _to_decimal(high)
        if parsed is not None and parsed > 0:
            high_values.append((parsed, idx))

    if not high_values:
        raise PriceFetchError("Could not find recent high from Yahoo Finance.")

    recent_high, recent_high_index = max(high_values, key=lambda item: item[0])

    recent_high_date = None
    if timestamps and recent_high_index < len(timestamps):
        recent_high_date = datetime.fromtimestamp(
            timestamps[recent_high_index],
            tz=ZoneInfo(timezone),
        ).strftime("%Y-%m-%d")

    day_change = None
    day_change_percent = None
    if previous_close is not None and previous_close > 0:
        day_change = current_price - previous_close
        day_change_percent = (day_change / previous_close) * Decimal("100")

    drawdown_percent = ((current_price - recent_high) / recent_high) * Decimal("100")

    return PriceResult(
        symbol=display_symbol.upper(),
        price=_round(current_price, "0.01"),
        currency=meta.get("currency", "USD"),
        source_url=f"https://finance.yahoo.com/quote/{symbol}",
        previous_close=_round(previous_close, "0.01") if previous_close is not None else None,
        day_change=_round(day_change, "0.01") if day_change is not None else None,
        day_change_percent=_round(day_change_percent, "0.01") if day_change_percent is not None else None,
        recent_high=_round(recent_high, "0.01"),
        recent_high_date=recent_high_date,
        drawdown_percent=_round(drawdown_percent, "0.01"),
    )
