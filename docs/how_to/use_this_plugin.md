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

## STAR sputtering (SpuTtering for Advanced Research) { #star-sputtering }

### Recording a sputtering experiment

1. Create a new entry → **STAR RF Sputtering** or **STAR DC Sputtering**.
2. Set **Name**, **Operator**, **Base pressure**, and **Samples**.
3. Add **Steps** – choose from pre-sputtering, stabilization, and sputtering
   step types. Each step takes duration, power/voltage/current, and gas flow.
4. Add one **Source** per magnetron gun in use. Assign a `SputteringTarget`
   reference inside each `SputteringSource`.
5. Tick **Creates new thin film** on any step to auto-generate the film/stack
   entries after normalization.

### Substrate heating and rotation

All STAR step types (RF, DC, reactive DC, and Se annealing) expose four
optional fields for each step:

| Field | Unit | Description |
|-------|------|-------------|
| **Substrate set temperature** | °C | Set-point temperature on the substrate heater |
| **Rotation enabled** | bool | Whether substrate rotation is active |
| **Rotation speed** | rpm | Target rotation speed |
| **Rotation direction** | enum | `Clockwise` or `Counter-clockwise` |

Set these on any step where the substrate is heated or rotated during that
particular phase.

### Reactive DC sputtering (with pulsed selenium)

Use **STAR DC Reactive Sputtering** when a pulsed selenium environment is
required simultaneously with metal sputtering (e.g. CIGS co-deposition).

1. Create a new entry → **STAR DC Reactive Sputtering**.
2. Fill in sources and standard DC parameters as usual.
3. For each step that needs selenium, expand the **Selenium Pulse Parameters**
   sub-section (**Selenium environment**) and set:

   | Field | Description |
   |-------|-------------|
   | **Selenium cell** | Reference to a `Selenium Cell` entity |
   | **Valve opening** | Valve aperture controlling Se flux (mm) |
   | **Time on / Time off** | Pulse duty cycle (s) |
   | **Cell temperature** | Effusion cell temperature (°C) |
   | **Cracker current / Cracker voltage** | Cracker supply parameters |
   | **Cracker power** | Auto-computed from current × voltage |
   | **Cracker power percentage** | % of maximum cracker power |
   | **Process time** | Total step duration for Se pulsing (min) |
   | **Total Se on time** | Auto-computed total selenium exposure (s) |

   !!! tip
       **Cracker power** and **Total Se on time** are filled automatically
       on normalization – no manual entry needed.

### Selenization annealing

Use **STAR Selenization Annealing** to anneal a sample in a selenium
atmosphere inside the STAR chamber without activating any sputtering targets.

1. Create a new entry → **STAR Selenization Annealing**.
2. Set **Name**, **Operator**, **Base pressure**, and **Samples**. The
   **Sources** field is hidden (not applicable).
3. Add one or more **Se Annealing Step** sub-sections. Each step exposes
   the same **Selenium Pulse Parameters** as reactive DC steps, plus the
   substrate heating and rotation fields.

### Selenium cell entity

`Selenium Cell` is a shared entity that tracks the state of a physical
selenium effusion cell over time.

1. Create a new entry → **Selenium Cell** (under the *STAR* category).
2. Add a **Weight Record** for each time the cell is weighed:
   - **Weight** (g)
   - **Measurement date**
3. Set **Refill date** when the cell is refilled.

Reference this entry from the **Selenium cell** field inside any
`INLSeleniumPulseParameters` sub-section to link a process to the specific
cell used.

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

### EDX/EDS spectrum

1. Upload an EMSA/MAS text file (`.txt`, `.msa`, `.emsa`, or `.ems`) whose
   first few lines contain `#FORMAT : EMSA` — the parser creates an
   `INLEDXSpectrum` entry with a counts vs. energy plot.
2. Acquisition metadata (beam energy, live time, stage position, etc.) is
   parsed from the EMSA header automatically.

### SEM session

1. Upload FEI/ThermoFisher TIFF files named `YYMMDD - <name>.tif` (the base
   image without a `_NNN` suffix) — all related images
   (`YYMMDD - <name>_001.tif`, `_002.tif`, …) are grouped into one
   `INLSEMSession` entry automatically.
2. A gallery figure is generated with all images stacked vertically.
3. Set **Label** on individual `INLSEMImage` sub-sections to annotate images.

### Bruker AFM/KPFM/cAFM session

1. Upload a Bruker NanoScope binary file with a numbered extension
   (e.g. `sample.001`, `sample.002`, …) — the parser creates an
   `INLAFMSession` entry automatically.
2. The technique (`AFM`, `KPFM`, or `cAFM`) is detected from the channel
   names in the file and stored in the **Technique** field.
3. Each image channel (Height Sensor, Amplitude, Surface Potential, etc.)
   becomes an `INLAFMChannel` sub-section, and a calibrated Plotly heatmap
   with µm axes is generated for every channel.

### EIS (Electrochemical Impedance Spectroscopy)

1. Upload a Bio-Logic `.mpr` file containing a PEIS or GEIS experiment —
   the parser creates an `EISMeasurement` entry automatically.

---

## Analysis with Jupyter notebooks { #analysis }

INL provides four `JupyterAnalysis` schemas — for EQE, Solar Cell IV, GDOES,
and XRD — that generate a pre-populated Jupyter notebook linked to an
analysis ELN entry. See [Reference – Analysis](../reference/analysis.md) for
the full list of fields and what each notebook does.

1. Create a new entry of the desired type, e.g. **INL XRD Jupyter Analysis**.
2. Set **Search queries for inputs** to match the measurement entries you
   want to analyze (e.g. all `INLXRayDiffraction` entries for a sample).
3. Click **Reset Inputs** to populate the **Inputs** sub-section from the
   query.
4. Click **Generate Notebook**. A `.ipynb` file is created and linked in
   **Notebook**.
5. Open **Notebook** and run the cells. The linked entry is loaded into the
   `analysis` variable, and its inputs are available as `analysis.inputs`.

!!! tip
    If you edit the notebook and want to regenerate it from scratch, clear
    the **Notebook** field first — **Generate Notebook** does nothing while a
    notebook is already linked.

---

## METEOR e-beam evaporation (Metal EvaporaTion by Electron-beam for SOlar Research) { #meteor }

The **METEOR** instrument (Korvus Technology) is an e-beam evaporator with
four independent pockets and a QCM thickness monitor. Log files (`.nbl`)
are parsed automatically on upload.

### Uploading a log file

1. Upload a `*.nbl` Korvus log file to your NOMAD upload.
2. The parser creates a **METEOR E-Beam Evaporation** entry named
   `<filename>.METEORDeposition` automatically.
3. All time-series data (elapsed time, chamber pressure, substrate
   temperature, e-beam power, rotation speed, per-pocket currents/power/flux,
   QCM frequency and rate) are imported. The log datetime is extracted from
   the file header.

### Configuring the entry

After the parser run, open the created entry and fill in the following
fields manually:

| Field | Description |
|-------|-------------|
| **Mask** | Description of the contact shadow mask (e.g. `"shadow mask A, 2 mm circular contacts"`) |
| **Samples** | Reference(s) to existing `INLThinFilmStack` sample entries |
| **Substrate** | Reference to an `INLSubstrate` entry (used for new film creation if no sample is set) |
| **Pockets → Material** | For each active pocket, type the material name (e.g. `"Gold"`) to trigger a PubChem lookup |
| **QCM Monitor → Thickness override** | Override the parser-read QCM thickness with a manually measured value (Å) |

### Auto-creating a thin film entry

1. Set the **Material** on at least one `METEORPocket` (the first pocket
   with a material set is used).
2. Ensure either **Samples** or **Substrate** is filled.
3. Tick **Creates new thin film** and click **Process** (or save and
   re-normalize).

During normalization:

- An `INLThinFilm` entry is created with the pocket material and the
  QCM thickness (`Thickness override` takes precedence over the parsed value).
- An `INLThinFilmStack` entry is created, linking the film and substrate.
- The `Creates new thin film` toggle resets to `False` automatically.

### Understanding per-pocket data

Each of the four `METEORPocket` sub-sections contains:

| Field | Description |
|-------|-------------|
| **Pocket index** | 1–4 |
| **Material** | `PureSubstanceSection` (PubChem lookup) |
| **Filament current** | Fil N(A) time series |
| **Set power** | Target power (first `Power N(W)` column) |
| **Measured power** | Actual power (second `Power N(W)` column, logged by Korvus) |
| **Flux** | Ion flux (nA) |
| **Enabled** | Shutter open/closed state per time point |

### Understanding QCM data

The `METEORQCMMonitor` sub-section captures:

| Field | Description |
|-------|-------------|
| **Frequency** | Crystal oscillation frequency (Hz) |
| **Deposition rate** | Instantaneous rate (Å/s) |
| **QCM thickness** | Final cumulative thickness from the last log row (Å) |
| **Thickness override** | User value; takes precedence over QCM thickness for film creation |
| **Density** | Material density in the QCM controller (g/cm³) |
| **Tooling factor** | QCM tooling correction factor (%) |

---

## File naming for automatic parsing

| Measurement type | Required file name pattern | Produces |
|-----------------|---------------------------|---------|
| Cyclic voltammetry (xlsx) | `*mVs.xlsx` | `PotentiostatMeasurement` |
| Chronoamperometry | `*ED.xlsx` | `ChronoamperometryMeasurement` |
| 4-Point probe | `*4pp.xls` or `*4pp.xlsx` | `INLFourPointProbe` |
| KLA-Tencor profilometry | `*[Pp]rofile.pdf` | `INLKLATencorProfiler` |
| EQE | `*eqe*.txt` *(case-insensitive)* | `INLEQE` |
| Solar cell IV | `*Results Table*.txt` *(case-insensitive)* | `INLSolarCellIV` |
| GDOES | `*gdoes*.txt` *(case-insensitive)* | `INLGDOES` |
| SEM session | `YYMMDD - <name>.tif` *(base image, no `_NNN` suffix)* | `INLSEMSession` |
| EDX/EDS spectrum | `.txt`/`.msa`/`.emsa`/`.ems` with `#FORMAT : EMSA` header | `INLEDXSpectrum` |
| Bruker AFM/KPFM/cAFM | `*.001`, `*.002`, … *(numbered Bruker binary)* | `INLAFMSession` |
| EIS / CV / IV (Bio-Logic) | `*.mpr` *(technique auto-detected from data columns)* | `EISMeasurement` or `PotentiostatMeasurement` |
