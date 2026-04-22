# Reference – Characterization

This page documents all ELN entry types in the **INL Characterization** category.

---

## INLXRayDiffraction

**Base class:** `ELNXRayDiffraction`, `EntryData`  
**Label:** `INL XRD`

Extends the `nomad-measurements` XRD schema with an operator field and a
sample reference. Supported file formats: `.xrdml`, `.rasx`, `.brml`, `.raw`.

| Quantity | Type | Description |
|----------|------|-------------|
| `operator` | `str` | Person who ran the measurement |

**Sub-sections:**

| Sub-section | Type | Description |
|-------------|------|-------------|
| `samples` | `INLSampleReference` (repeats) | Thin-film stacks measured |

`INLSampleReference` references an `INLThinFilmStack` entry, linking the
measurement directly to the sample provenance chain.

---

## INLUVVisTransmission

**Base class:** `ELNUVVisNirTransmission`, `EntryData`  
**Label:** `INL UV-Vis Transmission`

Extends the `nomad-measurements` UV-Vis schema. Supported file format: `.asc`.

| Quantity | Type | Description |
|----------|------|-------------|
| `operator` | `str` | Person who ran the measurement |

**Sub-sections:**

| Sub-section | Type | Description |
|-------------|------|-------------|
| `samples` | `INLSampleReference` (repeats) | Thin-film stacks measured |

---

## WorkingElectrode

**Base class:** `INLThinFilmStack`, `EntryData`  
**Label:** defined by `INLThinFilmStack`  
**Ontology:** [voc4cat:0007206](https://w3id.org/nfdi4cat/voc4cat_0007206)

A thin-film stack entry extended with the electrode area used in electrochemical
measurements.

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `area_electrode` | `float` | cm² | Active electrode area |

Inherits all `INLThinFilmStack` fields: `layers`, `substrate`, `components`.

---

## ElectrolyteSolution

**Base class:** `Solution`  
**Ontology:** [voc4cat:0007206](https://w3id.org/nfdi4cat/voc4cat_0007206)

Extends the solution schema with electrochemistry-specific concentration fields.

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `molar_concentration` | `float` | mol/L | Molar concentration |
| `molal_concentration` | `float` | mol/kg | Molal concentration |

---

## ChronoamperometryMeasurement

**Base class:** `PlotSection`, `Measurement`, `EntryData`  
**Label:** `INL Chronoamperometry`  
**Ontology:** [voc4cat:0007206](https://w3id.org/nfdi4cat/voc4cat_0007206)

Records a constant-potential electrochemical experiment and auto-generates a
current (density) vs. time plot.

### Quantities

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `voltage_applied` | `float` | V | Applied potential during the experiment |
| `area_electrode` | `float` | cm² | Electrode area for current density calculation |

### Sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `current` | `CurrentTimeSeries` | Time-resolved current measurements |

### Normalization behavior

- Converts current to mA
- If `area_electrode` is set, divides by area and labels the axis
  *Current density (mA cm⁻²)*; otherwise labels it *Current (mA)*
- Generates a Plotly scatter figure (time on x-axis)

---

## PotentiostatMeasurement

**Base class:** `PlotSection`, `Measurement`, `EntryData`  
**Label:** `INL Cyclic Voltammetry`  
**Ontology:** [voc4cat:0007206](https://w3id.org/nfdi4cat/voc4cat_0007206)

Records a cyclic voltammetry experiment and auto-generates a CV curve.

### Quantities

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `rate` | `float` | mV/s | Scan rate |
| `area_electrode` | `float` | cm² | Electrode area for current density calculation |

### Sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `current` | `CurrentTimeSeries` | Time-resolved current |
| `voltage` | `VoltageTimeSeries` | Time-resolved voltage |
| `scan` | `ScanTimeSeries` | Scan index as a function of time |

### Normalization behavior

- Plots the CV curve for **scan 3**; falls back to **scan 2** if scan 3 is
  entirely `NaN`
- If `area_electrode` is set, the y-axis shows current density (mA cm⁻²)
- Generates a Plotly scatter figure (voltage on x-axis)

---

## Time-series helper sections

These internal sections hold the raw array data for electrochemical measurements.
They inherit from `TimeSeries` and hide the `set_value` and `set_time` fields.

| Class | Unit of `value` | Description |
|-------|----------------|-------------|
| `CurrentTimeSeries` | A | Current as a function of time |
| `CurrentDensityTimeSeries` | A/m² | Current density as a function of time |
| `VoltageTimeSeries` | V | Voltage as a function of time |
| `ScanTimeSeries` | – | Scan index as a function of time |

---

## INLFourPointProbe

**Base class:** `INLCharacterization`  
**Label:** `INL 4-Point Probe`

Sheet resistance and resistivity map from a 4-point probe instrument.
A spatial scatter plot coloured by sheet resistance is auto-generated during
normalization.

**File format:** upload a `*4pp.xls` or `*4pp.xlsx` file — the parser creates
the entry automatically.

### Quantities

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `x_size` | `float` | mm | Sample X dimension |
| `y_size` | `float` | mm | Sample Y dimension |
| `exclusion_size` | `float` | mm | Edge exclusion zone |
| `correction_factor` | `float` | – | Geometric correction factor F |
| `probe_spacing` | `float` | mm | Distance between probe tips |
| `temperature_coefficient` | `float` | – | Resistance temperature coefficient |
| `measurement_temperature` | `float` | °C | Measurement temperature |
| `reference_temperature` | `float` | °C | Reference temperature for correction |
| `measurement_mode` | `str` | – | Instrument mode (e.g. `SetPoint`) |

### Sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `results` | `INLFourPointProbeResults` (repeats) | Statistics and per-point data per run |

### INLFourPointProbeResults

Sub-section holding the statistical summary and per-point arrays for a single
measurement run. A sheet-resistance spatial map is plotted automatically.

**Statistics:**

| Quantity | Unit | Description |
|----------|------|-------------|
| `sigma_3_max` / `sigma_3_min` | Ω/sq | 3 σ bounds of sheet resistance |
| `sheet_resistance_max` / `min` | Ω/sq | Maximum / minimum across all points |
| `sheet_resistance_ave` | Ω/sq | Mean sheet resistance |
| `sheet_resistance_std_dev` | Ω/sq | Standard deviation |
| `uniformity_pct` | % | Uniformity Uni(%) |
| `sheet_resistance_range` | Ω/sq | Max − Min range |
| `std_dev_over_ave_pct` | % | StDev/Ave(%) |

**Per-point arrays:**

| Quantity | Unit | Description |
|----------|------|-------------|
| `x_position` / `y_position` | mm | Coordinates of each point |
| `sheet_resistance` | Ω/sq | Sheet resistance at each point |
| `resistivity` | Ω·cm | Resistivity at each point |

---

## INLKLATencorProfiler

**Base class:** `INLCharacterization`  
**Label:** `INL KLA-Tencor Profiler`

Stylus profilometry measurement from the KLA-Tencor P-series profiler.

**File format:** upload a `*[Pp]rofile.pdf` file — the parser creates the entry
automatically.

### Quantities

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `recipe` | `str` | – | Instrument recipe name |
| `site_name` | `str` | – | Site label from the instrument |
| `scan_length` | `float` | µm | Total scan length |
| `scan_speed` | `float` | µm/s | Stylus scan speed |
| `sample_rate` | `float` | Hz | Data acquisition rate |
| `scan_direction` | `str` | – | Scan direction |
| `repeats` | `int` | – | Number of scan repeats |
| `stylus_force` | `float` | mg | Stylus contact force |
| `noise_filter` | `float` | µm | Noise filter wavelength cut-off |

### Sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `results` | `INLKLATencorProfilerResults` (repeats) | Step height and roughness parameters per site |

### INLKLATencorProfilerResults

| Quantity | Unit | Description |
|----------|------|-------------|
| `step_height` | Å | Step height (St Height) between cursor regions |
| `Ra` | Å | Average roughness |
| `max_Ra` | Å | Maximum Ra over the roughness trace |
| `Rq` | Å | RMS roughness |
| `Rh` | Å | Peak-to-valley height |

---

## INLEQE

**Base class:** `INLCharacterization`, `PlotSection`  
**Label:** `INL EQE`

External Quantum Efficiency measurement. Plots EQE (%) vs. wavelength (nm)
and stores scalar parameters extracted from the curve.

**File format:** upload a `*eqe*.txt` file (case-insensitive) — the parser
creates the entry automatically.

### Quantities

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `wavelength` | `float[]` | nm | Wavelength array |
| `quantum_efficiency` | `float[]` | – | EQE values (fraction 0–1) |

### Sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `results` | `EQEResult` (repeats) | Scalar parameters extracted from the curve |

### EQEResult

| Quantity | Unit | Description |
|----------|------|-------------|
| `jsc` | mA/cm² | Short-circuit current density (AM1.5G integration) |
| `bandgap` | eV | Bandgap estimated from EQE |
| `device_id` | – | Device identifier |
| `chopping_frequency` | Hz | Chopping frequency used |
| `light_bias_current` | mA | Light bias current |
| `voltage_bias` | V | Voltage bias applied |

---

## INLSolarCellIV

**Base class:** `INLCharacterization`, `PlotSection`  
**Label:** `INL Solar Cell IV`

Solar cell current–voltage measurement. Plots the best-cell JV curve and, when
multiple cells are measured, boxplots of Voc, Jsc, FF, and efficiency.

**File format:** upload a `*Results Table*.txt` file (case-insensitive) — the
parser creates the entry automatically.

### Sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `results` | `SolarCellIVResult` (repeats) | Extracted parameters per cell |
| `iv_curves` | `SolarCellIVCurve` (repeats) | Raw I-V curve data per cell |

### SolarCellIVResult

| Quantity | Unit | Description |
|----------|------|-------------|
| `voc` | V | Open-circuit voltage |
| `isc` | A | Short-circuit current |
| `jsc` | mA/cm² | Short-circuit current density |
| `vmax` | V | Voltage at maximum power |
| `pmax` | mW | Maximum power |
| `fill_factor` | – | Fill factor (0–1) |
| `efficiency` | – | Power conversion efficiency (0–1) |
| `cell_area` | cm² | Active cell area |
| `r_shunt` | Ω·cm² | Area-normalised shunt resistance |
| `r_series` | Ω·cm² | Area-normalised series resistance |
| `r_at_voc` | Ω | Differential resistance at Voc |
| `r_at_isc` | Ω | Differential resistance at Isc |
| `exposure` | s | Illumination exposure time |

### SolarCellIVCurve

| Quantity | Unit | Description |
|----------|------|-------------|
| `measurement_name` | – | Label matching the corresponding `SolarCellIVResult` |
| `voltage` | V | Measured voltage array |
| `current` | A | Measured current array |

### Normalization behavior

- Plots the JV curve for the cell with the highest efficiency (current density
  in mA/cm² when `cell_area` is available; raw mA otherwise)
- When more than one cell is present, adds boxplots of Voc, Jsc, FF, and
  efficiency

---

## INLGDOES

**Base class:** `INLCharacterization`, `PlotSection`  
**Label:** `INL GDOES`

Glow Discharge Optical Emission Spectroscopy depth profile. Plots elemental
concentration (mol %) vs. depth (µm) with one trace per element.

**File format:** upload a `*gdoes*.txt` file (case-insensitive) — the parser
creates the entry automatically.

### Quantities

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `depth` | `float[]` | µm | Depth profile values |

### Sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `element_profiles` | `GDOESElementProfile` (repeats) | Per-element concentration profile |

### GDOESElementProfile

| Quantity | Description |
|----------|-------------|
| `element_name` | Element label as it appears in the data file |
| `concentration` | Concentration values (mol %) |

---

## INLSEMSession

**Base class:** `INLCharacterization`, `PlotSection`  
**Label:** `INL SEM Session`

One or more SEM images acquired during a single microscope session. Acquisition
metadata is parsed from the FEI/ThermoFisher TIFF tag 34682. A gallery figure
is generated with all images stacked vertically.

**File format:** upload a ZIP containing FEI/TFS TIFF files, or drop the base
image file directly. The parser matches files named
`YYMMDD - <name>.tif` (no `_NNN` suffix) and collects all related images
(`YYMMDD - <name>_001.tif`, `_002.tif`, …) into a single `INLSEMSession` entry.

### Quantities

| Quantity | Type | Description |
|----------|------|-------------|
| `microscope_model` | `str` | Model name from `System/SystemType` |
| `source_type` | `str` | Electron source type from `System/Source` |

### Sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `images` | `INLSEMImage` (repeats) | Individual images in the session |

### INLSEMImage

Holds pixel data and all acquisition metadata for one image. A calibrated
(µm-axis) Plotly heatmap is generated per image during normalization.

| Quantity | Unit | Description |
|----------|------|-------------|
| `file_name` | – | File name within the ZIP |
| `label` | – | User annotation |
| `image_array` | – | Grayscale pixel data (downsampled to ≤ 1024 px) |
| `accelerating_voltage` | kV | Beam voltage |
| `magnification` | – | Nominal magnification |
| `horizontal_field_width` | µm | Physical width of the full image |
| `pixel_width` | nm | Physical width of one pixel |
| `working_distance` | mm | Working distance |
| `detector_name` | – | Detector name (e.g. `ETD`, `CBS`) |
| `detector_mode` | – | Signal mode (e.g. `SE`, `BSE`) |
| `emission_current` | µA | Source emission current |
| `dwell_time` | µs | Pixel dwell time |
| `stage_x` / `y` / `z` | mm | Stage position |
| `stage_tilt` | ° | Stage tilt angle |
| `acquisition_datetime` | – | Date and time of acquisition |
| `operator` | – | Operator username |
