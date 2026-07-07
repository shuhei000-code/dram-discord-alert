from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class AlertState:
    last_alert_level: int = 0
    last_price: str | None = None
    last_drawdown_percent: str | None = None
    last_updated_at: str | None = None


def load_state(path: str) -> AlertState:
    state_path = Path(path)
    if not state_path.exists():
        return AlertState()

    try:
        data: dict[str, Any] = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return AlertState()

    return AlertState(
        last_alert_level=int(data.get("last_alert_level") or 0),
        last_price=data.get("last_price"),
        last_drawdown_percent=data.get("last_drawdown_percent"),
        last_updated_at=data.get("last_updated_at"),
    )


def save_state(path: str, state: AlertState) -> None:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(asdict(state), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
