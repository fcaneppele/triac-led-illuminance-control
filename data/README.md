# Data dictionary

All values come from the M.Sc. dissertation (Carvalho Neto, 2021); page numbers below refer to
its printed pagination. Decimal separator: point.

## Calibration (GY-302 / BH1750 vs. Instrubras ITR-3000 lux meter)

Setup: LED lamp in a luminaire 1.70 m from the sensor. The lamp was dimmed in 2 % steps of the
triac firing time, and the tests were done at night (pp. 62–64).

| File | Rows | Columns |
|---|---:|---|
| `calibration_raw_n26.csv` | 26 | raw sensor reading without / with moving average (identical), reference lux meter (Table 5, p. 84) |
| `calibration_corrected_n22.csv` | 22 | reading after the correction `0.7777*raw - 0.4562` without / with moving average (identical), reference lux meter (Table 6, p. 86) |

`tools/verify_calibration.py` returns:
* raw fit: slope 0.7777, intercept −0.4562, R² 0.9985, RMSE 0.517 lx, MAE 0.402 lx;
* corrected fit: slope 1.0123, intercept 0.2846, R² 0.9989, RMSE 0.470 lx, MAE 0.360 lx. These
  are regression residuals;
* direct agreement (corrected − reference): mean −0.52 lx, SD 0.51 lx, RMSE 0.72 lx.

## Actuator

| File | Content |
|---|---|
| `dimmer_two_leds_210V.csv` | Firing angle vs RMS voltage across the two LED lamps, 210 V mains: resistive-load formula vs multimeter (Table 11, p. 95) |
| `dimmer_two_leds_123V.csv` | Same at 123.49 V mains (Table 10, p. 95) |
| `triac_proteus_simulation_Vp175.csv` | Proteus simulation with a resistive load, Vp = 175 V (Table 9, p. 94) |

The `error_pct_as_reported` column is copied from the source. The multimeter (Thompson 880) is
not specified as true-RMS.

## Bench runs (single runs, n = 1)

| File | Content |
|---|---|
| `bench_A1_setpoint_tracking.csv` | Four setpoint-tracking runs without external light (pp. 96–100) |
| `bench_A2_external_light.csv` | Six external-light step runs: LED voltage, sensor readings and lux-meter readings at each event, as reported in the text (pp. 100–105) |

Sensor at 0.30 m above the floor; LED lamps at 2.5 m. The lux meter sat at 0.30 m for the 10 lx
setpoint and at 0.05 m for the 33 lx setpoint, which corresponds to 25 lx at bird height,
mapping obtained with the LEDs only. The position of the lux meter when measuring the external
light levels is not documented.

## Digitised response traces

`digitized/<run>.csv` holds one row per plotted sample (one sample = one 3 s cycle). The columns
are the sensor reading (lx), PE (%) and CE (%), read from `source_plots/<run>.png`. Rows where
any value lies on a vertex or a steep segment have `low_confidence_vertex = 1`.

| Run | Dissertation plot | Condition | Approx. resolution (1 px): reading / PE / CE |
|---|---|---|---|
| A1-1 | Graph 19 (p. 97) | lamps off → 10 lx | 0.06 lx / 0.6 % / 0.06 % |
| A1-2 | Graph 20 (p. 97) | lamps off → 33 lx | 0.24 lx / 0.6 % / 0.06 % |
| A1-3 | Graph 22 (p. 98) | full → 10 lx | 0.60 lx / 0.6 % / 0.06 % |
| A1-4 | Graph 24 (p. 99) | full → 33 lx | 0.24 lx / 0.6 % / 0.06 % |
| A2-1 | Graph 26 (p. 101) | 10 lx, external 1.67 lx | 0.02 lx / 0.24 % / 0.06 % |
| A2-2 | Graph 27 (p. 102) | 10 lx, external 5.31 lx | 0.12 lx / 1.2 % / 0.12 % |
| A2-3 | Graph 28 (p. 103) | 10 lx, external 10.43 lx | 0.24 lx / 1.2 % / 0.12 % |
| A2-4 | Graph 29 (p. 104) | 33 lx, external 1.22 lx | 0.006 lx / 0.01 % / 0.01 % |
| A2-5 | Graph 30 (p. 105) | 33 lx, external 5.53 lx | 0.06 lx / 0.24 % / 0.06 % |
| A2-6 | Graph 31 (p. 106) | 33 lx, external 10.33 lx | 0.24 lx / 0.6 % / 0.12 % |

The sensor readings used by the controller are integers; round the digitised readings when
plotting.

Known issues in the original records, reported rather than corrected:
* The plotted sample index can be one or two cycles later than the cycle numbers in the text.
* PE/CE were requested at a different instant of the cycle from the lux value, so they do not
  always match the reading of the same sample.
* In A2-5 and A2-6, steady readings of about 36, 32 and 30 lx with PE = 0 are inconsistent
  with the ±5 % dead band in the firmware.
* In A2-3, the reading stayed at 11–12 lx with the lamps already off: the actuator was
  saturated.
