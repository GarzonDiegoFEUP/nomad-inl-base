# Reference – METEOR E-Beam Evaporation (Metal EvaporaTion by Electron-beam for SOlar Research)

This page documents all ELN entry types in the **METEOR** category, which
covers e-beam evaporation experiments performed on the Korvus Technology
METEOR system at INL.

---

## METEORDeposition

**Category:** METEOR  
**Base class:** `Process`, `EntryData`  
**Label:** *METEOR E-Beam Evaporation*

A single e-beam evaporation run. Time-series data is populated automatically
by the `.nbl` log parser. Per-pocket materials and the mask description must
be entered manually in the ELN.

### Quantities

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `log_datetime` | `Datetime` | – | Timestamp extracted from the `.nbl` file header |
| `mask` | `str` | – | Description of the contact shadow mask (free text) |
| `creates_new_thin_film` | `bool` | – | Toggle to auto-create `INLThinFilm` + `INLThinFilmStack` entries |
| `elapsed_time` | `float[]` | s | Elapsed time from the first log row |
| `chamber_pressure` | `float[]` | mbar | Chamber pressure time series |
| `substrate_temperature` | `float[]` | °C | Substrate temperature time series |
| `ebeam_power` | `float[]` | W | Global e-beam filament power time series |
| `ebeam_current_percentage` | `float[]` | % | E-beam emission current as % of maximum |
| `rotation_speed` | `float[]` | rpm | Substrate holder rotation speed time series |

### Sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `samples` | `INLSampleReference` (repeats) | Samples coated in this run |
| `substrate` | `INLSubstrateReference` | Substrate used when no pre-existing sample is set |
| `pockets` | `METEORPocket` (repeats, max 4) | Per-pocket evaporation data |
| `qcm` | `METEORQCMMonitor` | QCM thickness monitor data |

### Normalization behavior

When `creates_new_thin_film` is `True`:

1. Finds the first `METEORPocket` with a `material` field set.
2. Determines the film thickness:
   - Uses `qcm.thickness_override` if set.
   - Falls back to `qcm.thickness` (parser-filled from last log row).
3. Creates an `INLThinFilm` entry (named `<entry_name>_thin_film`).
4. Creates an `INLThinFilmStack` entry (named `<entry_name>_thin_film_stack`)
   linking the film and substrate.
5. Resets `creates_new_thin_film` to `False`.

If a thin film stack reference is already present, the step is skipped so
re-normalization is safe.

---

## METEORPocket

**Base class:** `ArchiveSection`  
**Label:** *E-Beam Pocket*

Represents one of the four e-beam evaporation pockets.

### Quantities

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `name` | `str` | – | Pocket label (e.g. `"Pocket 1"`) |
| `pocket_index` | `int` | – | Pocket number (1–4) |
| `filament_current` | `float[]` | A | E-beam filament current (`Fil N(A)` column) |
| `set_power` | `float[]` | W | Target power (first `Power N(W)` column) |
| `measured_power` | `float[]` | W | Actual power (second `Power N(W)` column) |
| `flux` | `float[]` | nA | Ion flux reading |
| `enabled` | `bool[]` | – | Shutter state (open = `True`) per time point |

### Sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `material` | `PureSubstanceSection` | Material loaded in this pocket; type a name or formula for PubChem lookup |

---

## METEORQCMMonitor

**Base class:** `ArchiveSection`  
**Label:** *QCM Monitor*

Quartz crystal microbalance data from the Korvus log.

### Quantities

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `frequency` | `float[]` | Hz | Crystal oscillation frequency time series |
| `deposition_rate` | `float[]` | Å/s | Instantaneous deposition rate time series |
| `thickness` | `float` | Å | Final cumulative QCM thickness (last log row) *(auto-filled by parser)* |
| `thickness_override` | `float` | Å | User-supplied thickness; takes precedence over `thickness` for film creation |
| `density` | `float` | g/cm³ | Material density configured in the QCM controller |
| `tooling_factor` | `float` | % | QCM tooling correction factor |

---

## .nbl log format

Korvus `.nbl` files contain a single-line preamble that concatenates the
machine name, the run datetime, and all column headers without a delimiter
between them:

```
METEOR 08/05/2026 16:06:08Time,Pressure(mBar),…
```

The parser:

1. Extracts the datetime string via a `DD/MM/YYYY HH:MM:SS` regex.
2. Locates the `Time,` token to find where headers begin.
3. Splits headers on `,`, strips whitespace, and drops empty tokens.
4. Renames the second set of `Power N(W)` columns to `Measured Power N(W)`
   to resolve Korvus's duplicate column names.
5. Appends a dummy `_trailing` column to absorb the trailing comma present
   on every data row.

The parser is registered for all `*.nbl` files and writes a guarded
(`guard=True`) child archive so that user edits to the ELN are not
overwritten on subsequent parses.

### Column mapping

| `.nbl` column | NOMAD field | Notes |
|---------------|-------------|-------|
| `Time` | `elapsed_time` | Offset to zero from first row |
| `Pressure(mBar)` | `chamber_pressure` | × 100 → Pa |
| `Speed(Hz)` | `qcm.frequency` | QCM crystal frequency |
| `Rate(A/s)` | `qcm.deposition_rate` | × 1e-10 → m/s |
| `Thickness(A)` | `qcm.thickness` | Last valid value × 1e-10 → m |
| `Density(g/cc)` | `qcm.density` | Median × 1000 → kg/m³ |
| `Tooling(%)` | `qcm.tooling_factor` | Median |
| `Fil N(A)` (N=1–4) | `pockets[N-1].filament_current` | |
| `Power N(W)` (first set) | `pockets[N-1].set_power` | |
| `Measured Power N(W)` (renamed) | `pockets[N-1].measured_power` | |
| `Flux N(nA)` | `pockets[N-1].flux` | |
| `Shutter N` | `pockets[N-1].enabled` | Interpreted as bool |
| `Temp(C)` | `substrate_temperature` | + 273.15 → K |
| `Power(W)` | `ebeam_power` | Global e-beam power |
| `Current(%)` | `ebeam_current_percentage` | |
| `Rotation speed(RPM)` | `rotation_speed` | |
