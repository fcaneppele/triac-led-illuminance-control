"""Identify the plant (command -> illuminance at the sensor) from the bench records and
validate the closed-loop model against all ten single-run bench tests.

Outputs (in ./out):
    plant_params.json        identified static map, lag, run-to-run variability, noise level
    identification_report.md numbers for the experimental log
    fig_identification.png   static map + closed-loop validation (diagnostic, not for the paper)
"""
from __future__ import annotations

import json
import os

import numpy as np
from scipy.optimize import least_squares

import model as M

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
DIG = json.load(open(os.path.join(HERE, "data", "digitized_traces_raw.json")))
REC = json.load(open(os.path.join(HERE, "data", "bench_records.json"), encoding="utf8"))
RUNS = REC["runs"]


def trace(run_id):
    lux, pe, ce = ([None if v is None else v[0] for v in tr] for tr in DIG[RUNS[run_id]["plot"]])
    return np.array(lux, float), np.array(pe, float), np.array(ce, float)


def v_to_pot(V):
    """Measured V(angle) at 210 V (monotone) -> firing angle -> Uno command POT."""
    t = REC["triac_210V"]
    ang = np.interp(V, t["V_meas"][::-1], t["angle_deg"][::-1])
    return 100 - ang / 1.8, bool(V < min(t["V_meas"]) or V > max(t["V_meas"]))


# ------------------------------------------------------------------ 1. static-map data points
points = []          # (run, pot, reading)
for rid in ["A1-1", "A1-2", "A1-3", "A1-4"]:
    lux, pe, _ = trace(rid)
    pot = RUNS[rid]["pot0"]
    for k in range(len(lux)):
        points.append((rid, pot, round(lux[k])))
        # command applied after sample k: CE recomputed from the logged PE with the code's FIS
        pot = min(100, max(0, pot + M.ce_lookup(int(round(pe[k])))))
for rid, r in RUNS.items():          # A2 dark steady states (before insertion, after removal)
    if r["type"] != "A2":
        continue
    lux, _, _ = trace(rid)
    for V, idx in ((r["V_start"], r["ins_sample"] - 2), (r["V_off"], len(lux) - 1)):
        pot, extrap = v_to_pot(V)
        if not extrap:
            points.append((rid, pot, round(lux[idx])))

run_ids = sorted({p[0] for p in points})
KNOTSETS = {"fine": [10, 15, 20, 25, 30, 40, 50, 60, 70], "coarse": [10, 20, 30, 40, 50, 60, 70],
            "coarse+80": [10, 20, 30, 40, 50, 60, 70, 80]}
KNOTSET = os.environ.get("KNOTSET", "fine")
KP = np.array([M.POT_OFF] + KNOTSETS[KNOTSET] + [M.POT_FULL])
LAMBDA_SMOOTH = float(os.environ.get("LAMBDA_SMOOTH", "0"))  # curvature penalty weight


def unpack(theta):
    inc = theta[:len(KP)] ** 2                 # monotone non-decreasing map
    kE = np.cumsum(inc)
    kE[0] = 0.0
    logs = theta[len(KP):]
    logs = logs - logs.mean()                  # run scales have geometric mean 1
    return kE, dict(zip(run_ids, np.exp(logs)))


def resid(theta):
    kE, sc = unpack(theta)
    res = []
    for rid, pot, r in points:
        E = 0.0 if pot <= M.POT_OFF else np.interp(min(pot, M.POT_FULL), KP, kE) * sc[rid]
        res.append((E - 0.5) - r)              # truncating quantiser: reading ~ E - 0.5
    slope = np.diff(kE) / np.diff(KP)
    return np.array(res)

def resid_reg(theta):
    kE, _ = unpack(theta)
    slope = np.diff(kE) / np.diff(KP)
    return np.concatenate([resid(theta), LAMBDA_SMOOTH * 10 * np.diff(slope)])


theta0 = np.concatenate([np.sqrt(np.linspace(0, 60, len(KP)) / len(KP) + 0.5), np.zeros(len(run_ids))])
fit = least_squares(resid_reg, theta0)
kE, scales = unpack(fit.x)
res = resid(fit.x)
s_vals = np.array(list(scales.values()))
sigma_scale = float(np.std(np.log(s_vals), ddof=1))

# ------------------------------------------------------------------ 2. lag (first-order) by closed-loop replay


def replay(rid, plant, rng=None, sigma=0.0):
    r = RUNS[rid]
    lux, _, _ = trace(rid)
    n = len(lux)
    ext = np.zeros(n)
    pot0 = r.get("pot0", None)
    if r["type"] == "A2":
        pre = lux[r["ins_sample"] - 2]
        jump = round(lux[r["ins_sample"] - 1]) - round(pre)      # step seen by the sensor
        ext[r["ins_sample"] - 1: r["rem_sample"] - 1] = jump
        settle = M.simulate(plant, M.FuzzyIncremental(r["sp"], 0.0), np.zeros(40), 0.0)
        pot0 = settle["pot"][-1]
    ctrl = M.FuzzyIncremental(r["sp"], pot0)
    sim = M.simulate(plant, ctrl, ext, pot0, rng, sigma)
    return lux, sim, ext


def replay_error(lag, scale_mode):
    errs = []
    for rid in RUNS:
        sc = scales.get(rid, 1.0) if scale_mode == "fitted" else 1.0
        p = M.Plant(KP, kE, lag=lag, scale=sc)
        lux, sim, _ = replay(rid, p)
        errs.append(sim["r"] - np.round(lux))
    e = np.concatenate(errs)
    return float(np.sqrt(np.mean(e ** 2)))


lags = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
lag_scores = {lag: replay_error(lag, "nominal") for lag in lags}
best_lag = min(lag_scores, key=lag_scores.get)   # criterion: pooled closed-loop RMSE, nominal gain

# ------------------------------------------------------------------ 3. sensor temporal noise from steady segments
changes, transitions = 0, 0
for rid in RUNS:
    lux, _, ce = trace(rid)
    r = np.round(lux)
    for k in range(1, len(r)):
        if abs(ce[k - 1]) < 0.3 and abs(ce[k]) < 0.3:          # command unchanged
            ev = RUNS[rid]
            if ev["type"] == "A2" and k + 1 in (ev["ins_sample"], ev["rem_sample"]):
                continue
            transitions += 1
            changes += int(r[k] != r[k - 1])


def flicker_rate(sigma, n=200000, seed=1):
    g = np.random.default_rng(seed)
    x0 = g.uniform(0, 1, n)                                   # position inside a raw-count bin
    a = np.round(x0 + g.normal(0, sigma, n))
    b = np.round(x0 + g.normal(0, sigma, n))
    return float(np.mean(a != b))


sig_grid = np.linspace(0.01, 0.6, 60)
rates = np.array([flicker_rate(s) for s in sig_grid])
obs_rate = changes / transitions
sigma_nom = float(np.interp(obs_rate, rates, sig_grid))
# one-sided 95 % upper bound on the rate (exact binomial / Clopper-Pearson)
from scipy.stats import beta as _beta
rate_up = float(_beta.ppf(0.95, changes + 1, transitions - changes))
sigma_up = float(np.interp(rate_up, rates, sig_grid))

# ------------------------------------------------------------------ 4. validation table
val = []
for rid in RUNS:
    for mode in ("fitted", "nominal"):
        sc = scales.get(rid, 1.0) if mode == "fitted" else 1.0
        p = M.Plant(KP, kE, lag=best_lag, scale=sc)
        lux, sim, ext = replay(rid, p)
        e = sim["r"] - np.round(lux)
        val.append({"run": rid, "scale_mode": mode, "n": len(e),
                    "rmse_counts": float(np.sqrt(np.mean(e ** 2))),
                    "max_abs_counts": float(np.max(np.abs(e))),
                    "final_meas": float(np.round(lux[-1])), "final_sim": int(sim["r"][-1]),
                    "ext_step_counts": float(ext.max())})

params = {
    "knots_pot": KP.tolist(), "knots_E": kE.tolist(), "lag": best_lag,
    "lag_scores_rmse_counts": {str(k): v for k, v in lag_scores.items()},
    "run_scales": scales, "sigma_log_scale": sigma_scale,
    "static_fit_rmse_counts": float(np.sqrt(np.mean(res ** 2))), "n_static_points": len(points),
    "noise": {"changes": changes, "transitions": transitions, "rate": obs_rate,
              "rate_upper95": rate_up, "sigma_raw_nominal": sigma_nom, "sigma_raw_upper95": sigma_up},
    "validation": val, "knotset": KNOTSET, "lambda_smooth": LAMBDA_SMOOTH,
    "pooled_rmse_nominal": lag_scores[best_lag],
}
json.dump(params, open(os.path.join(OUT, "plant_params.json"), "w"), indent=2)

# ------------------------------------------------------------------ 5. report + diagnostic figure
lines = ["# Identification report (generated by identify.py)\n",
         f"* Static-map points: {len(points)} (A1 replays + A2 dark steady states via measured V(angle)).",
         f"* Static-map fit RMSE: {params['static_fit_rmse_counts']:.2f} counts.",
         "* Static map E(POT) knots: " + ", ".join(f"{p:.1f}%→{e:.1f} lx" for p, e in zip(KP, kE)),
         "* Run-to-run gain factors: " + ", ".join(f"{k} {v:.3f}" for k, v in scales.items()),
         f"* SD of log run gain: {sigma_scale:.3f}",
         "* Pooled closed-loop validation RMSE vs lag (nominal gain): " + ", ".join(f"{k}: {v:.2f}" for k, v in lag_scores.items()),
         f"* Knot set: {KNOTSET}; smoothing weight: {LAMBDA_SMOOTH}",
         f"* Selected lag factor: {best_lag} (pooled RMSE {lag_scores[best_lag]:.2f} counts)",
         f"* Steady-segment flicker: {changes} changes in {transitions} transitions (rate {obs_rate:.4f}; 95 % upper {rate_up:.4f})",
         f"* Sensor noise (raw counts): nominal {sigma_nom:.3f}; upper 95 % {sigma_up:.3f}",
         "\n| Run | Gain mode | n | RMSE (counts) | max abs (counts) | final meas | final sim |",
         "|---|---|---:|---:|---:|---:|---:|"]
for v in val:
    lines.append(f"| {v['run']} | {v['scale_mode']} | {v['n']} | {v['rmse_counts']:.2f} | {v['max_abs_counts']:.0f} | {v['final_meas']:.0f} | {v['final_sim']} |")
open(os.path.join(OUT, "identification_report.md"), "w", encoding="utf8").write("\n".join(lines) + "\n")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(3, 4, figsize=(16, 10))
ax = axes[0, 0]
for rid in run_ids:
    pp = [(p, r) for q, p, r in points if q == rid]
    ax.plot(*zip(*pp), "o", ms=4, label=rid)
xx = np.linspace(0, 100, 400)
ax.plot(xx, [M.Plant(KP, kE).g(x) - 0.5 for x in xx], "k-")
ax.set_xlabel("POT (%)"); ax.set_ylabel("reading"); ax.legend(fontsize=6)
for i, rid in enumerate(RUNS):
    ax = axes.flat[i + 1]
    p = M.Plant(KP, kE, lag=best_lag, scale=1.0)
    lux, sim, _ = replay(rid, p)
    ax.plot(range(1, len(lux) + 1), np.round(lux), "ko-", ms=3, label="digitised")
    ax.plot(range(1, len(lux) + 1), sim["r"], "s--", ms=3, label="model")
    ax.set_title(rid); ax.legend(fontsize=6)
axes.flat[-1].axis("off")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_identification.png"), dpi=110)
print("\n".join(lines))
