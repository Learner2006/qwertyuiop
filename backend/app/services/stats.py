"""Statistical utilities and uncertainty quantification (Milestone R7 / Finding F8).

Provides day-block bootstrap confidence intervals for outturn evaluation.
Because half-hourly energy settlements within a day are autocorrelated,
resampling is conducted at the whole-day block level (48 settlement intervals per block)
rather than naive i.i.d. interval resampling.
"""

from typing import Any, Callable, Dict, List, Optional
import numpy as np


def day_block_bootstrap(
    daily_records: List[Dict[str, float]],
    stat_fn: Callable[[np.ndarray, np.ndarray], float],
    n_resamples: int = 2000,
    ci_level: float = 0.95,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Computes a day-block bootstrap estimate and confidence interval for a statistic.

    Args:
        daily_records: List of dicts, each containing 'avoided_shortfall_mwh' and 'incremental_surplus_mwh'.
        stat_fn: Function taking (avoided_vector, surplus_vector) of length N and returning a float.
        n_resamples: Number of bootstrap draws (default 2000).
        ci_level: Confidence interval coverage (default 0.95).
        seed: Random seed for reproducibility.

    Returns:
        Dict with point_estimate, ci_lower, ci_upper, standard_error, prob_positive, n_days.
    """
    n_days = len(daily_records)
    if n_days == 0:
        return {
            "point_estimate": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "standard_error": 0.0,
            "prob_positive": 0.0,
            "n_days": 0,
            "ci_level": ci_level,
        }

    avoided = np.array([r.get("avoided_shortfall_mwh", 0.0) for r in daily_records], dtype=np.float64)
    surplus = np.array([r.get("incremental_surplus_mwh", 0.0) for r in daily_records], dtype=np.float64)

    point_estimate = float(stat_fn(avoided, surplus))

    rng = np.random.default_rng(seed)
    indices = rng.integers(0, n_days, size=(n_resamples, n_days))

    # Evaluate stat_fn on each resample
    boot_stats = np.empty(n_resamples, dtype=np.float64)
    for b in range(n_resamples):
        idx = indices[b]
        boot_stats[b] = stat_fn(avoided[idx], surplus[idx])

    alpha = (1.0 - ci_level) / 2.0
    ci_lower = float(np.percentile(boot_stats, alpha * 100.0))
    ci_upper = float(np.percentile(boot_stats, (1.0 - alpha) * 100.0))
    standard_error = float(np.std(boot_stats, ddof=1)) if n_resamples > 1 else 0.0
    prob_positive = float(np.mean(boot_stats > 0.0))

    return {
        "point_estimate": round(point_estimate, 1),
        "ci_lower": round(ci_lower, 1),
        "ci_upper": round(ci_upper, 1),
        "standard_error": round(standard_error, 1),
        "prob_positive": round(prob_positive, 4),
        "is_significant": bool(ci_lower > 0.0 or ci_upper < 0.0),
        "n_days": n_days,
        "n_resamples": n_resamples,
        "ci_level": ci_level,
    }


def day_block_bootstrap_summary(
    daily_records: List[Dict[str, float]],
    k: float = 2.0,
    s: float = 0.0,
    p_adv: float = 1.0,
    n_resamples: int = 2000,
    ci_level: float = 0.95,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generates day-block bootstrap confidence intervals for key performance metrics:
    - Net MWh-equivalent: sum(avoided * (k - 1) - extra * (1 - s)) * p_adv
    - Total Avoided Shortfall MWh
    - Total Incremental Surplus MWh
    - Break-Even Price Ratio k*: 1 + (1 - s) * (sum(extra) / sum(avoided))
    """
    n_days = len(daily_records)
    if n_days == 0:
        return {}

    avoided = np.array([r.get("avoided_shortfall_mwh", 0.0) for r in daily_records], dtype=np.float64)
    surplus = np.array([r.get("incremental_surplus_mwh", 0.0) for r in daily_records], dtype=np.float64)

    rng = np.random.default_rng(seed)
    indices = rng.integers(0, n_days, size=(n_resamples, n_days))

    # 1. Total Avoided Shortfall
    tot_avoided_point = float(np.sum(avoided))
    boot_avoided = np.sum(avoided[indices], axis=1)

    # 2. Total Incremental Surplus
    tot_surplus_point = float(np.sum(surplus))
    boot_surplus = np.sum(surplus[indices], axis=1)

    # 3. Net saving / Net MWh
    net_point = float((tot_avoided_point * (k - 1.0) - tot_surplus_point * (1.0 - s)) * p_adv)
    boot_net = (boot_avoided * (k - 1.0) - boot_surplus * (1.0 - s)) * p_adv

    # 4. Break-even ratio
    be_point = float(1.0 + (1.0 - s) * (tot_surplus_point / max(tot_avoided_point, 1e-9)))
    denom = np.maximum(boot_avoided, 1e-9)
    boot_be = 1.0 + (1.0 - s) * (boot_surplus / denom)

    alpha = (1.0 - ci_level) / 2.0
    low_pct = alpha * 100.0
    high_pct = (1.0 - alpha) * 100.0

    return {
        "n_days": n_days,
        "n_resamples": n_resamples,
        "ci_level": ci_level,
        "net_mwh": {
            "point_estimate": round(net_point, 1),
            "ci_lower": round(float(np.percentile(boot_net, low_pct)), 1),
            "ci_upper": round(float(np.percentile(boot_net, high_pct)), 1),
            "se": round(float(np.std(boot_net, ddof=1)), 1),
            "prob_positive": round(float(np.mean(boot_net > 0.0)), 4),
            "k": k,
            "s": s,
        },
        "avoided_shortfall_mwh": {
            "point_estimate": round(tot_avoided_point, 1),
            "ci_lower": round(float(np.percentile(boot_avoided, low_pct)), 1),
            "ci_upper": round(float(np.percentile(boot_avoided, high_pct)), 1),
            "se": round(float(np.std(boot_avoided, ddof=1)), 1),
        },
        "incremental_surplus_mwh": {
            "point_estimate": round(tot_surplus_point, 1),
            "ci_lower": round(float(np.percentile(boot_surplus, low_pct)), 1),
            "ci_upper": round(float(np.percentile(boot_surplus, high_pct)), 1),
            "se": round(float(np.std(boot_surplus, ddof=1)), 1),
        },
        "breakeven_ratio": {
            "point_estimate": round(be_point, 3),
            "ci_lower": round(float(np.percentile(boot_be, low_pct)), 3),
            "ci_upper": round(float(np.percentile(boot_be, high_pct)), 3),
            "se": round(float(np.std(boot_be, ddof=1)), 3),
        },
    }
