from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    discord_webhook: str
    symbol: str
    yahoo_symbol: str
    timezone: str
    notify_on_error: bool
    discord_mention: str
    state_file: str
    lookback_range: str
    run_mode: str


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_config() -> AppConfig:
    load_dotenv()

    webhook = os.getenv("DISCORD_WEBHOOK", "").strip()
    if not webhook:
        raise ValueError(
            "DISCORD_WEBHOOK is not set. "
            "Add it to GitHub Actions repository secrets."
        )

    symbol = os.getenv("DRAM_SYMBOL", "DRAM").strip() or "DRAM"

    return AppConfig(
        discord_webhook=webhook,
        symbol=symbol,
        yahoo_symbol=os.getenv("YAHOO_SYMBOL", symbol).strip() or symbol,
        timezone=os.getenv("TIMEZONE", "Asia/Tokyo").strip() or "Asia/Tokyo",
        notify_on_error=_to_bool(os.getenv("NOTIFY_ON_ERROR"), default=True),
        discord_mention=os.getenv("DISCORD_MENTION", "").strip(),
        state_file=os.getenv("STATE_FILE", "state/dip_state.json").strip(),
        lookback_range=os.getenv("LOOKBACK_RANGE", "3mo").strip() or "3mo",
        run_mode=os.getenv("RUN_MODE", "alert").strip().lower() or "alert",
    )
