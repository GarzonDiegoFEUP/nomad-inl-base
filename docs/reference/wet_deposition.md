# Reference – Wet Deposition

This page documents all ELN entry types in the **INL Wet Deposition** category.

---

## WetDepositionRecipe

**Base class:** `EntryData`

A reusable template that stores standard parameters for a wet deposition process.
Apply it to a deposition entry by referencing it and ticking **Apply recipe**.

| Quantity | Type | Description |
|----------|------|-------------|
| `name` | `str` | Recipe name |
| `description` | `str` | Rich-text description |

**Sub-sections:**

| Sub-section | Type | Description |
|-------------|------|-------------|
| `instrument` | `InstrumentReference` | Default instrument |
| `atmosphere` | `Atmosphere` | Default atmosphere (glovebox, ambient …) |
| `solution` | `INLPrecursorSolution` (repeats) | Default precursor(s) |
| `steps` | `INLWetDepositionStep` (repeats) | Ordered process steps |

Recipe fields are copied to the deposition entry **only if the corresponding
field is currently empty** (non-destructive merge). The `apply_recipe` toggle
resets to `False` after a successful application.

### Method-specific recipe classes

Each deposition method has a dedicated recipe class that adds method-specific
fields on top of `WetDepositionRecipe`:

| Recipe class | Inherits | Extra fields |
|---|---|---|
| `INLSpinCoatingRecipe` | `INLSpinCoating` | All spin-coating fields (acts as a full template entry) |
| `INLSlotDieCoatingRecipe` | `WetDepositionRecipe` | `properties: SlotDieCoatingProperties` |
| `INLBladeCoatingRecipe` | `WetDepositionRecipe` | `properties: BladeCoatingProperties` |
| `INLInkjetPrintingRecipe` | `WetDepositionRecipe` | `properties: InkjetPrintingProperties` |
| `INLSprayPyrolysisRecipe` | `WetDepositionRecipe` | `properties: SprayPyrolysisProperties` |
| `INLDipCoatingRecipe` | `WetDepositionRecipe` | `properties: DipCoatingProperties` |
| `INLChemicalBathDepositionRecipe` | `WetDepositionRecipe` | `bath_temperature`, `duration`, `ph`, `stirring_speed`, `deposited_material` |

---

## INLThinFilmDeposition (base)

All deposition entry types below inherit from this base class.

### Shared quantities

| Quantity | Type | Description |
|----------|------|-------------|
| `name` | `str` | Entry name (inherited) |
| `operator` | `str` | Person who performed the deposition |
| `tags` | `str` (list) | Free-text tags for search and filtering |
| `deposited_material` | `str` | Material of the deposited film (auto-filled from solution solute name if not set) |
| `creates_new_thin_film` | `bool` | Auto-create or append an `INLThinFilm` + `INLThinFilmStack` entry |
| `apply_recipe` | `bool` | Copy recipe fields into this entry on normalize |

### Shared sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `instrument` | `InstrumentReference` | Instrument used |
| `atmosphere` | `Atmosphere` | Processing atmosphere |
| `substrate` | `INLSubstrateReference` | Bare substrate (used when depositing the first layer) |
| `sample` | `INLThinFilmStackReference` | Existing stack to append a new layer to (or resulting stack after creation) |
| `samples` | `INLSampleReference` (repeats) | Additional sample references |
| `recipe` | `WetDepositionRecipeReference` | Recipe to apply |
| `solution` | `INLPrecursorSolution` (repeats) | Precursor solutions |
| `steps` | `INLWetDepositionStep` (repeats) | Ordered process steps (spin, anneal, quench, …) |

### Process step types

Steps are added to the `steps` list. Available step types:

| Class | Label | Key quantities |
|-------|-------|----------------|
| `INLSpinCoatingStep` | Spin Coating Step | `speed` (rpm), `duration` (s), `acceleration` (rpm/s) |
| `INLHotplateAnnealingStep` | Hotplate Annealing Step | `temperature` (°C), `duration` (min) |
| `INLAntisolventQuenchingStep` | Antisolvent Quenching Step | `volume` (ml), `dispensing_speed` (ml/s) |

Each step can optionally carry its own `solution` sub-sections to override the
entry-level solution for that specific step.

### Auto-creation of film/stack entries

When `creates_new_thin_film` is `True`, normalization runs one of:

- **Case A – `sample` already set:** creates an `INLThinFilm` entry and appends
  it as a new layer to the existing stack (writes back to the stack YAML).
- **Case B – only `substrate` set:** creates an `INLThinFilm` entry and a new
  `INLThinFilmStack` linking the film and substrate; sets `sample`.
- **Case C – neither set:** logs a warning and skips creation.

In all cases `creates_new_thin_film` resets to `False` after one run.

---

## INLSpinCoating

**Inherits:** `INLThinFilmDeposition`  
**Method label:** `Spin Coating`  
**Ontology:** [CHMO:0001472](http://purl.obolibrary.org/obo/CHMO_0001472)

Uses the shared `steps` list (see base class). Add `INLSpinCoatingStep`,
`INLHotplateAnnealingStep`, and/or `INLAntisolventQuenchingStep` entries in order.

**Recipe class:** `INLSpinCoatingRecipe` — a full spin-coating entry that acts as
a reusable template (inherits all `INLSpinCoating` fields).

---

## INLSlotDieCoating

**Inherits:** `INLThinFilmDeposition`  
**Method label:** `Slot-Die Coating`  
**Ontology:** [TFSCO:00000075](https://purl.archive.org/tfsco/TFSCO_00000075)

| Sub-section | Type | Description |
|-------------|------|-------------|
| `properties` | `SlotDieCoatingProperties` | Head gap, coating speed, flow rate, etc. |

---

## INLBladeCoating

**Inherits:** `INLThinFilmDeposition`  
**Method label:** `Blade Coating`  
**Ontology:** [TFSCO:00002060](https://purl.archive.org/tfsco/TFSCO_00002060)

| Sub-section | Type | Description |
|-------------|------|-------------|
| `properties` | `BladeCoatingProperties` | Blade gap, speed, temperature, etc. |

---

## INLInkjetPrinting

**Inherits:** `INLThinFilmDeposition`  
**Method label:** `Inkjet Printing`  
**Ontology:** [TFSCO:00002053](https://purl.archive.org/tfsco/TFSCO_00002053)

| Sub-section | Type | Description |
|-------------|------|-------------|
| `properties` | `InkjetPrintingProperties` | Drop volume, firing frequency, nozzle parameters |

---

## INLSprayPyrolysis

**Inherits:** `INLThinFilmDeposition`  
**Method label:** `Spray Pyrolysis`  
**Ontology:** [CHMO:0001516](http://purl.obolibrary.org/obo/CHMO_0001516)

| Sub-section | Type | Description |
|-------------|------|-------------|
| `properties` | `SprayPyrolysisProperties` | Nozzle type, carrier gas, substrate temperature |

---

## INLDipCoating

**Inherits:** `INLThinFilmDeposition`  
**Method label:** `Dip Coating`  
**Ontology:** [CHMO:0001471](http://purl.obolibrary.org/obo/CHMO_0001471)

| Sub-section | Type | Description |
|-------------|------|-------------|
| `properties` | `DipCoatingProperties` | Withdrawal speed, immersion time, solution viscosity |

---

## INLChemicalBathDeposition

**Inherits:** `INLThinFilmDeposition`  
**Method label:** `Chemical Bath Deposition`  
**Ontology:** [CHMO:0001465](http://purl.obolibrary.org/obo/CHMO_0001465)

Additional quantities specific to CBD:

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `bath_temperature` | `float` | °C | Temperature of the chemical bath |
| `duration` | `float` | min | Total deposition duration |
| `ph` | `float` | – | pH of the bath |
| `color_change_time` | `float` | min | Time at which a colour change was observed |
| `stirring_speed` | `float` | rpm | Stirring speed during deposition |
