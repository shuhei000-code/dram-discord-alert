from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import requests

from .investing import PriceResult
from .rules import DipRule, format_rules


class DiscordNotifyError(RuntimeError):
    """Raised when Discord webhook notification fails."""


def _fmt_decimal(value: Decimal | None, suffix: str = "") -> str:
    if value is None:
        return "N/A"
    text = f"{value:.2f}"
    if value > 0 and suffix == "%":
        text = f"+{text}"
    return f"{text}{suffix}"


def send_status_notification(
    webhook_url: str,
    result: PriceResult,
    timezone: str = "Asia/Tokyo",
    mention: str = "",
    dip_rule: DipRule | None = None,
    mode: str = "daily",
) -> None:
    now = datetime.now(ZoneInfo(timezone))
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")

    if mode == "daily":
        title = "📊 DRAM 定期通知（22:40）"
        description = "本日のDRAM状況です。"
        color = 3447003
    else:
        title = "📉 DRAM 買い増し通知"
        description = "下落率が買い増し基準に到達しました。"
        color = 15105570

    if dip_rule is None:
        judgment = "買い増しなし"
    else:
        judgment = f"{dip_rule.label} の目安"

    fields = [
        {
            "name": "現在価格",
            "value": f"`{_fmt_decimal(result.price)} {result.currency}`",
            "inline": True,
        },
        {
            "name": "前日比",
            "value": f"`{_fmt_decimal(result.day_change_percent, '%')}`",
            "inline": True,
        },
        {
            "name": "直近高値",
            "value": f"`{_fmt_decimal(result.recent_high)} {result.currency}`"
            + (f"\n{result.recent_high_date}" if result.recent_high_date else ""),
            "inline": True,
        },
        {
            "name": "直近高値からの下落率",
            "value": f"`{_fmt_decimal(result.drawdown_percent, '%')}`",
            "inline": True,
        },
        {
            "name": "買い増し判定",
            "value": f"**{judgment}**",
            "inline": True,
        },
        {
            "name": "買い増しルール",
            "value": format_rules(),
            "inline": False,
        },
        {
            "name": "取得元",
            "value": f"[{result.source_name}]({result.source_url})",
            "inline": True,
        },
        {
            "name": "取得時刻",
            "value": f"`{timestamp}`",
            "inline": True,
        },
    ]

    payload = {
        "content": mention.strip() if mention.strip() else None,
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color,
                "fields": fields,
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

    payload = {
        "content": mention.strip() if mention.strip() else None,
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
