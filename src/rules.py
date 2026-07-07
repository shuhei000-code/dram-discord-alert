from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DipRule:
    level: int
    shares: int
    label: str


RULES = [
    DipRule(level=30, shares=5, label="-30%以上：5株追加"),
    DipRule(level=20, shares=4, label="-20%：4株追加"),
    DipRule(level=10, shares=2, label="-10%：2株追加"),
    DipRule(level=5, shares=1, label="-5%：1株追加"),
]


def judge_dip(drawdown_percent: Decimal) -> DipRule | None:
    """Return the strongest dip rule reached.

    drawdown_percent is negative when the price is below the recent high.
    """
    abs_drawdown = abs(drawdown_percent)

    for rule in RULES:
        if abs_drawdown >= Decimal(rule.level):
            return rule

    return None


def format_rules() -> str:
    return "\n".join(
        [
            "-5%：1株追加",
            "-10%：2株追加",
            "-20%：4株追加",
            "-30%以上：5株追加",
        ]
    )
