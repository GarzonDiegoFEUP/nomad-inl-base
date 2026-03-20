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
