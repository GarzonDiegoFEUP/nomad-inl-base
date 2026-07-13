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
| `INLSprayPyrolysisRecipe` | `WetDepositionRecipe` | `properties: SprayPyrolysisProperties` (hides `steps`) |
| `INLDipCoatingRecipe` | `WetDepositionRecipe` | `properties: DipCoatingProperties` |
| `INLChemicalBathDepositionRecipe` | `WetDepositionRecipe` | `bath_composition`, `bath_temperature`, `duration`, `ph`, `stirring_speed`, `deposited_material` — see [CBD types](#cbd-types) below |

### CBD types

`INLChemicalBathDepositionRecipe` supports two preparation workflows:

**Type 1 – In-situ preparation**
Use the `steps` list with `INLCBDBathPreparationStep` entries.
Each step can carry `reagents` (list of `INLCBDReagent`) describing what is
added to the bath at that stage.

**Type 2 – Pre-mixed solutions**
Use the `bath_composition` list with `INLCBDComponentMixture` entries.
Each component references a pre-made `Solution` entry and specifies the volume
added to the bath.  
Optionally, embed a `solution_template` inside each component so that
`Solution` entries can be auto-created at deposition time (see
[`INLChemicalBathDeposition`](#inlchemicalbathdeposition)).

#### INLCBDComponentMixture

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Display name (e.g. "CdCl₂ solution") |
| `solution` | `NMPSolution` ref | Pre-made `Solution` entry |
| `volume` | `float` (ml) | Volume added to the bath |
| `order` | `int` | Order of addition |
| `notes` | `str` | Mixing conditions, notes |
| `solution_template` | `INLCBDSolutionTemplate` | Inline template for auto-creating the solution entry |

#### INLCBDSolutionTemplate

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Name for the `Solution` entry that will be created |
| `solvent` | `str` | Solvent name used for PubChem lookup (defaults to `water`) |
| `total_volume` | `float` (ml) | Total prepared volume |
| `reagents` | `INLCBDReagent` (repeats) | Solutes dissolved in the solution |

#### INLCBDReagent

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | **PubChem lookup name** (e.g. `"cadmium acetate"`, `"thiourea"`) — used to retrieve molecular weight and calculate molar concentration |
| `mass` | `float` (g) | Mass of solid reagent |
| `volume` | `float` (ml) | Volume of liquid reagent |

#### INLCBDBathPreparationStep

Extends `INLWetDepositionStep` with a `reagents` sub-section (`INLCBDReagent`, repeats).
Used in Type 1 recipes to document step-by-step in-situ bath preparation.

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
| `create_solutions` | `bool` | – | Trigger auto-creation of `Solution` entries from `bath_composition` templates (resets to `False` after one run) |
| `ammonium_hydroxide_solution` | `NMPSolution` ref | – | Stock NH₄OH `Solution` entry — any template reagent whose name contains `"nh4oh"`, `"ammonium"`, or `"ammonia"` is linked to this via `SolutionComponentReference` instead of a plain component |

**Sub-sections:**

| Sub-section | Type | Description |
|-------------|------|-------------|
| `bath_composition` | `INLCBDComponentMixture` (repeats) | Bath components for Type 2 (pre-mixed) CBD |
| `recipe` | `INLChemicalBathDepositionRecipeReference` | CBD recipe to apply |

### Auto-creation of Solution entries (Type 2)

When `create_solutions` is set to `True` on an `INLChemicalBathDeposition` entry:

1. For each `bath_composition` component that has a `solution_template` but no
   `solution` reference, a new `nomad-material-processing` `Solution` entry is
   created in the same upload.
2. Each reagent in the template becomes a `SolutionComponent` with
   `component_role = "Solute"`, `mass` (g→kg), optional `volume` (ml→L), and
   `substance_name` set to the reagent name for PubChem lookup.
3. If `ammonium_hydroxide_solution` is set, reagents matching `"nh4oh"` /
   `"ammonium"` / `"ammonia"` become a `SolutionComponentReference` pointing to
   the stock solution, with the template volume applied.
4. A `SolutionComponent` with `component_role = "Solvent"` is added using the
   template `solvent` field (defaults to `"water"`); its volume is set to
   `total_volume`.
5. After creation, `component.solution` is wired to the new entry's reference.
6. `create_solutions` resets to `False`.

Molar concentrations are calculated automatically by NOMAD's
`Solution.normalize()` once the `Solution` entries are processed (requires a
valid PubChem substance name on each reagent).
