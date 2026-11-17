"""Leave-one-run-out (LORO) check of the plant model: for each of the ten bench runs, refit the
static map g(POT) WITHOUT that run's points (same knots, smoothing and lag as the final model),
then replay the held-out run in closed loop with nominal gain and report its RMSE.
Output: out/loro.json"""
import json, os
import numpy as np
from scipy.optimize import least_squares
import model as M

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "out", "plant_params.json")))
DIG = json.load(open(os.path.join(HERE, "data", "digitized_traces_raw.json")))
REC = json.load(open(os.path.join(HERE, "data", "bench_records.json"), encoding="utf8"))
RUNS = REC["runs"]
KP = np.array(P["knots_pot"]); LAG = P["lag"]


def trace(rid):
    return (np.array([v[0] for v in tr], float) for tr in DIG[RUNS[rid]["plot"]])


def v_to_pot(V):
    t = REC["triac_210V"]
    ang = np.interp(V, t["V_meas"][::-1], t["angle_deg"][::-1])
    return 100 - ang / 1.8, bool(V < min(t["V_meas"]) or V > max(t["V_meas"]))


points = []
for rid in ["A1-1", "A1-2", "A1-3", "A1-4"]:
    lux, pe, _ = trace(rid); pot = RUNS[rid]["pot0"]
    for k in range(len(lux)):
        points.append((rid, pot, round(lux[k])))
        pot = min(100, max(0, pot + M.ce_lookup(int(round(pe[k])))))
for rid, r in RUNS.items():
    if r["type"] != "A2":
        continue
    lux, _, _ = trace(rid)
    for V, idx in ((r["V_start"], r["ins_sample"] - 2), (r["V_off"], len(lux) - 1)):
        pot, ex = v_to_pot(V)
        if not ex:
            points.append((rid, pot, round(lux[idx])))


def fit(pts):
    ids = sorted({p[0] for p in pts})
    def unpack(th):
        kE = np.cumsum(th[:len(KP)] ** 2); kE[0] = 0.0
        ls = th[len(KP):]; ls = ls - ls.mean()
        return kE, dict(zip(ids, np.exp(ls)))
    def res(th):
        kE, sc = unpack(th)
        return np.array([((0.0 if p <= M.POT_OFF else np.interp(min(p, M.POT_FULL), KP, kE) * sc[r]) - 0.5) - y
                         for r, p, y in pts])
    th0 = np.concatenate([np.sqrt(np.linspace(0, 60, len(KP)) / len(KP) + 0.5), np.zeros(len(ids))])
    return unpack(least_squares(res, th0).x)[0]


def replay(rid, plant):
    r = RUNS[rid]; lux, _, _ = trace(rid); n = len(lux); ext = np.zeros(n); pot0 = r.get("pot0")
    if r["type"] == "A2":
        jump = round(lux[r["ins_sample"] - 1]) - round(lux[r["ins_sample"] - 2])
        ext[r["ins_sample"] - 1: r["rem_sample"] - 1] = jump
        pot0 = M.simulate(plant, M.FuzzyIncremental(r["sp"], 0.0), np.zeros(40), 0.0)["pot"][-1]
    sim = M.simulate(plant, M.FuzzyIncremental(r["sp"], pot0), ext, pot0)
    return sim["r"] - np.round(lux)


out, allerr_in, allerr_out = {}, [], []
for rid in RUNS:
    kE_out = fit([p for p in points if p[0] != rid])
    e_out = replay(rid, M.Plant(KP, kE_out, lag=LAG))
    e_in = replay(rid, M.Plant(KP, P["knots_E"], lag=LAG))
    out[rid] = {"rmse_in_sample": float(np.sqrt(np.mean(e_in ** 2))), "rmse_held_out": float(np.sqrt(np.mean(e_out ** 2)))}
    allerr_in.append(e_in); allerr_out.append(e_out)
    print(rid, round(out[rid]["rmse_in_sample"], 2), round(out[rid]["rmse_held_out"], 2))
pin = float(np.sqrt(np.mean(np.concatenate(allerr_in) ** 2)))
pout = float(np.sqrt(np.mean(np.concatenate(allerr_out) ** 2)))
out["pooled"] = {"rmse_in_sample": pin, "rmse_held_out": pout}
print("pooled", round(pin, 2), round(pout, 2))
json.dump(out, open(os.path.join(HERE, "out", "loro.json"), "w"), indent=2)
