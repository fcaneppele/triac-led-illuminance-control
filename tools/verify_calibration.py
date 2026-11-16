"""Recompute the calibration statistics from data/*.csv."""
import csv, os
import numpy as np
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

def load(name):
    rows = list(csv.reader(open(os.path.join(D, name))))[1:]
    return np.array([float(r[0]) for r in rows]), np.array([float(r[2]) for r in rows])

for name in ("calibration_raw_n26.csv", "calibration_corrected_n22.csv"):
    x, y = load(name)
    a, b = np.polyfit(x, y, 1); res = y - (a * x + b)
    r2 = 1 - (res ** 2).sum() / ((y - y.mean()) ** 2).sum()
    print(f"{name}: n={len(x)} slope={a:.4f} intercept={b:.4f} R2={r2:.4f} "
          f"RMSE={np.sqrt((res**2).mean()):.3f} lx MAE={np.abs(res).mean():.3f} lx (regression residuals)")
    if "corrected" in name:
        d = x - y
        print(f"  direct agreement (corrected - luxmeter): mean={d.mean():.3f} lx SD={d.std(ddof=1):.3f} lx "
              f"RMSE={np.sqrt((d**2).mean()):.3f} lx MAE={np.abs(d).mean():.3f} lx")
