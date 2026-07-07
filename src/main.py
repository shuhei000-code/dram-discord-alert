from __future__ import annotations

import sys
import traceback

from .config import load_config
from .investing import fetch_dram_price
from .notifier import send_error_notification, send_price_notification


def main() -> int:
    try:
        config = load_config()
        result = fetch_dram_price(config.investing_url, config.symbol)
        send_price_notification(
            webhook_url=config.discord_webhook,
            result=result,
            timezone=config.timezone,
            mention=config.discord_mention,
        )
        print(f"Notification sent: {result.symbol} {result.price} {result.currency}")
        return 0

    except Exception as exc:
        error_message = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        print(f"ERROR: {error_message}", file=sys.stderr)

        try:
            config = load_config()
            if config.notify_on_error:
                send_error_notification(
                    webhook_url=config.discord_webhook,
                    error_message=error_message,
                    timezone=config.timezone,
                    mention=config.discord_mention,
                )
        except Exception as notify_exc:
            print(f"ERROR: Failed to send error notification: {notify_exc}", file=sys.stderr)

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
