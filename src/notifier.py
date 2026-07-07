from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import requests

from .investing import PriceResult


class DiscordNotifyError(RuntimeError):
    """Raised when Discord webhook notification fails."""


def _format_decimal(value: Decimal) -> str:
    # Show up to 4 decimals while removing unnecessary trailing zeros.
    normalized = f"{value:.4f}".rstrip("0").rstrip(".")
    return normalized


def send_price_notification(
    webhook_url: str,
    result: PriceResult,
    timezone: str = "Asia/Tokyo",
    mention: str = "",
) -> None:
    now = datetime.now(ZoneInfo(timezone))
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")

    content = mention.strip() if mention.strip() else None

    payload = {
        "content": content,
        "embeds": [
            {
                "title": "📈 DRAM ETF Price Alert",
                "description": f"**{result.symbol}** の現在価格を取得しました。",
                "color": 3447003,
                "fields": [
                    {
                        "name": "現在価格",
                        "value": f"`{_format_decimal(result.price)} {result.currency}`",
                        "inline": True,
                    },
                    {
                        "name": "取得時刻",
                        "value": f"`{timestamp}`",
                        "inline": True,
                    },
                    {
                        "name": "Source",
                        "value": f"[Investing.com]({result.source_url})",
                        "inline": False,
                    },
                ],
            }
        ],
    }

    _post_discord(webhook_url, payload)


def send_error_notification(
    webhook_url: str,
    error_message: str,
    timezone: str = "Asia/Tokyo",
    mention: str = "",
) -> None:
    now = datetime.now(ZoneInfo(timezone))
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")

    content = mention.strip() if mention.strip() else None

    payload = {
        "content": content,
        "embeds": [
            {
                "title": "⚠️ DRAM Notifier Error",
                "description": "DRAM価格の取得または通知処理でエラーが発生しました。",
                "color": 15158332,
                "fields": [
                    {
                        "name": "エラー内容",
                        "value": f"```{error_message[:900]}```",
                        "inline": False,
                    },
                    {
                        "name": "発生時刻",
                        "value": f"`{timestamp}`",
                        "inline": True,
                    },
                ],
            }
        ],
    }

    _post_discord(webhook_url, payload)


def _post_discord(webhook_url: str, payload: dict) -> None:
    try:
        response = requests.post(webhook_url, json=payload, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DiscordNotifyError(f"Failed to send Discord notification: {exc}") from exc
