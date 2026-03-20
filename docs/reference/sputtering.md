# Reference – STAR Sputtering

This page documents all ELN entry types in the **STAR** category, which covers
magnetron sputtering experiments performed on the STAR deposition system at INL.

---

## SputteringTarget

**Category:** STAR  
**Base class:** `CompositeSystem`, `EntryData`

A persistent record of a physical sputtering target. Each `SputteringTarget`
entry acts as a logbook: it accumulates usage time and energy across all
experiments that reference it, and can alert when recalibration is needed.

### Quantities

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `name` | `str` | – | Human-readable target name (inherited) |
| `lab_id` | `str` | – | Unique lab identifier (inherited) |
| `supplier` | `str` | – | Manufacturer or supplier of the target |
| `delivery_date` | `Datetime` | – | Date the target was received |
| `installation_date` | `Datetime` | – | Date the target was installed in the chamber |
| `last_calibration_date` | `Datetime` | – | Date of the most recent calibration |
| `calibration_interval_time` | `float` | hours | Usage time threshold that triggers recalibration |
| `calibration_interval_energy` | `float` | kWh | Energy threshold that triggers recalibration |
| `total_deposition_time` | `float` | hours | Accumulated time across all deposition records *(auto)* |
| `total_deposition_energy` | `float` | kWh | Accumulated energy across all deposition records *(auto)* |
| `time_since_last_calibration` | `float` | hours | Time accumulated since `last_calibration_date` *(auto)* |
| `energy_since_last_calibration` | `float` | kWh | Energy accumulated since `last_calibration_date` *(auto)* |
| `needs_calibration` | `bool` | – | `True` if any threshold is exceeded *(auto)* |

### Sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `target_id` | `ReadableIdentifiers` | Structured INL/LaNaSC identifier |
| `geometry` | `Geometry` | Physical dimensions of the target |
| `components` | `PureSubstanceComponent` (repeats) | Chemical composition |
| `calibration_data` | `StarCalibrationDataReference` | Current calibration entry |
| `old_calibration_data` | `StarCalibrationDataReference` (repeats) | Historical calibrations |
| `deposition_records` | `TargetDepositionRecord` (repeats) | Usage log *(auto-appended)* |

### Normalization behavior

- Sets `target_raw_path` to the upload file path (used for cross-entry record writing)
- Recomputes `total_deposition_time`, `total_deposition_energy`,
  `time_since_last_calibration`, `energy_since_last_calibration`
- Sets `needs_calibration = True` if either threshold is exceeded

---

## TargetDepositionRecord

**Base class:** `ArchiveSection`

A single entry in a target's usage log. Records are written automatically by
`StarSputtering.normalize()`.

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `experiment` | `SputterDeposition` | – | Reference to the sputtering experiment |
| `source_index` | `int` | – | Index of the source slot used |
| `deposition_time` | `float` | hours | Total powered time in this experiment |
| `deposition_energy` | `float` | kWh | Total energy delivered in this experiment |

---

## StarCalibrationData

**Category:** STAR  
**Base class:** `EntryData`

Stores the measured deposition rate from a calibration run.

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `calibration_date` | `Datetime` | – | Date of the calibration |
| `deposition_rate` | `float` | nm/min | Measured rate |
| `calibration_experiment` | `SputterDeposition` | – | Reference to the calibration run |

---

## StarSputteringRecipe

**Category:** STAR  
**Base class:** `EntryData`

A reusable template of `StarStep` objects. Apply by setting the **Recipe**
reference on a sputtering experiment and ticking **Apply recipe**.

| Quantity | Type | Description |
|----------|------|-------------|
| `name` | `str` | Recipe name |
| `description` | `str` | Rich-text description |

**Sub-sections:**

| Sub-section | Type | Description |
|-------------|------|-------------|
| `steps` | `StarStep` (repeats) | Ordered sequence of deposition steps |

---

## StarRFSputtering / StarDCSputtering

**Category:** STAR  
**Base class:** `SputterDeposition`, `EntryData`

These are the two concrete entry types for sputtering experiments. They
inherit all fields from `StarSputtering` and differ only in the step types
they use.

| Method | Step types available |
|--------|---------------------|
| `StarRFSputtering` | `PresputteringRFStep`, `StabilizationRFStep`, `SputteringRFStep` |
| `StarDCSputtering` | `PresputteringDCStep`, `StabilizationDCStep`, `SputteringDCStep`, `PostSputteringDCStep` |

### Quantities (from StarSputtering)

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `name` | `str` | – | Experiment name |
| `operator` | `str` | – | Person who ran the experiment |
| `base_pressure` | `float` | mbar | Chamber base pressure before deposition |
| `is_a_calibration_experiment` | `bool` | – | Mark as calibration run |
| `apply_recipe` | `bool` | – | Trigger recipe application on normalize |

### Sub-sections (from StarSputtering)

| Sub-section | Type | Description |
|-------------|------|-------------|
| `sources` | `SputteringSource` (repeats) | Magnetron guns; each references a `SputteringTarget` |
| `steps` | `StarStep` (repeats) | Deposition step sequence |
| `samples` | `StarStackReference` (repeats) | Thin-film stacks produced |
| `recipe` | `StarSputteringRecipeReference` | Recipe to apply |

### Normalization behavior

For each `SputteringSource` that references a `SputteringTarget`:

1. Computes the total powered time and energy for the source across all steps
2. Writes a `TargetDepositionRecord` to the target entry
3. Triggers re-normalization of the target so its totals are updated

---

## Step types

All step types inherit from `StarStep` which in turn extends `VaporDepositionStep`.

| Class | RF/DC | Description |
|-------|-------|-------------|
| `PresputteringRFStep` | RF | Pre-sputtering cleaning step with shutter closed |
| `StabilizationRFStep` | RF | Plasma stabilization before opening shutter |
| `SputteringRFStep` | RF | Main deposition step |
| `PresputteringDCStep` | DC | Pre-sputtering cleaning |
| `StabilizationDCStep` | DC | Plasma stabilization |
| `SputteringDCStep` | DC | Main deposition step |
| `PostSputteringDCStep` | DC | Post-sputtering cool-down |

Common step quantities:

| Quantity | Unit | Description |
|----------|------|-------------|
| `duration` | s | Step duration |
| `creates_new_thin_film` | – | Toggle to auto-create film/stack entries |
| `set_power` / `power` | W | Set-point and measured power |
| `set_voltage` / `voltage` | V | DC voltage (DC steps only) |
| `set_current` / `current` | A | DC current (DC steps only) |
| `Ct_value` / `Cl_value` | – | RF tuning capacitor values (RF steps only) |
| `chamber_pressure` | mbar | Measured chamber pressure during step |
