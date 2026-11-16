"""Discrete-time model of the bench prototype (one step = one 3 s control cycle).

Every element below reproduces something documented in the dissertation's source code or
measurements; nothing is tuned here.  Plant parameters (static map g, lag, variability) are
identified separately in identify.py from the logged bench runs.

Signal chain per cycle k (as in the MATLAB/Arduino code):
    E_k      true illuminance at the sensor [lux-meter scale]
    raw_k    BH1750 integer reading = round((E_k + 0.4562)/0.7777 + noise)  (inverse of calibration)
    r_k      corrected integer reading = int(0.7777*raw_k - 0.4562)        (Mega, `int lux2`)
    PE_k     int(r_k*100/SP) - 100, clipped to [-100, 100], firmware dead band   (Mega)
    CE_k     Mamdani FIS (code parameters, CP = [0 9 15 15]), CE = 0 if PE = 0  (MATLAB)
    POT_k    clip(POT_{k-1} + CE_k, 0, 100); |CE| > 15 discarded             (Uno)
    E_{k+1}  = g(POT_k) * s + E_ext,k+1  (with optional first-order lag on the LED term)
"""
from __future__ import annotations

import numpy as np

CAL_A, CAL_B = 0.7777, -0.4562          # Eq. (9): corrected = 0.7777*raw - 0.4562
# Uno: delay = 83.33*(100-POT) us; no firing if delay >= 8000 us; gate held high if delay <= 820 us
POT_OFF = 100 - 8000 / 83.33             # ~4.0 %: at or below, lamps receive no firing pulse
POT_FULL = 100 - 820 / 83.33             # ~90.2 %: at or above, full conduction
DEADBAND = {33: 5, 10: 9}                # Mega firmware: |PE| <= 5 (SP 33) or <= 9 (SP 10) -> PE = 0


# ----------------------------------------------------------------------------- FIS
def _trap(x, a, b, c, d):
    y = np.zeros_like(x, dtype=float)
    if b > a:
        y = np.where((x > a) & (x < b), (x - a) / (b - a), y)
    y = np.where((x >= b) & (x <= c), 1.0, y)
    if d > c:
        y = np.where((x > c) & (x < d), (d - x) / (d - c), y)
    return y


def _tri(x, a, b, c):
    return np.clip(np.minimum((x - a) / (b - a), (c - x) / (c - b)), 0, 1)


def fis_ce(pe: float, cp_b: float = 9.0) -> float:
    """Mamdani min-max, centroid; parameters from the executed MATLAB script (Appendix C)."""
    if pe == 0:
        return 0.0                                   # `if e0==0, vo=0`
    e = np.array([float(pe)])
    en = _trap(e, -100, -100, -50, 0)[0]
    stp = _tri(e, -50, 0, 50)[0]
    ep = _trap(e, 0, 50, 100, 100)[0]
    v = np.round(np.arange(-15, 15.0001, 0.1), 10)
    cn = _trap(v, -15, -15, -9, 0)
    cm = _tri(v, -9, 0, 9)
    cpm = _trap(v, 0, cp_b, 15, 15)
    agg = np.maximum(np.minimum(cn, ep), np.maximum(np.minimum(cm, stp), np.minimum(cpm, en)))
    return float((v * agg).sum() / agg.sum())


# PE produced by the firmware is always an integer (C integer arithmetic) -> lookup table
_CE_TABLE = {pe: fis_ce(pe) for pe in range(-100, 101)}


def ce_lookup(pe: int) -> float:
    return _CE_TABLE[int(pe)]


# ----------------------------------------------------------------------------- sensor / firmware
def sensor_reading(E: float, rng: np.random.Generator | None, sigma_raw: float) -> int:
    """True illuminance -> BH1750 raw count -> corrected integer reading (`int lux2`)."""
    x = (max(E, 0.0) - CAL_B) / CAL_A
    if rng is not None and sigma_raw > 0:
        x += rng.normal(0.0, sigma_raw)
    raw = max(int(round(x)), 0)
    return int(CAL_A * raw + CAL_B)                  # C cast truncates toward zero


def firmware_pe(r: int, sp: int) -> int:
    pe = int(r * 100 / sp) - 100 if r >= 0 else -100   # (lux2*100/Set_point)-100, int arithmetic
    pe = max(-100, min(100, pe))
    if abs(pe) <= DEADBAND.get(sp, 0):
        pe = 0
    return pe


# ----------------------------------------------------------------------------- plant
class Plant:
    """LED illuminance at the sensor as a function of the Uno command POT (0-100 %)."""

    def __init__(self, knots_pot, knots_E, lag: float = 1.0, scale: float = 1.0):
        self.kp = np.asarray(knots_pot, float)
        self.kE = np.asarray(knots_E, float)
        self.lag = lag          # fraction of the step towards the static value reached per cycle
        self.scale = scale      # run-to-run gain factor (identified variability)
        self.E_led = 0.0

    def g(self, pot: float) -> float:
        if pot <= POT_OFF:
            return 0.0
        pot = min(pot, POT_FULL)
        return float(np.interp(pot, self.kp, self.kE)) * self.scale

    def reset(self, pot: float):
        self.E_led = self.g(pot)

    def step(self, pot: float) -> float:
        self.E_led += self.lag * (self.g(pot) - self.E_led)
        return self.E_led

    def pot_for(self, E_target: float) -> float:
        """Smallest command giving E_target in steady state (used to commission on/off)."""
        grid = np.linspace(0, 100, 10001)
        vals = np.array([self.g(p) for p in grid])
        idx = np.argmax(vals >= E_target)
        return float(grid[idx]) if vals[idx] >= E_target else 100.0


# ----------------------------------------------------------------------------- controllers
class FuzzyIncremental:
    """Controller exactly as implemented (Mega PE + MATLAB FIS + Uno accumulator)."""
    name = "fuzzy"

    def __init__(self, sp: int, pot0: float):
        self.sp, self.pot = sp, pot0

    def update(self, r: int) -> float:
        ce = ce_lookup(firmware_pe(r, self.sp))
        if abs(ce) > 15:
            ce = 0.0
        self.pot = min(100.0, max(0.0, self.pot + ce))
        return self.pot


class IntegralEquivalent:
    """Linear incremental (integral) law with the fuzzy small-signal gain and the same rate
    limit, dead band and quantisation: used to test whether the fuzzy shaping matters."""
    name = "integral"

    def __init__(self, sp: int, pot0: float, k: float, rate: float):
        self.sp, self.pot, self.k, self.rate = sp, pot0, k, rate

    def update(self, r: int) -> float:
        pe = firmware_pe(r, self.sp)
        ce = float(np.clip(-self.k * pe, -self.rate, self.rate))
        self.pot = min(100.0, max(0.0, self.pot + ce))
        return self.pot


class OnOffHysteresis:
    """Lamps either OFF or ON at a fixed commissioned level (the command that gives the setpoint
    in darkness).  Switch OFF when r >= SP*(1+h); switch ON when r <= SP*(1-h)."""
    name = "on/off"

    def __init__(self, sp: int, pot_on: float, h: float, on0: bool = True, min_dwell: int = 0):
        self.sp, self.pot_on, self.h, self.on = sp, pot_on, h, on0
        self.switches = 0
        self.min_dwell, self.dwell = min_dwell, min_dwell   # anti-short-cycling (cycles)

    @property
    def pot(self):
        return self.pot_on if self.on else 0.0

    def update(self, r: int) -> float:
        self.dwell += 1
        if self.dwell < self.min_dwell:
            return self.pot
        if self.on and r >= self.sp * (1 + self.h):
            self.on, self.switches, self.dwell = False, self.switches + 1, 0
        elif (not self.on) and r <= self.sp * (1 - self.h):
            self.on, self.switches, self.dwell = True, self.switches + 1, 0
        return self.pot


# ----------------------------------------------------------------------------- simulation
def simulate(plant: Plant, ctrl, E_ext: np.ndarray, pot0: float, rng=None, sigma_raw=0.0):
    """Closed loop. Reading r_k is taken from the light produced by the command of cycle k-1."""
    n = len(E_ext)
    plant.reset(pot0)
    pot = pot0
    out = {"r": np.zeros(n, int), "pot": np.zeros(n), "E": np.zeros(n), "E_led": np.zeros(n)}
    for k in range(n):
        E_led = plant.step(pot)
        E = E_led + E_ext[k]
        r = sensor_reading(E, rng, sigma_raw)
        out["r"][k], out["E"][k], out["E_led"][k] = r, E, E_led
        pot = ctrl.update(r)
        out["pot"][k] = pot
    return out
