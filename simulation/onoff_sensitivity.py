"""Sensitivity of the on/off baseline to its hysteresis width (reviewer question): +/-10 % and
+/-20 % hysteresis, nominal noise, same paired random draws as compare.py. Output:
out/onoff_hysteresis_sensitivity.csv"""
import csv, os, zlib
import numpy as np
import compare as C
import model as M

rows = []
for h in (0.10, 0.20):
    for sp in (10, 33):
        cases = [("S1", s) for s in C.STEPS[sp]] + [("S2", None), ("S3", None)]
        for scen, step in cases:
            vals = {"in_band_pct": [], "lamp_switches": []}
            for i in range(C.N_MC):
                seed = zlib.crc32(repr(("nominal", sp, scen, step, i)).encode())
                E_ext, events = C.scenario(scen, sp, np.random.default_rng(seed), step)
                pot_on = C.make_plant().pot_for(sp + 0.5)
                plant = C.make_plant(np.random.default_rng(seed + 1))
                ref = plant.g(C.settle_pot(plant, sp))
                c = M.OnOffHysteresis(sp, pot_on, h, on0=True)
                sim = M.simulate(plant, c, E_ext, pot_on, np.random.default_rng(seed + 7), C.SIGMAS["nominal"])
                m = C.metrics(sim, sp, ref, list(events) if events else None, c.switches, E_ext)
                for k in vals: vals[k].append(m[k])
            rows.append({"hysteresis": h, "sp": sp, "scenario": scen, "step": step or "",
                         **{f"{k}_mean": float(np.mean(v)) for k, v in vals.items()},
                         **{f"{k}_sd": float(np.std(v, ddof=1)) for k, v in vals.items()}})
            print(h, sp, scen, step, round(rows[-1]["in_band_pct_mean"], 1), round(rows[-1]["lamp_switches_mean"], 1))
with open(os.path.join(C.OUT, "onoff_hysteresis_sensitivity.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
