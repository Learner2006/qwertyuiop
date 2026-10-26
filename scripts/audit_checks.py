import sys, datetime, numpy as np
sys.path.insert(0, "backend")
from app.services.prepare import DataManager
from app.services.models import v1_additive, v2_proportional
from app.services.calibrate import calibrate_daily_forecast

dm = DataManager.get_instance()
days = {}
for d in range(1, 31):
    dd = datetime.date(2026, 1, d); td = dd + datetime.timedelta(days=1)
    fc = dm.select_target_forecast(dd, td); cal = dm.get_calibration_observations(dd); ac = dm.get_target_actuals(td)
    days[d] = dict(F=np.array([x["generation_gw"] for x in fc]),
                   A=np.array([x["generation_gw"] for x in ac]), fc=fc, cal=cal)

def tot(plan_fn, rng):
    sf = su = esf = esu = cut = 0.0
    for d in rng:
        F, A = days[d]["F"], days[d]["A"]; P = plan_fn(d)
        esf += np.maximum(0, F - A).sum() * 500; esu += np.maximum(0, A - F).sum() * 500
        sf += np.maximum(0, P - A).sum() * 500;  su += np.maximum(0, A - P).sum() * 500
        cut += (F - P).sum() * 500
    return dict(avoided=esf - sf, extra=su - esu, cut=cut)

H1, H2, ALL = range(1, 16), range(16, 31), range(1, 31)
models = {
    "v1_add_p75":  lambda d: np.array(v1_additive(days[d]["fc"], days[d]["cal"], 75.0)["plans"]),
    "v2_prop_p75": lambda d: np.array(v2_proportional(days[d]["fc"], days[d]["cal"], 75.0)["plans"]),
    "flat_15":     lambda d: 0.85 * days[d]["F"],
}

print("== 1. Break-even: repo k* = extra/avoided vs correct (avoided+extra)/avoided ==")
for nm, fn in models.items():
    for lab, r in (("sel", H1), ("hold", H2), ("all", ALL)):
        t = tot(fn, r)
        print(f"{nm:12s} {lab:4s} avoided={t['avoided']:>10,.0f} extra={t['extra']:>10,.0f} "
              f"repo_k*={t['extra']/t['avoided']:.3f} correct={(t['avoided']+t['extra'])/t['avoided']:.3f}")

print("\n== 2. Matched-volume test vs flat cut of equal total volume ==")
def flat_for_cut(V, rng):
    lo, hi = 0.0, 0.6
    for _ in range(60):
        m = (lo + hi) / 2
        c = tot(lambda d: (1 - m) * days[d]["F"], rng)["cut"]
        lo, hi = (m, hi) if c < V else (lo, m)
    return lo
for nm, fn in models.items():
    for lab, r in (("sel", H1), ("hold", H2)):
        t = tot(fn, r); m = flat_for_cut(t["cut"], r)
        f = tot(lambda d: (1 - m) * days[d]["F"], r)
        print(f"{nm:12s} {lab:4s} cut={t['cut']:>10,.0f} model={t['avoided']:>10,.0f} "
              f"matched flat ({m*100:4.1f}%)={f['avoided']:>10,.0f} diff={t['avoided']-f['avoided']:>+10,.0f}")

print("\n== 3. Uniform haircut sweep (efficiency falls as cut grows) ==")
for r in (0.02, 0.05, 0.10, 0.13, 0.15, 0.20, 0.25):
    t = tot(lambda d: (1 - r) * days[d]["F"], ALL)
    print(f"cut {r*100:4.1f}% avoided={t['avoided']:>10,.0f} extra={t['extra']:>10,.0f} "
          f"eff={t['avoided']/(t['avoided']+t['extra'])*100:5.1f}% true_break_even={(t['avoided']+t['extra'])/t['avoided']:.3f}")

print("\n== 4. Level bias by half ==")
for lab, r in (("Jan1-15 dec", H1), ("Jan16-30 dec", H2), ("all", ALL)):
    F = sum(days[d]["F"].sum() for d in r); A = sum(days[d]["A"].sum() for d in r)
    print(f"{lab:13s} over-forecast {(F-A)/F*100:.1f}% of forecast ({(F-A)/A*100:.1f}% of outturn)")
rat = np.array([days[d]["A"].sum() / days[d]["F"].sum() for d in ALL])
print("daily actual/forecast: mean %.3f sd %.3f min %.2f max %.2f; days actual>=forecast: %d"
      % (rat.mean(), rat.std(), rat.min(), rat.max(), (rat >= 1).sum()))

print("\n== 5. Band coverage (nominal ~80%) ==")
cov = []
for d in ALL:
    res = calibrate_daily_forecast(days[d]["fc"], days[d]["cal"], 75.0)
    lo = np.array([i["indicative_lower_gw"] for i in res["intervals"]])
    hi = np.array([i["indicative_upper_gw"] for i in res["intervals"]])
    cov.append(((days[d]["A"] >= lo) & (days[d]["A"] <= hi)).mean())
cov = np.array(cov)
print("mean %.1f%% | days1-3 %.1f%% | days4-30 %.1f%% | min %.0f%% max %.0f%%"
      % (cov.mean()*100, cov[:3].mean()*100, cov[3:].mean()*100, cov.min()*100, cov.max()*100))
