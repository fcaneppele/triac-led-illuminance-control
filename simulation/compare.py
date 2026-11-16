"""Monte Carlo comparison: fuzzy incremental controller (as implemented) vs on/off with
hysteresis, plus a linear integral law with the fuzzy small-signal gain (equivalence check).

ALL RESULTS ARE SIMULATED with the plant identified in identify.py (out/plant_params.json).

Scenarios (external light at the sensor, lux-meter scale):
  S1  bench-like steps: magnitudes equal to the sensor jumps observed on the bench
      (SP 10: 2, 6, 12 lx; SP 33: 1, 7, 12 lx), on for 30 cycles.
  S2  SYNTHETIC slow daylight: linear rise 0 -> 1.5*SP in 10 min, hold 10 min, fall in 10 min.
  S3  SYNTHETIC cloudy daylight: S2 multiplied by a random two-state cloud factor (1.0 / 0.4)
      with geometric dwell times (mean 20 cycles = 1 min).

Random per Monte Carlo run: plant gain factor exp(N(0, sigma_log_scale)) (identified run-to-run
spread), sensor temporal noise, step magnitude jitter U(-0.5, 0.5) lx, cloud sequence.
The on/off "ON" level is commissioned once on the nominal plant (command giving the setpoint in
darkness); the fuzzy and integral loops start settled at the setpoint in darkness.
"""
from __future__ import annotations

import csv
import json
import os

import zlib

import numpy as np

import model as M

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
P = json.load(open(os.path.join(OUT, "plant_params.json")))
N_MC = int(os.environ.get("N_MC", "200"))
H_ONOFF = 0.20            # +/-20 % band: tolerance quoted in the dissertation's management source
BAND = 0.20               # in-band criterion for the metrics (same tolerance)
K_INT = abs(M.ce_lookup(10)) / 10       # small-signal slope of the executed FIS (~0.16 %/%)
RATE = abs(M.ce_lookup(100))            # FIS saturation (~9.46 %)
SIGMAS = {"nominal": P["noise"]["sigma_raw_upper95"], "stress": 0.60}
STEPS = {10: [2, 6, 12], 33: [1, 7, 12]}
MIN_DWELL = 20            # on/off-dwell variant: 1 min minimum in each state (assumed, anti-short-cycling)


def make_plant(rng=None):
    s = 1.0 if rng is None else float(np.exp(rng.normal(0, P["sigma_log_scale"])))
    return M.Plant(P["knots_pot"], P["knots_E"], lag=P["lag"], scale=s)


def scenario(name, sp, rng, step=None):
    if name == "S1":
        a = step + rng.uniform(-0.5, 0.5)
        e = np.zeros(60); e[10:40] = a
        return e, (10, 40)
    ramp = np.concatenate([np.linspace(0, 1, 200), np.ones(200), np.linspace(1, 0, 200)]) * 1.5 * sp
    if name == "S2":
        return ramp, None
    f, state, out = 1.0, 1, []
    for _ in range(len(ramp)):
        if rng.random() < 1 / 20:
            state = 1 - state
        out.append(1.0 if state else 0.4)
    return ramp * np.array(out), None


def settle_pot(plant, sp):
    sim = M.simulate(plant, M.FuzzyIncremental(sp, 0.0), np.zeros(60), 0.0)
    return float(sim["pot"][-1])


def metrics(sim, sp, ref_E_led, events, switches, E_ext):
    """Error metrics only over controllable samples (external light alone below 0.95*SP):
    when daylight alone exceeds the target no dimming controller can hold it."""
    r = sim["r"].astype(float)
    err = np.abs(r - sp) / sp
    ctl = E_ext < 0.95 * sp
    lit = sim["pot"] > M.POT_OFF
    m = {"mae_pct": 100 * err[ctl].mean(),
         "in_band_pct": 100 * np.mean(err[ctl] <= BAND),
         "max_dev_pct": 100 * err[ctl].max(),
         "uncontrollable_pct": 100 * np.mean(~ctl),
         "lamp_switches": int(switches if switches is not None else np.sum(lit[1:] != lit[:-1])),
         "art_light_rel_pct": 100 * sim["E_led"].mean() / ref_E_led}
    if events:
        rec = []
        for ev in events:
            ok = err <= BAND
            k = ev
            while k < len(ok) - 2 and not (ok[k] and ok[k + 1] and ok[k + 2]):
                k += 1
            rec.append(3 * (k - ev))
        m["recovery_s_on"], m["recovery_s_off"] = rec
    return m


def run_all():
    rows, examples = [], {}
    for noise_name, sigma in SIGMAS.items():
        for sp in (10, 33):
            cases = [("S1", s) for s in STEPS[sp]] + [("S2", None), ("S3", None)]
            for scen, step in cases:
                for i in range(N_MC):
                    seed = zlib.crc32(repr((noise_name, sp, scen, step, i)).encode())  # reproducible
                    rng_s = np.random.default_rng(seed)
                    E_ext, events = scenario(scen, sp, rng_s, step)
                    gain_seed = seed + 1
                    nominal = make_plant()
                    pot_on = nominal.pot_for(sp + 0.5)               # commissioned in darkness
                    for ctrl_name in ("fuzzy", "integral", "on/off", "on/off-dwell"):
                        plant = make_plant(np.random.default_rng(gain_seed))
                        ref = plant.g(settle_pot(plant, sp))
                        p0 = settle_pot(plant, sp)
                        if ctrl_name == "fuzzy":
                            c = M.FuzzyIncremental(sp, p0)
                        elif ctrl_name == "integral":
                            c = M.IntegralEquivalent(sp, p0, K_INT, RATE)
                        elif ctrl_name == "on/off":
                            c, p0 = M.OnOffHysteresis(sp, pot_on, H_ONOFF, on0=True), pot_on
                        else:   # minimum 20 cycles (1 min) in each state
                            c, p0 = M.OnOffHysteresis(sp, pot_on, H_ONOFF, on0=True, min_dwell=MIN_DWELL), pot_on
                        sim = M.simulate(plant, c, E_ext, p0, np.random.default_rng(seed + 7), sigma)
                        mt = metrics(sim, sp, ref, list(events) if events else None,
                                     getattr(c, "switches", None), E_ext)
                        rows.append({"noise": noise_name, "sp": sp, "scenario": scen,
                                     "step": step if step is not None else "", "mc": i,
                                     "controller": ctrl_name, **mt})
                        if i == 0 and noise_name == "nominal":
                            examples[f"{scen}_{sp}_{step}_{ctrl_name}"] = {
                                "E_ext": E_ext.tolist(), "r": sim["r"].tolist(), "pot": sim["pot"].tolist()}
    return rows, examples


def summarise(rows):
    import itertools
    keys = ["mae_pct", "in_band_pct", "max_dev_pct", "uncontrollable_pct", "lamp_switches", "art_light_rel_pct",
            "recovery_s_on", "recovery_s_off"]
    groups = {}
    for r in rows:
        groups.setdefault((r["noise"], r["sp"], r["scenario"], str(r["step"]), r["controller"]), []).append(r)
    summ = []
    for g, rs in groups.items():
        d = {"noise": g[0], "sp": g[1], "scenario": g[2], "step": g[3], "controller": g[4], "n": len(rs)}
        for k in keys:
            v = np.array([x[k] for x in rs if k in x], float)
            if len(v):
                d[k + "_mean"], d[k + "_sd"] = float(v.mean()), float(v.std(ddof=1))
                d[k + "_p2.5"], d[k + "_p97.5"] = float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))
        summ.append(d)
    # paired differences fuzzy - on/off and fuzzy - integral (same random draws), bootstrap 95 % CI
    diffs = []
    rng = np.random.default_rng(0)
    for g in {(r["noise"], r["sp"], r["scenario"], str(r["step"])) for r in rows}:
        for other in ("on/off", "on/off-dwell", "integral"):
            for k in ("mae_pct", "in_band_pct", "lamp_switches", "art_light_rel_pct"):
                a = {r["mc"]: r[k] for r in rows if (r["noise"], r["sp"], r["scenario"], str(r["step"])) == g and r["controller"] == "fuzzy"}
                b = {r["mc"]: r[k] for r in rows if (r["noise"], r["sp"], r["scenario"], str(r["step"])) == g and r["controller"] == other}
                d = np.array([a[i] - b[i] for i in a])
                boots = [rng.choice(d, len(d)).mean() for _ in range(2000)]
                diffs.append({"noise": g[0], "sp": g[1], "scenario": g[2], "step": g[3],
                              "comparison": f"fuzzy - {other}", "metric": k,
                              "mean_diff": float(d.mean()), "ci_low": float(np.percentile(boots, 2.5)),
                              "ci_high": float(np.percentile(boots, 97.5))})
    return summ, diffs


if __name__ == "__main__":
    rows, examples = run_all()
    summ, diffs = summarise(rows)
    for name, data in (("mc_runs.csv", rows), ("summary.csv", summ), ("paired_differences.csv", diffs)):
        keys = sorted({k for d in data for k in d}, key=lambda k: list(data[0]).index(k) if k in data[0] else 99)
        with open(os.path.join(OUT, name), "w", newline="", encoding="utf8") as f:
            w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(data)
    json.dump({"settings": {"N_MC": N_MC, "H_onoff": H_ONOFF, "band": BAND, "K_int": K_INT,
                            "rate": RATE, "sigmas": SIGMAS, "steps": STEPS, "min_dwell": MIN_DWELL},
               "examples": examples}, open(os.path.join(OUT, "examples.json"), "w"))
    print(f"runs: {len(rows)}; groups: {len(summ)}")
