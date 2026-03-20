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

1. Create a new entry → **INL Cyclic Voltammetry** (`PotentiostatMeasurement`).
2. Add **Current**, **Voltage**, and **Scan** time-series sub-sections with
   your measured data.
3. Set **Area electrode** if you want the plot to show current density
   instead of raw current.
4. After normalization, a CV curve is displayed (scan 3 by default, scan 2 as
   fallback).

### Chronoamperometry

1. Create a new entry → **INL Chronoamperometry** (`ChronoamperometryMeasurement`).
2. Set **Voltage applied** and add a **Current** time-series sub-section.
3. Set **Area electrode** to normalize the curve to current density.
4. The normalized entry displays a current (density) vs. time plot.
