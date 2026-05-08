# Explanation

This page explains the key concepts and design decisions behind the
`nomad-inl-base` plugin.

---

## Entity / Activity model

NOMAD organizes scientific data around two complementary concepts:

- **Entities** are physical objects that persist over time and can be referenced
  by multiple activities.  Examples: a substrate, a thin film, a sputtering
  target.
- **Activities** are processes or measurements that consume or produce entities.
  Examples: a spin-coating run, a sputtering experiment, an XRD measurement.

All INL schemas follow this model. Entity entries (under the *INL Entities*
category) are created once and referenced throughout the experiment lifecycle.
Activity entries record what was done and point to the involved entities.

---

## The thin-film chain

A complete thin-film sample in NOMAD is represented by a chain of three linked
entries:

```
INLSubstrate  ──► INLThinFilmStack ◄──  INLThinFilm  (one per layer)
```

`INLThinFilmStack` holds:

- A **substrate** reference (via `INLSubstrateReference`)
- One or more **layer** references (via `INLThinFilmReference`)
- A `components` list built automatically during normalization containing
  `SystemComponent` objects pointing to the actual entries

Normalization also propagates substrate geometry (width, length) to every
layer, keeping the stack self-consistent.

All deposition methods and characterization schemas reference the
`INLThinFilmStack` as the sample object, ensuring full provenance traceability
from raw substrate to final measurement.

### Why separate entries?

Storing each object as its own NOMAD entry means:

- The same substrate can be referenced by many depositions without duplication
- Measurements can be linked directly to the specific stack measured
- NOMAD's graph and search features can traverse the full chain

---

## Auto-creation of film/stack entries

When **Creates new thin film** is set to `True` on a deposition entry,
normalization:

1. Creates an `INLThinFilm` YAML entry in the upload
2. Creates an `INLThinFilmStack` YAML entry linking the film and substrate
3. Sets the deposition entry's `thin_film_stack` reference to the new stack
4. Resets the toggle to `False` so the action is not repeated

If a stack reference already exists, the step is skipped, so re-normalizing
a saved entry is safe.

---

## Recipe system

Both deposition families (wet deposition and STAR sputtering) support
**reusable recipe entries**.

### WetDepositionRecipe

A `WetDepositionRecipe` entry stores template values for instrument,
atmosphere, substrate, solutions, annealing, and quenching. When
**Apply recipe** is triggered on a deposition entry, each template field
is copied into the deposition *only if that field is currently empty*.
This non-destructive merge means a recipe can be partially overridden per
experiment without modifying the recipe itself.

### StarSputteringRecipe

A `StarSputteringRecipe` stores a sequence of `StarStep` objects (pre-sputtering,
stabilization, sputtering). When applied, the recipe's steps are appended to
the experiment's step list.

---

## Target inventory and calibration tracking

The `SputteringTarget` entry acts as a persistent logbook for a physical
magnetron target. Each time a `StarSputtering` experiment that references
the target is normalized, the target's deposition records list gains a new
`TargetDepositionRecord` entry with:

- The experiment reference
- The source slot index
- The total deposition time (sum of all powered steps)
- The total deposition energy (sum of power × duration for all steps)

The target's normalization then recomputes:

| Quantity | Description |
|----------|-------------|
| `total_deposition_time` | Sum across all records |
| `total_deposition_energy` | Sum across all records |
| `time_since_last_calibration` | Sum since `last_calibration_date` |
| `energy_since_last_calibration` | Sum since `last_calibration_date` |
| `needs_calibration` | `True` if either interval threshold is exceeded |

This automates target lifecycle management without requiring manual bookkeeping.

---

## Electrochemistry schemas

Three electrochemical measurement schemas are supported, all parsed from
Bio-Logic EC-Lab `.mpr` binary files:

- **`PotentiostatMeasurement`** – used for both Cyclic Voltammetry (CV) and
  linear-sweep IV experiments. When a `scan` sub-section is present the entry
  is treated as CV and the CV curve for the highest available scan number is
  plotted. When no `scan` sub-section is present (IV/LSV mode) all data points
  are plotted as a single sweep.
- **`ChronoamperometryMeasurement`** – constant-potential experiment; plots
  current (density) vs. time.
- **`EISMeasurement`** – Potentio- or Galvano-EIS; stores the full impedance
  spectrum and auto-generates a Nyquist plot and a two-panel Bode plot.

All three schemas optionally accept an **area electrode** value (in m²).
When provided, displayed y-axis quantities switch from raw current (mA) to
current density (mA cm⁻²), enabling direct comparison across electrode sizes.

A single **MPR parser** handles all three experiment types. Technique is
auto-detected from the column names present in the `.mpr` data block
(`freq/Hz` → EIS; `cycle number` → CV; otherwise IV). Instrument metadata
(electrode area, material, electrolyte, reference electrode, scan rate) is
extracted via **yadg** where possible, with an automatic fallback to reading
the binary `VMP Set` module for techniques yadg does not yet support (EIS).

The working electrode (`WorkingElectrode`) extends `INLThinFilmStack` so the
exact sample geometry (substrate, layer stack) used in the measurement is
always recorded.

---

## STAR reactive sputtering and selenization (SpuTtering for Advanced Research)

The STAR sputtering schema was extended with two process types that involve a
selenium effusion cell alongside (or instead of) standard sputtering targets.

### STARDCReactiveSputtering

Inherits all `StarDCSputtering` behavior (sources, target records, recipe
application, thin film creation). Each `STARReactiveDCStep` carries a
sibling `INLSeleniumPulseParameters` sub-section that describes the pulsed
Se environment active during that step. Multiple steps can have different
pulse parameters, or only a subset of steps may activate selenium.

The `INLSeleniumPulseParameters` section auto-computes two derived quantities
on normalization:

- **Cracker power** = `cracker_current × cracker_voltage`
- **Total Se on time** = `round(process_time / (time_on + time_off)) × time_on`

This means the user only needs to set the four raw measurements; the derived
values are always consistent.

### STARSelenizationAnnealing

Uses the same STAR chamber infrastructure (pressure control, substrate
heating, rotation) as sputtering experiments, but without any active targets.
The `sources` sub-section is hidden from the ELN. Each `STARSeAnnealingStep`
still exposes the full Se pulse parameter block and the substrate
temperature/rotation fields.

### SeleniumCell entity

`SeleniumCell` is a persistent entity entry that acts as a logbook for a
physical selenium effusion cell. Weight records (`SeleniumCellWeightRecord`)
accumulate over the life of the cell, and a `refill_date` marks when the
cell was last replenished. This enables tracking of selenium consumption
and cell lifetime without modifying individual experiment entries.

---

## METEOR e-beam evaporation (Metal EvaporaTion by Electron-beam for SOlar Research)

### Schema design

`METEORDeposition` inherits from both `Process` and `EntryData`. Rather than
per-step modelling (as in the STAR sputtering schemas), METEOR uses a single
process entry that holds the complete time series for the entire run. This
matches how the Korvus `.nbl` log format works: one file = one run with
continuous data from all channels.

Four `METEORPocket` sub-sections represent the four e-beam evaporation pockets.
Each pocket carries its own time-series arrays (filament current, set/measured
power, flux, enabled state). Setting the `material` field on a pocket enables
PubChem lookup and links the deposited material to the NOMAD substance database.

A `METEORQCMMonitor` sub-section stores QCM data. The parsed `thickness` is
filled automatically from the last row of the log; a `thickness_override` field
lets the user supply a value from an independent measurement. During thin film
creation the override takes precedence when set.

### .nbl log format

The Korvus `.nbl` log file has an unusual single-line preamble that fuses:

```
<machine name> <datetime> <all column headers concatenated without separator>
```

The `_parse_nbl_columns()` function extracts the datetime with a regex, then
locates the `Time,` token to identify where column headers begin. Duplicate
`Power N(W)` columns (Korvus logs both set and measured power under the same
header name) are renamed: the second set becomes `Measured Power N(W)`.
Rows have a trailing comma; a dummy `_trailing` column absorbs it.

### Thin film creation

`METEORDeposition.normalize()` follows the same pattern as wet deposition:
when `creates_new_thin_film` is `True` it creates `INLThinFilm` and
`INLThinFilmStack` entries, then resets the toggle. The film thickness is
taken from `qcm.thickness_override` if set, otherwise from `qcm.thickness`.
The material comes from the first `METEORPocket` whose `material` field is
populated.

---

## Shared entities vs. method-specific aliases

The `INLThinFilm`, `INLThinFilmStack`, and related reference classes live in
`entities.py` and are shared across all schema modules. The STAR sputtering
schema re-exports them as `StarThinFilm`, `StarStack`, etc. for backwards
compatibility with existing NOMAD archives; these names are simple aliases
and refer to exactly the same classes.
