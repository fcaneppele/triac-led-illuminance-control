# Original source code

Transcribed verbatim from the dissertation appendices, without modification. Identifiers and
comments are in Portuguese. The code has not been re-tested on hardware for this release.

| File | Appendix | Runs on | Role |
|---|---|---|---|
| `mega_acquisition_scheduler/mega_acquisition_scheduler.ino` | A | Arduino Mega2560 | Reads the BH1750 (I²C, address 0x23, continuous high-resolution mode); applies `lux2 = int(0.7777*lux - 0.4562)`; computes `PE = (lux2*100/Set_point) - 100`, clipped to ±100; dead band (PE := 0 if \|PE\| ≤ 5 for setpoint 33, ≤ 9 for setpoint 10); photoperiod scheduler; answers MATLAB on serial (`'A'` → PE, `'B'` → corrected reading) |
| `uno_dimmer/uno_dimmer.ino` | B | Arduino Uno + dimmer shield | Receives CE; discards \|CE\| > 15; accumulator `POT = clip(POT + CE, 0, 100)`; firing delay `83.33*(100 - POT)` µs after the zero-crossing interrupt (gate held high if ≤ 820 µs, no firing if ≥ 8000 µs) |
| `matlab/fuzzy_loop.m` | C | MATLAB R2015a, host PC | Serial links (Uno on COM4, Mega on COM3, 9600 baud); Mamdani min–max inference, centroid; membership functions PE: EN `[-100 -100 -50 0]`, STP `[-50 0 50]`, EP `[0 50 100 100]`; CE: CN `[-15 -15 -9 0]`, CM `[-9 0 9]`, CP `[0 9 15 15]`; rules EN→CP, STP→CM, EP→CN; `pause(3)` per cycle |

## Notes and discrepancies with the dissertation text

* The design plot of the output membership functions (Fuzzy Logic Designer) shows the CP
  shoulder at about 9.8. The executed script uses 9. The logged CE saturation agrees better
  with 9.
* The text says a 40-sample moving average was adopted. The Mega code uses `#define N 10`,
  and the filtered value is not used in the PE computation.
* The setpoint "25 lux" of the lighting programme is implemented as `Set_point = 33`, the
  sensor value that corresponds to 25 lx at bird height. Darkness is `Set_point = 1`, which
  forces PE = 100.
* The zero-crossing detector circuit of the commercial dimmer shield is not documented.
