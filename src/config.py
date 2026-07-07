from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    discord_webhook: str
    investing_url: str
    symbol: str
    timezone: str
    notify_on_error: bool
    discord_mention: str


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_config() -> AppConfig:
    """Load configuration from environment variables.

    Local execution can use a .env file.
    GitHub Actions should use repository secrets.
    """
    load_dotenv()

    webhook = os.getenv("DISCORD_WEBHOOK", "").strip()
    if not webhook:
        raise ValueError(
            "DISCORD_WEBHOOK is not set. "
            "Add it to .env for local use or GitHub Actions repository secrets."
        )

    return AppConfig(
        discord_webhook=webhook,
        investing_url=os.getenv("INVESTING_URL", "https://jp.investing.com/etfs/dram").strip(),
        symbol=os.getenv("DRAM_SYMBOL", "DRAM").strip(),
        timezone=os.getenv("TIMEZONE", "Asia/Tokyo").strip(),
        notify_on_error=_to_bool(os.getenv("NOTIFY_ON_ERROR"), default=True),
        discord_mention=os.getenv("DISCORD_MENTION", "").strip(),
    )
