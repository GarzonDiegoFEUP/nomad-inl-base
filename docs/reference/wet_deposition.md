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
| `substrate` | `INLSubstrateReference` | Default substrate |
| `solution` | `PrecursorSolution` (repeats) | Default precursor(s) |
| `annealing` | `Annealing` | Default annealing conditions |
| `quenching` | `Quenching` | Default quenching conditions |

Recipe fields are copied to the deposition entry **only if the corresponding
field is currently empty** (non-destructive merge). The `apply_recipe` toggle
resets to `False` after a successful application.

---

## INLThinFilmDeposition (base)

All deposition entry types below inherit from this base class.

### Shared quantities

| Quantity | Type | Description |
|----------|------|-------------|
| `name` | `str` | Entry name (inherited) |
| `operator` | `str` | Person who performed the deposition |
| `tags` | `str` (list) | Free-text tags for search and filtering |
| `creates_new_thin_film` | `bool` | Auto-create `INLThinFilm` + `INLThinFilmStack` entries |
| `apply_recipe` | `bool` | Copy recipe fields into this entry on normalize |

### Shared sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `instrument` | `InstrumentReference` | Instrument used |
| `atmosphere` | `Atmosphere` | Processing atmosphere |
| `substrate` | `INLSubstrateReference` | Substrate used |
| `recipe` | `WetDepositionRecipeReference` | Recipe to apply |
| `thin_film_stack` | `INLThinFilmStackReference` | Resulting stack (auto or manual) |
| `solution` | `PrecursorSolution` (repeats) | Precursor solutions |
| `annealing` | `Annealing` | Post-deposition anneal |
| `quenching` | `Quenching` | Post-deposition quench |

### Auto-creation of film/stack entries

When `creates_new_thin_film` is `True`, normalization:

1. Creates an `INLThinFilm` YAML entry in the upload
2. Creates an `INLThinFilmStack` YAML entry linking the film and substrate
3. Sets `thin_film_stack` to reference the new stack
4. Resets `creates_new_thin_film` to `False`

If `thin_film_stack` already points to an entry the step is skipped.

---

## INLSpinCoating

**Inherits:** `INLThinFilmDeposition`  
**Method label:** `Spin Coating`  
**Ontology:** [CHMO:0001472](http://purl.obolibrary.org/obo/CHMO_0001472)

| Sub-section | Type | Description |
|-------------|------|-------------|
| `recipe_steps` | `SpinCoatingRecipeSteps` (repeats) | Speed, acceleration, and time for each stage |

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
| `stirring_speed` | `float` | rpm | Stirring speed during deposition |
