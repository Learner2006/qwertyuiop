"""Economic calculations for Wind Day-Ahead Estimator.
Implements correct energy procurement ledger and break-even analysis:
- Net saving: net_saving = [avoided * (k - 1) - extra * (1 - s)] * P_adv
- Break-even multiplier: k* = 1 + (1 - s) * extra / avoided
"""

from typing import Optional


def cut_volume(avoided_mwh: float, extra_mwh: float) -> float:
    """Total volume haircut: Cut = avoided shortfall + incremental extra supply."""
    return avoided_mwh + extra_mwh


def break_even_price_ratio(avoided_mwh: float, extra_mwh: float, s: float = 0.0) -> Optional[float]:
    """Calculates the break-even replacement price premium ratio k* = P_rep / P_adv.
    Returns None if avoided_mwh <= 0 (shortfall was not reduced). No sentinels.
    At s = 0 (unrecoverable surplus): k* = 1 + extra / avoided = (avoided + extra) / avoided.
    """
    if avoided_mwh <= 0.0:
        return None
    return 1.0 + (1.0 - s) * (extra_mwh / avoided_mwh)


def net_saving(
    avoided_mwh: float,
    extra_mwh: float,
    k: float,
    s: float = 0.0,
    p_adv: float = 1.0,
) -> float:
    """Calculates net financial saving from the cautious plan relative to raw forecast.
    net_saving = [avoided * (k - 1) - extra * (1 - s)] * P_adv
    """
    return (avoided_mwh * (k - 1.0) - extra_mwh * (1.0 - s)) * p_adv
