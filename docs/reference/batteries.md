# Reference – Batteries

This page documents the ELN entry types populated automatically from log
files exported by the INL Battery Chamber sputtering/annealing systems
(**PC03 CathodeChamber**, **PC04 ElectrolyteChamber**).

---

## Overview

Each chamber periodically exports a CSV log with the following structure:

```
Line 1: meta-column names  (Recording Name, Date Started, User)
Line 2: meta-values        (All Signals, YYYY-M-D HH-MM-SS, OperatorName)
Line 3: empty
Line 4: data column headers (~460 columns)
Lines 5+: data rows sampled at ~1 Hz
```

Uploading such a CSV automatically creates one of the following entries:

| Entry type | Chamber | Populated when |
|---|---|---|
| `PC03CathodeChamberDeposition` | PC03 | Filename starts with `PC03` |
| `PC04ElectrolyteChamberDeposition` | PC04 | Filename starts with `PC04` **and** the log contains sputtering source columns |
| `PC04SubstrateAnnealing` | PC04 | Filename starts with `PC04` **and** the log contains only heater channels (no sputtering source columns) |

`PC04ChamberParser` inspects the column headers (looking for the
`PC Source 1 Active` marker) at parse time to decide which of the two PC04
entry types to create — no separate configuration is needed.

---

## Filename convention & automatic sample linking

Log filenames follow the convention:

```
PC0X_All Signals_[Sample Name] Date.csv
```

e.g. `PC04_All Signals_LNbO_004 2026.07.16-09.32.33.csv` → sample name
`LNbO_004`.

If the filename matches this convention, the extracted name is stored in the
entry's `sample_name` quantity and, during normalization, used to
automatically find-or-create the corresponding sample:

1. The current upload is searched for an existing `INLSubstrate`,
   `INLThinFilmStack`, or `INLSampleFragment` entry whose `name` matches
   `sample_name`. A bare `INLThinFilm` is **never** matched — sample linking
   always deals with complete samples (a stack or substrate), not individual
   thin-film layers.
2. **Match found:**
      - `INLThinFilmStack` → the newly deposited thin film (deposition
        entries only) is appended to it as an additional layer, written back
        to the stack's raw YAML file.
      - `INLSubstrate` → a new `INLThinFilmStack` is created referencing it,
        with the newly deposited thin film (if any) as its first layer.
      - `INLSampleFragment` → linked as-is (a layer cannot be appended to a
        fragment); a warning is logged.
3. **No match:** a brand-new `INLThinFilmStack` named after `sample_name` is
   created (with the deposited thin film as its first layer, if any).

If the filename doesn't follow the convention, `sample_name` stays unset, a
warning is logged, and parsing otherwise completes normally — no sample is
linked or created.

This behavior differs slightly between the deposition and annealing entries:

- **`PC03CathodeChamberDeposition` / `PC04ElectrolyteChamberDeposition`:** the
  resolved sample reference is appended to the `samples` list (skipped if a
  sample with that name is already present, so reprocessing doesn't create
  duplicates).
- **`PC04SubstrateAnnealing`:** the resolved sample is assigned to
  `thin_film_stack`, but only if that field (and `thin_film`) isn't already
  set manually, and only if the match is an actual `INLThinFilmStack` (a
  matched `INLSampleFragment` is left unset with a warning, since
  `thin_film_stack` cannot reference that type).

!!! note "Test / CLI parsing"
    Sample search relies on NOMAD's search index and is skipped when parsing
    outside of a live server (e.g. `nomad.client.parse()`, used in this
    plugin's test suite) — in that case a brand-new sample is always created.

---

## BatteryChamberSputteringDeposition (base)

**Base class:** `PlotSection`, `EntryData`

Shared base class for `PC03CathodeChamberDeposition` and
`PC04ElectrolyteChamberDeposition`. All quantities, subsections, and
normalization logic below are inherited by both.

### Metadata

| Quantity | Type | Description |
|----------|------|--------------|
| `recording_name` | `str` | Recording name from the CSV header |
| `operator` | `str` | Operator name from the CSV header |
| `start_datetime` | `Datetime` | Recording start time |
| `base_pressure` | `float` (Pa) | Minimum ion gauge pressure recorded (auto-computed) |
| `deposition_time` | `float` (s) | Total elapsed time with the substrate shutter open (auto-computed) |
| `substrate_type` | `str` | Substrate type identified by the system |
| `sample_name` | `str` | Sample name extracted from the filename — see [above](#filename-convention-automatic-sample-linking) |

### Sample references

| Sub-section | Type | Description |
|-------------|------|-------------|
| `substrate` | `INLSubstrateReference` | Single substrate reference (fallback) |
| `substrates` | `INLSubstrateReference` (repeats) | Individual substrate pieces loaded in the run; one `INLThinFilmStack` is created per entry |
| `samples` | `INLSampleReference` (repeats) | Samples linked automatically via `sample_name`, plus any additional manual references |

### Time-series & process data

All time-series quantities are NumPy arrays sampled at ~1 Hz and trimmed to
the periods where at least one source was active: `timestamps`,
`process_phase`, `process_time`, `substrate_shutter_open`,
`substrate_temperature[_2]`, `substrate_temperature_setpoint`,
`substrate_heater_current`, `substrate_rotation_speed`,
`substrate_bias_active/voltage/current/power`, `tc1_temperature` … `tc6_temperature`.

### Sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `chamber_environment` | `SputteringChamberEnvironment` | Gas flows (MFC 1–3) and pressure gauges (Capman, ion gauge, wide-range, roughing) |
| `sources` | `SputteringSource` (repeats, 1–4) | Per-source material, target, shutter, rate, thickness |
| `rf_power_supplies` | `SputteringRFPowerSupply` (repeats, PS1/PS3/PS5) | Forward/reflected power, DC bias, tuning |
| `dc_power_supply` | `SputteringDCPowerSupply` (PS4) | Pulsed DC current/voltage/power, arc/spark counts |
| `plot_config` | `PlotConfig` | Controls which figures are generated |

### Normalization

On normalization the entry:

1. Trims inactive time steps and re-zeros the time axis.
2. Recomputes `base_pressure` and `deposition_time`.
3. Builds Plotly figures according to `plot_config`.
4. Creates the deposited `INLThinFilm` entry (from active source materials)
   and, for each entry in `substrates`, a new `INLThinFilmStack`.
5. Resolves `sample_name` (if any) into `samples` — see
   [filename convention](#filename-convention-automatic-sample-linking).

### PC03CathodeChamberDeposition

**Inherits:** `BatteryChamberSputteringDeposition`
**Label:** `PC03 Cathode Chamber Deposition`

Populated automatically by uploading a CSV file whose filename starts with
`PC03`.

### PC04ElectrolyteChamberDeposition

**Inherits:** `BatteryChamberSputteringDeposition`
**Label:** `PC04 Electrolyte Chamber Deposition`

Populated automatically by uploading a PC04 CSV file that contains
sputtering source columns.

---

## PC04SubstrateAnnealing

**Base class:** `PlotSection`, `Annealing`
**Label:** `PC04 Substrate Annealing`

Populated automatically when a PC04 CSV log contains only heater channels
and no sputtering source columns. Inherits `duration`, `steps`, and `samples`
from `nomad_material_processing.general.Annealing`.

| Quantity | Type | Description |
|----------|------|--------------|
| `recording_name` | `str` | Recording name from the CSV header |
| `operator` | `str` | Operator name from the CSV header |
| `start_datetime` | `Datetime` | Recording start time |
| `substrate_type` | `str` | Substrate type identified by the system |
| `sample_name` | `str` | Sample name extracted from the filename — see [above](#filename-convention-automatic-sample-linking) |
| `peak_temperature` | `float` (K) | Maximum substrate heater temperature reached (auto-computed) |

| Sub-section | Type | Description |
|-------------|------|-------------|
| `thin_film` | `INLThinFilmReference` | Thin film that was annealed in this run (manual) |
| `thin_film_stack` | `INLThinFilmStackReference` | Stack that was annealed in this run (manual, or auto-linked via `sample_name`) |
| `plot_config` | `PlotConfig` | Controls which figures are generated (defaults to `Thermal Treatment` mode) |

Time-series quantities: `timestamps`, `process_phase`, `wide_range_pressure`,
`substrate_temperature[_2]`, `substrate_temperature_setpoint`,
`substrate_heater_current`, `tc1_temperature` … `tc6_temperature`.
