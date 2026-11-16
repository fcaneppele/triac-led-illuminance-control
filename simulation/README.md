# Calibrated simulation: fuzzy vs on/off and integral baselines

**All results in this folder are simulated.** The plant model is identified from the
single-run bench records; Monte Carlo statistics are not physical repetitions.

## Files

| File | Role |
|---|---|
| `model.py` | Sensor → Mega firmware → MATLAB FIS → Uno accumulator → plant chain; fuzzy (as implemented), integral-equivalent, on/off and on/off with minimum dwell controllers |
| `identify.py` | Static map g(POT), first-order lag, run-to-run gain spread and sensor temporal noise; closed-loop validation against the ten bench runs |
| `compare.py` | Scenarios, metrics and paired differences with bootstrap 95 % confidence intervals |
| `data/` | Digitised traces (keys = dissertation plot numbers) and bench records |
| `out/` | `plant_params.json`, `identification_report.md`, `summary.csv`, `paired_differences.csv`, `mc_runs.csv`, `examples.json`, diagnostic figure |

## Model (one step = one 3 s cycle)

* The firmware and script are reproduced exactly: integer corrected reading, integer PE with
  saturation and dead band, the FIS with the executed parameters, the Uno accumulator and the
  firing thresholds.
* Plant: LED illuminance at the sensor = g(POT) × run gain, with a first-order lag; external
  light adds at the sensor; the reading at cycle k reflects the command of cycle k−1.
* g(POT) is a monotone piecewise-linear map fitted to 53 points: the reconstructed A1 runs plus
  the dark steady states of the A2 runs, whose command was obtained from the measured LED
  voltage via the measured voltage–angle curve.
* The knot set, smoothing and lag were selected by pooled closed-loop validation RMSE with
  nominal gain. The result is 1.59 sensor counts (see `out/identification_report.md`).

## Comparison protocol

* **Controllers:**
  - fuzzy, as implemented;
  - integral-equivalent: CE = −K·PE with the fuzzy small-signal gain, the same saturation,
    dead band and quantisation;
  - on/off with ±20 % hysteresis at the level commissioned in darkness;
  - the same on/off with a 1 min minimum dwell.
* **Scenarios:**
  - steps equal to the sensor jumps observed on the bench;
  - a **synthetic** 30 min daylight ramp (0 → 1.5·SP);
  - the same ramp with **synthetic** two-state cloud modulation.
* **Monte Carlo:** N = 200 runs per condition, paired across controllers (same random draws).
  Sensor noise is set at the nominal level (upper 95 % bound from steady segments) and at a
  stress level of 0.60 raw counts.
* **Metrics:** computed only where external light alone is below 0.95·SP. They are time within
  ±20 % of SP, mean and maximum absolute deviation, lamp switching events, mean artificial
  light relative to dark operation (a dimensionless proxy, **not** energy) and recovery time.

## Assumptions and known discrepancies

* The synthetic daylight profiles are illustrative, not measured.
* The driver hysteresis of the LED lamps is not modelled.
* At 10 lx the model shows ±1-count transient oscillations not seen on the bench, so the
  simulated fuzzy performance there is pessimistic.
* The model follows the firmware dead band. It therefore does not reproduce the steady readings
  of A2-5 and A2-6, which are inconsistent with that dead band.
* External-light step sizes in the A2 validation are taken from the observed reading jumps, so
  that part of the validation partly depends on the same data.
