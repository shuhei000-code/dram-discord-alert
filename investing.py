from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class PriceResult:
    symbol: str
    price: Decimal
    currency: str
    source_url: str


class InvestingPriceError(RuntimeError):
    """Raised when the price cannot be fetched or parsed."""


def _parse_decimal(value: str) -> Decimal | None:
    """Extract a decimal number from a text fragment."""
    if not value:
        return None

    cleaned = value.strip().replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None

    try:
        parsed = Decimal(match.group(0))
    except InvalidOperation:
        return None

    if parsed <= 0:
        return None

    # Guardrail to avoid accidentally parsing timestamps or unrelated huge values.
    if parsed > Decimal("1000000"):
        return None

    return parsed


def _extract_price_from_html(html: str) -> Decimal | None:
    """Try multiple strategies because Investing.com changes markup sometimes."""
    soup = BeautifulSoup(html, "html.parser")

    selectors = [
        '[data-test="instrument-price-last"]',
        '[data-test="price"]',
        '[data-test="last-price"]',
        'span[data-test="instrument-price-last"]',
        'div[data-test="instrument-price-last"]',
    ]

    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            price = _parse_decimal(node.get_text(" ", strip=True))
            if price is not None:
                return price

    # Fallback: search embedded JSON / scripts.
    # The first strategy above is preferred; regex fallback exists only for markup changes.
    patterns = [
        r'"lastPrice"\s*:\s*"?([0-9][0-9,]*(?:\.[0-9]+)?)"?',
        r'"last"\s*:\s*"?([0-9][0-9,]*(?:\.[0-9]+)?)"?',
        r'"price"\s*:\s*"?([0-9][0-9,]*(?:\.[0-9]+)?)"?',
        r'"instrumentPriceLast"\s*:\s*"?([0-9][0-9,]*(?:\.[0-9]+)?)"?',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, html):
            price = _parse_decimal(match.group(1))
            if price is not None:
                return price

    # Final fallback: page title / meta text may include a visible price.
    title_text = ""
    if soup.title and soup.title.string:
        title_text = soup.title.string

    meta_texts = []
    for meta in soup.find_all("meta"):
        content = meta.get("content")
        if content:
            meta_texts.append(content)

    combined = " ".join([title_text, *meta_texts])
    if "DRAM" in combined.upper():
        return _parse_decimal(combined)

    return None


def fetch_dram_price(url: str, symbol: str = "DRAM") -> PriceResult:
    """Fetch DRAM price from Investing.com."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise InvestingPriceError(f"Failed to fetch Investing.com page: {exc}") from exc

    html = response.text
    price = _extract_price_from_html(html)

    if price is None:
        raise InvestingPriceError(
            "Could not parse DRAM price from Investing.com HTML. "
            "The page structure may have changed or the request may have been blocked."
        )

    return PriceResult(
        symbol=symbol,
        price=price,
        currency="USD",
        source_url=url,
    )
