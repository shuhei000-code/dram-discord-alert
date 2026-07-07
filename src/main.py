from __future__ import annotations

import sys
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import load_config
from .investing import fetch_dram_price
from .notifier import send_error_notification, send_status_notification
from .rules import judge_dip
from .state import load_state, save_state


def main() -> int:
    try:
        config = load_config()

        result = fetch_dram_price(
            yahoo_symbol=config.yahoo_symbol,
            display_symbol=config.symbol,
            lookback_range=config.lookback_range,
            timezone=config.timezone,
        )

        dip_rule = judge_dip(result.drawdown_percent)
        state = load_state(config.state_file)

        current_level = dip_rule.level if dip_rule else 0
        should_notify = False
        mode = config.run_mode

        if mode == "daily":
            should_notify = True
        elif current_level > state.last_alert_level:
            should_notify = True
            mode = "alert"

        # Reset alert level after recovery above -5%.
        if current_level == 0 and state.last_alert_level != 0:
            state.last_alert_level = 0

        # Update state when daily report sees a dip, or when a deeper dip alert fires.
        if current_level > 0 and (should_notify or current_level > state.last_alert_level):
            state.last_alert_level = current_level

        now = datetime.now(ZoneInfo(config.timezone))
        state.last_price = str(result.price)
        state.last_drawdown_percent = str(result.drawdown_percent)
        state.last_updated_at = now.isoformat()
        save_state(config.state_file, state)

        if should_notify:
            send_status_notification(
                webhook_url=config.discord_webhook,
                result=result,
                timezone=config.timezone,
                mention=config.discord_mention,
                dip_rule=dip_rule,
                mode=mode,
            )
            print(
                f"Notification sent. mode={mode}, "
                f"price={result.price}, drawdown={result.drawdown_percent}%, "
                f"level={current_level}%"
            )
        else:
            print(
                f"No notification needed. "
                f"price={result.price}, drawdown={result.drawdown_percent}%, "
                f"level={current_level}%, last_alert_level={state.last_alert_level}%"
            )

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
