# How to Use This Plugin

This page covers common tasks you will perform with the `nomad-inl-base` ELN
schemas. See the [Tutorial](../tutorial/tutorial.md) for a guided walkthrough
of a first experiment.

---

## Managing shared entities

### Creating a substrate

1. Create a new entry → **INL Substrate**.
2. Set **Name** (e.g. `SLG-A01`) and **Material** (defaults to `SLG`).
3. Leave **Geometry** empty – a 25 × 25 × 1 mm `RectangleCuboid` is filled in
   automatically during normalization.
4. Set **Lab ID** so the substrate can be found by ID in reference fields.

### Creating a thin film and stack manually

If you want to create film/stack entries yourself rather than using the
auto-creation toggle:

1. Create a new entry → **INL Thin Film**. Set **Material** and **Thickness**.
2. Create a new entry → **INL Thin Film Stack**.
   - Add a **Substrate** sub-section pointing to your substrate.
   - Add one or more **Layers** sub-sections pointing to thin-film entries.
3. Normalization propagates the substrate dimensions to each film's geometry.

---

## Wet deposition

### Recording a deposition

All wet deposition entries (`INLSpinCoating`, `INLSlotDieCoating`,
`INLBladeCoating`, `INLInkjetPrinting`, `INLSprayPyrolysis`, `INLDipCoating`,
`INLChemicalBathDeposition`) share the same base fields:

| Field | Purpose |
|-------|---------|
| **Operator** | Person who ran the process |
| **Substrate** | Reference to an `INLSubstrate` entry |
| **Solution** | One or more `PrecursorSolution` sub-sections |
| **Atmosphere** | Glovebox / ambient conditions |
| **Annealing** | Post-deposition anneal parameters |
| **Creates new thin film** | Toggle to auto-create linked film + stack entries |

Method-specific sections (e.g. `SpinCoatingRecipeSteps` for spin coating,
`SlotDieCoatingProperties` for slot-die) appear in the corresponding entry type.

### Using recipes { #using-recipes }

A `WetDepositionRecipe` stores a complete set of standard parameters that can
be stamped onto a new deposition entry.

1. Create a new entry → **Wet Deposition Recipe**.
2. Fill in the desired **Instrument**, **Atmosphere**, **Substrate**, **Solution**,
   **Annealing**, and **Quenching** sub-sections.
3. In a deposition entry, set **Recipe** to reference your recipe entry.
4. Tick **Apply recipe** and save.

During normalization, each recipe field is copied into the deposition entry
*only if that field is currently empty* (existing values are never overwritten).
After one successful application the **Apply recipe** toggle resets to `False`.

---

## STAR sputtering { #star-sputtering }

### Recording a sputtering experiment

1. Create a new entry → **STAR RF Sputtering** or **STAR DC Sputtering**.
2. Set **Name**, **Operator**, **Base pressure**, and **Samples**.
3. Add **Steps** – choose from pre-sputtering, stabilization, and sputtering
   step types. Each step takes duration, power/voltage/current, and gas flow.
4. Add one **Source** per magnetron gun in use. Assign a `SputteringTarget`
   reference inside each `SputteringSource`.
5. Tick **Creates new thin film** on any step to auto-generate the film/stack
   entries after normalization.

### Using sputtering recipes

A `StarSputteringRecipe` stores a reusable sequence of `StarStep` objects.

1. Create a new entry → **STAR Sputtering Recipe**. Add steps.
2. In a sputtering entry, set **Recipe** to reference the recipe.
3. Tick **Apply recipe** and save. The recipe steps are copied to the
   experiment's step list (existing steps are preserved).

### Target inventory

The `SputteringTarget` entry tracks cumulative usage of a physical target.

1. Create a new entry → **Sputtering Target**.
2. Fill in **Name**, **Delivery date**, **Installation date**, and **Components**
   (the target material composition).
3. Set **Calibration interval (time)** and/or **(energy)** to enable automatic
   recalibration alerts.

Every time a sputtering experiment that references this target is
normalized, a `TargetDepositionRecord` is appended to the target's
**Deposition records**. The target's **Total deposition time**,
**Total deposition energy**, and **Time/Energy since last calibration**
are recomputed automatically. If any threshold is exceeded,
**Needs calibration** is set to `True`.

---

## Characterization

### XRD measurement

1. Upload a diffractogram file (`.xrdml`, `.rasx`, `.brml`, or `.raw`).
   An `INLXRayDiffraction` entry is created automatically by the parser.
2. Open the entry, set **Operator**, and add a **Samples** reference pointing
   to the measured `INLThinFilmStack`.

### UV-Vis transmission

1. Upload a `.asc` UV-Vis file. An `INLUVVisTransmission` entry is created.
2. Set **Operator** and add a **Samples** reference.

### Cyclic voltammetry

1. Upload a `*mVs.xlsx` file (e.g. `sample_50mVs.xlsx`) — the parser creates
   a `PotentiostatMeasurement` entry automatically.
2. Set **Area electrode** if you want the plot to show current density
   instead of raw current.
3. After normalization, a CV curve is displayed (scan 3 by default, scan 2 as
   fallback).

### Chronoamperometry

1. Upload a `*ED.xlsx` file (e.g. `sample_ED.xlsx`) — the parser creates a
   `ChronoamperometryMeasurement` entry automatically.
2. Set **Voltage applied** and **Area electrode** as needed.
3. The normalized entry displays a current (density) vs. time plot.

### 4-Point probe sheet resistance

1. Upload a `*4pp.xls` or `*4pp.xlsx` file — the parser creates an
   `INLFourPointProbe` entry with the statistical summary and a spatial map.
2. Open the entry to review individual `INLFourPointProbeResults` sub-sections.

### KLA-Tencor profilometry

1. Upload a `*[Pp]rofile.pdf` file — the parser creates an
   `INLKLATencorProfiler` entry with step height and roughness values.
2. Each measurement site becomes an `INLKLATencorProfilerResults` sub-section.

### External Quantum Efficiency (EQE)

1. Upload a `*eqe*.txt` file (case-insensitive) — the parser creates an
   `INLEQE` entry with the EQE spectrum and extracted scalar parameters.
2. Link a sample via the **Samples** reference field.

### Solar cell IV

1. Upload a `*Results Table*.txt` file (case-insensitive) — the parser creates
   an `INLSolarCellIV` entry with JV curves and parameter boxplots.
2. The best-efficiency cell's JV curve is plotted automatically.

### GDOES depth profile

1. Upload a `*gdoes*.txt` file (case-insensitive) — the parser creates an
   `INLGDOES` entry with a per-element concentration vs. depth plot.

### SEM session

1. Upload FEI/ThermoFisher TIFF files named `YYMMDD - <name>.tif` (the base
   image without a `_NNN` suffix) — all related images
   (`YYMMDD - <name>_001.tif`, `_002.tif`, …) are grouped into one
   `INLSEMSession` entry automatically.
2. A gallery figure is generated with all images stacked vertically.
3. Set **Label** on individual `INLSEMImage` sub-sections to annotate images.

---

## File naming for automatic parsing

| Measurement type | Required file name pattern | Produces |
|-----------------|---------------------------|---------|
| Cyclic voltammetry | `*mVs.xlsx` | `PotentiostatMeasurement` |
| Chronoamperometry | `*ED.xlsx` | `ChronoamperometryMeasurement` |
| 4-Point probe | `*4pp.xls` or `*4pp.xlsx` | `INLFourPointProbe` |
| KLA-Tencor profilometry | `*[Pp]rofile.pdf` | `INLKLATencorProfiler` |
| EQE | `*eqe*.txt` *(case-insensitive)* | `INLEQE` |
| Solar cell IV | `*Results Table*.txt` *(case-insensitive)* | `INLSolarCellIV` |
| GDOES | `*gdoes*.txt` *(case-insensitive)* | `INLGDOES` |
| SEM session | `YYMMDD - <name>.tif` *(base image, no `_NNN` suffix)* | `INLSEMSession` |
