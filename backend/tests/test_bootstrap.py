"""Day-block bootstrap tests (Milestone R7 / Finding F8).

Verifies uncertainty quantification and confidence interval calculation
for outturn performance metrics using whole-day block resampling.
"""

import numpy as np
import pytest

from app.services.prepare import DataManager
from app.services.replay import replay
from app.services.stats import day_block_bootstrap, day_block_bootstrap_summary


def test_bootstrap_synthetic_zero_variance():
    """Identical daily observations should produce zero bootstrap standard error."""
    identical_days = [
        {"avoided_shortfall_mwh": 1000.0, "incremental_surplus_mwh": 500.0}
        for _ in range(20)
    ]

    summary = day_block_bootstrap_summary(
        identical_days,
        k=2.0,
        s=0.0,
        n_resamples=500,
        seed=42,
    )

    # Net point estimate = 20 * (1000 - 500) = 10,000 MWh
    assert summary["net_mwh"]["point_estimate"] == 10000.0
    assert summary["net_mwh"]["ci_lower"] == 10000.0
    assert summary["net_mwh"]["ci_upper"] == 10000.0
    assert summary["net_mwh"]["se"] == 0.0
    assert summary["breakeven_ratio"]["point_estimate"] == 1.5
    assert summary["breakeven_ratio"]["ci_lower"] == 1.5


def test_bootstrap_synthetic_positive_significance():
    """Synthetic dataset with strictly positive net benefit should have high prob_positive."""
    rng = np.random.default_rng(42)
    days = []
    for _ in range(30):
        avoided = float(rng.uniform(2000.0, 5000.0))
        extra = float(rng.uniform(500.0, 1500.0))
        days.append({"avoided_shortfall_mwh": avoided, "incremental_surplus_mwh": extra})

    summary = day_block_bootstrap_summary(days, k=2.0, s=0.0, n_resamples=1000, seed=42)

    assert summary["net_mwh"]["ci_lower"] < summary["net_mwh"]["point_estimate"]
    assert summary["net_mwh"]["point_estimate"] < summary["net_mwh"]["ci_upper"]
    assert summary["net_mwh"]["prob_positive"] == 1.0
    assert summary["net_mwh"]["se"] > 0.0


def test_bootstrap_january_2026_flat15():
    """Day-block bootstrap on January 2026 replay data for flat_15.
    Evaluates point estimates and 95% bootstrap confidence intervals."""
    dm = DataManager.get_instance()
    res = replay("flat_15", range(1, 31), percentile=75.0, dm=dm)

    daily_records = [
        {
            "avoided_shortfall_mwh": d["avoided_shortfall_mwh"],
            "incremental_surplus_mwh": d["extra_supply_mwh"],
        }
        for d in res["per_day"]
    ]

    assert len(daily_records) == 30

    summary = day_block_bootstrap_summary(
        daily_records,
        k=2.0,
        s=0.0,
        n_resamples=2000,
        ci_level=0.95,
        seed=2026,
    )

    # In Jan 2026:
    # Avoided is ~1,016,662 MWh, Extra is ~411,934 MWh
    # Net MWh at k=2 is ~604,728 MWh
    # Break-even ratio is ~1.405x
    net_point = summary["net_mwh"]["point_estimate"]
    assert net_point == pytest.approx(604727.8, abs=2.0)

    # 95% CI should contain the point estimate
    ci_low = summary["net_mwh"]["ci_lower"]
    ci_high = summary["net_mwh"]["ci_upper"]
    assert ci_low < net_point < ci_high

    # Statistically significant positive benefit at k=2
    assert ci_low > 0, "Lower CI bound should be strictly positive"
    assert summary["net_mwh"]["prob_positive"] >= 0.99

    # Break-even ratio CI
    be_point = summary["breakeven_ratio"]["point_estimate"]
    assert be_point == pytest.approx(1.405, abs=0.01)
    assert summary["breakeven_ratio"]["ci_lower"] < be_point < summary["breakeven_ratio"]["ci_upper"]
