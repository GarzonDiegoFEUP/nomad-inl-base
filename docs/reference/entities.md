# Reference – Shared Entities

This page documents all shared entity entry types provided by `nomad-inl-base`.
These entries are created once and referenced by deposition and characterization
schemas throughout the experiment lifecycle.

---

## INLSubstrate

**Category:** INL Entities  
**Base class:** `Substrate`, `INLSample`, `EntryData`  
**Label:** `INL Substrate`

A physical substrate entry. Default geometry (25 × 25 × 1 mm) is filled in
automatically if none is provided.

| Quantity | Type | Default | Description |
|----------|------|---------|-------------|
| `name` | `str` | – | Human-readable name (inherited) |
| `lab_id` | `str` | – | Unique lab identifier (inherited) |
| `material` | `str` | `SLG` | Substrate material |
| `location` | `str` | – | Physical location (fridge, glovebox, …) |
| `status` | `enum` | – | `active`, `in use`, `consumed`, `broken`, or `archived` |

**Sub-sections:**

| Sub-section | Type | Description |
|-------------|------|-------------|
| `geometry` | `Geometry` | Physical dimensions (auto-filled as 25×25×1 mm) |

---

## INLThinFilm

**Category:** INL Entities  
**Base class:** `ThinFilm`, `INLSample`, `EntryData`  
**Label:** `INL Thin Film`

A single deposited layer. Geometry height is set from `thickness` during
normalization. Usually created automatically by deposition entries when
**Create / append film** is toggled.

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `material` | `str` | – | Material identifier |
| `thickness` | `float` | nm | Film thickness (also sets `geometry.height`) |
| `location` | `str` | – | Physical location |
| `status` | `enum` | – | Sample status |

---

## INLThinFilmStack

**Category:** INL Entities  
**Base class:** `ThinFilmStack`, `INLSample`, `EntryData`  
**Label:** `INL Thin Film Stack`

A substrate + one or more thin-film layers combined into a single sample entry.
During normalization, substrate dimensions are propagated to each film's geometry
and `components` is rebuilt automatically.

| Quantity | Type | Description |
|----------|------|-------------|
| `location` | `str` | Physical location |
| `status` | `enum` | Sample status |

**Sub-sections:**

| Sub-section | Type | Description |
|-------------|------|-------------|
| `substrate` | `INLSubstrateReference` | Substrate the layers were deposited on |
| `layers` | `INLThinFilmReference` (repeats) | Ordered thin-film layers (bottom → top) |
| `components` | `SystemComponent` (repeats) | Built automatically during normalization |

---

## INLInstrument

**Category:** INL Entities  
**Base class:** `Instrument`, `EntryData`  
**Label:** `INL Instrument`

A persistent record of a laboratory instrument. Used as a reference target
in deposition and characterization entries.

| Quantity | Type | Description |
|----------|------|-------------|
| `name` | `str` | Instrument name (inherited) |
| `supplier` | `str` | Manufacturer or supplier |
| `lab_id` | `str` | Lab identifier where the instrument is located |

**Sub-sections:**

| Sub-section | Type | Description |
|-------------|------|-------------|
| `maintenance_log` | `INLMaintenanceLog` (repeats) | Chronological log of maintenance events |

### INLMaintenanceLog

| Quantity | Type | Description |
|----------|------|-------------|
| `date` | `Datetime` | Date and time of the event |
| `performed_by` | `str` | Person who performed the maintenance |
| `description` | `str` | Rich-text description of work performed |

---

## INLGraphiteBox

**Category:** INL Entities  
**Base class:** `INLInstrument`  
**Label:** `INL Graphite Box`

A graphite box used in tube furnace annealing processes. Inherits all
`INLInstrument` fields.

**Sub-sections:**

| Sub-section | Type | Description |
|-------------|------|-------------|
| `geometry` | `RectangleCuboid` | Dimensions of the box (length × width × height) |

---

## INLSampleFragment

**Category:** INL Entities  
**Base class:** `INLSample`, `EntryData`  
**Label:** `INL Sample Fragment`

A fragment cut or broken from a parent sample (substrate, thin film, or stack)
at any stage of preparation. Keeps the full provenance chain intact.

| Quantity | Type | Description |
|----------|------|-------------|
| `parent_sample` | `INLSample` | Reference to the parent sample |
| `fraction` | `str` | Fraction label (e.g. `1/2`, `1/4`, `triangle`) |
| `cut_date` | `Datetime` | Date when the fragment was separated |
| `location` | `str` | Physical location |
| `status` | `enum` | Sample status |
