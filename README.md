# Triac-dimmed LED illuminance control with external-light compensation: bench data, firmware and calibrated simulation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24294283.svg)](https://doi.org/10.5281/zenodo.24294283)

Data, original source code and simulation supporting the article *"Closed-loop illuminance
control of triac-dimmed retrofit LED lamps with external-light compensation: a low-cost bench
study at low illuminance"* (submitted). The bench prototype was developed in the M.Sc.
dissertation of J. A. Carvalho Neto (FCA/Unesp, Botucatu, Brazil, 2021).

**System in one line:** BH1750 light sensor (GY-302) → Arduino Mega (acquisition, calibration,
error, dead band) → MATLAB on a host PC (3-rule Mamdani fuzzy inference) → Arduino Uno + dimmer
shield (BTA08-600B triac, phase-angle control) → two 9.5 W retrofit LED lamps, with a 3 s
control cycle, setpoints of 10 lx and 33 lx at the sensor, and a halogen lamp emulating external
light.

## Contents

| Folder | What it holds |
|---|---|
| `firmware/` | Original Arduino (Mega, Uno) and MATLAB code, transcribed verbatim from the dissertation appendices |
| `data/` | Sensor calibration pairs (n = 26 and n = 22), triac/dimmer voltage tables, bench-run summaries, digitised response traces and the original plots they were read from |
| `tools/` | Scripts to recompute the calibration statistics and to re-digitise the response plots |
| `simulation/` | Plant identification from the bench records, closed-loop validation, and the Monte Carlo comparison of the fuzzy controller with on/off (hysteresis) and integral baselines |

## Reproduce

```bash
pip install -r requirements.txt
python tools/verify_calibration.py          # calibration statistics
python tools/digitize_response_plots.py     # re-digitises data/source_plots -> tools/digitized_traces_check.json
cd simulation
python identify.py                          # plant identification + validation -> out/plant_params.json
python compare.py                           # Monte Carlo (N = 200 per condition, ~2 min) -> out/summary.csv
python onoff_sensitivity.py                 # on/off hysteresis sensitivity -> out/onoff_hysteresis_sensitivity.csv
python loro.py                              # leave-one-run-out check -> out/loro.json
```

Seeds are deterministic, so the outputs in `simulation/out/` are reproduced exactly.

## Read this before using the data

* **Single runs.** Every dynamic bench test (setpoint tracking A1-1 to A1-4; external-light steps
  A2-1 to A2-6) was run once (n = 1). Statistics in `simulation/out/` come from Monte Carlo runs
  of an identified model, **not** from repeated physical tests.
* **Simulated baselines.** No baseline controller was tested on hardware. The on/off and
  integral comparisons are simulations calibrated on the single-run bench records. The model
  reproduces the ten runs with a pooled closed-loop RMSE of 1.59 sensor counts; see
  `simulation/README.md` for the assumptions and known discrepancies.
* **Digitised traces.** Per-cycle lux, PE and CE values were read from the original MATLAB plots
  by pixel detection. They are not logged numbers. Resolution is stated in `data/README.md`.
* **No energy data.** Only the RMS voltage across the lamps was measured. Nothing here supports
  power or energy claims.
* **Host-based inference.** The fuzzy inference ran in MATLAB on a PC, not in embedded firmware.

## How to cite

Cite the archived release used in the article (see the version DOI on the Zenodo record of the latest release). Version 1.0.0:
[10.5281/zenodo.24294284](https://doi.org/10.5281/zenodo.24294284). All versions:
[10.5281/zenodo.24294283](https://doi.org/10.5281/zenodo.24294283). Please also cite the dissertation:

> J. A. Carvalho Neto, *Sistema de iluminação de granjas controladas por lógica fuzzy* (Lighting
> system for poultry houses controlled by fuzzy logic), M.Sc. dissertation, School of
> Agricultural Sciences, São Paulo State University (Unesp), Botucatu, Brazil, 2021.

## Licences

* Code (`firmware/`, `tools/`, `simulation/*.py`): MIT, see `LICENSE`.
* Data (`data/`, `simulation/data/`, `simulation/out/`): CC BY 4.0, see `LICENSE-DATA.md`.

## Use of AI tools

Generative AI tools assisted with numerical work (statistical reanalysis of the calibration,
pixel digitisation of the original plots and the simulation code) and with English-language
revision. The authors checked the results and take responsibility for them.
