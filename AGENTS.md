# Thin-Film Fitting Project Notes

## Purpose

This project fits thin-film thickness from COMSOL or experimental reflectance spectra using a physics-based optical model.

The current main route is:

1. Export reflectance spectra from COMSOL.
2. Use two incident angles, preferably `10 deg + 80 deg`.
3. Use a fixed polarization, currently `s` is the most stable validated route.
4. Fit film thickness `d` and optionally correct the second angle `theta2`.

This is a physical inverse-model workflow, not a neural-network workflow.

## Main File

Use:

```text
thinfilm_core.py
```

The older scripts are mostly exploratory:

```text
comsol_only_analysis.py
theta_scan_fit_from_comsol.py
Untitled-1.py
```

## Current Stable Engineering Route

Recommended configuration:

```python
THETA1 = 10.0
THETA2 = 80.0
POL = "s"
RUN_MODE = "fit_csv_with_theta2_search"
```

Inputs should be reflectance CSV files:

```python
CSV_FILE_ANGLE1 = Path(r"...10deg_s.csv")
CSV_FILE_ANGLE2 = Path(r"...80deg_s.csv")
```

The current stable validation result for the `60 nm` sample using `10 deg + 80 deg`, `s` polarization was approximately:

```text
d_fit_corrected ~= 59.97 nm
theta2_fit      ~= 80.04 deg
best_objective  ~= 3.02e-02
```

## Important COMSOL Export Guidance

For the stable main route, export pure-polarization reflectance spectra:

```text
10deg_s.csv
80deg_s.csv
```

Optional comparison or future mixed-polarization work may also export:

```text
10deg_p.csv
80deg_p.csv
```

Do not rely on COMSOL direct `mixed` / `avg(0.6p)` export as the fitting target unless it has been independently verified.

Observed issue:

```text
COMSOL mixed output was not equal to eta * R_p + (1 - eta) * R_s.
```

For mixed polarization, the safer engineering route is:

```text
Export pure s and pure p endpoints, then blend in Python.
```

The implemented blend model is:

```text
R_mix = eta * R_p + (1 - eta) * R_s
```

with `eta` constrained to `[0, 1]`.

## Main Run Modes

Set `RUN_MODE` near the top of `thinfilm_core.py`.

Useful modes:

```text
fit_csv_with_theta2_search
fit_csv_compare_pols
single_sample_error_analysis
batch_error_analysis
single_angle_0deg_scan
objective_heatmap_d_theta2
```

Main production mode:

```text
fit_csv_with_theta2_search
```

Polarization comparison:

```text
fit_csv_compare_pols
```

This compares:

```text
s
p
avg
mix
```

## Key Configuration

Two-angle inputs:

```python
CSV_FILE_ANGLE1 = Path(...)
CSV_FILE_ANGLE2 = Path(...)
THETA1 = 10.0
THETA2 = 80.0
```

Polarization:

```python
POL = "s"      # recommended main route
POL = "p"
POL = "avg"    # fixed 50/50 average
POL = "mix"    # eta * p + (1 - eta) * s
```

Mixed-polarization endpoint blending:

```python
MIX_USE_ENDPOINT_TARGET_BLEND = True
MIX_SOURCE_P_WEIGHT = 0.6
MIX_SOURCE_ANGLE1_MODE = "blend"
MIX_SOURCE_ANGLE2_MODE = "blend"
```

Endpoint files:

```python
MIX_SOURCE_CSV_ANGLE1_S = Path(...)
MIX_SOURCE_CSV_ANGLE1_P = Path(...)
MIX_SOURCE_CSV_ANGLE2_S = Path(...)
MIX_SOURCE_CSV_ANGLE2_P = Path(...)
```

## Dispersion Model

The code supports an optional Cauchy dispersion model:

```text
n(lambda) = A + B / lambda_um^2 + C / lambda_um^4
```

Switch:

```python
USE_DISPERSION = True
```

Parameters:

```python
N1 = 1.38
N1_DISPERSION_B = ...
N1_DISPERSION_C = ...

N2 = 1.52
N2_DISPERSION_B = ...
N2_DISPERSION_C = ...
```

COMSOL expression should use a dimensionless wavelength in micrometers:

```text
lambda_um = lambda0/1[um]
n1 = n1_A + n1_B/(lambda_um^2) + n1_C/(lambda_um^4)
```

Do not use raw `lambda0` without units.

Current finding:

```text
The test value n1_B = 0.005 worsened the 60 nm, 10 deg + 80 deg, s-polarized fit.
```

This does not mean dispersion is invalid. It only means that this parameter choice was not a better match for the current data.

## Output Location

Outputs are saved to:

```text
C:\Users\L2791\thinfilm_outputs
```

Typical outputs:

```text
fit_csv_with_theta2_search_summary.txt
fit_csv_with_theta2_search_summary.json
fit_csv_with_theta2_search_result.csv
fit plots
residual plots
```

## APP / Server Integration Notes

The fitting backend can be wrapped by an APP.

Recommended API-style inputs:

```text
csv_angle1
csv_angle2
theta1
theta2
pol
n0
n1
n2
use_dispersion
n1_dispersion_b
n1_dispersion_c
n2_dispersion_b
n2_dispersion_c
```

Recommended outputs:

```text
d_fit_corrected_nm
theta2_fit_deg
best_objective
fit curves
residual curves
input metadata
```

Server needs:

```text
CPU: 4-8 cores for prototype
RAM: 8-16 GB recommended
GPU: not required
```

The workload is CPU-based numerical physics fitting, not neural-network inference.

## Current Known Limitations

1. The model is currently a single-layer thin-film model.
2. Surface roughness, transition layers, and multilayer structures are not yet included.
3. Direct COMSOL mixed-polarization export was not reliable in previous tests.
4. Dispersion support exists, but valid material parameters still need to be identified.
5. Some old function names still contain `0deg`; the newer configuration aliases use `ANGLE1` and `ANGLE2`.

## Recommended Next Steps

1. Keep the main route fixed as `10 deg + 80 deg`, `s` polarization.
2. Validate more thicknesses with the same route.
3. Scan small ranges of `n1_A` and `n1_B` only after the constant-index baseline is stable.
4. Keep mixed-polarization work as a diagnostic branch, not the production main route.
5. If APP work starts now, keep the UI parameter-driven and avoid hard-coding `60 nm`, `0 deg`, or a single polarization.
