# Explanation

This page explains the key concepts and design decisions behind the
`nomad-inl-base` plugin.

---

## Entity / Activity model

NOMAD organizes scientific data around two complementary concepts:

- **Entities** are physical objects that persist over time and can be referenced
  by multiple activities.  Examples: a substrate, a thin film, a sputtering
  target.
- **Activities** are processes or measurements that consume or produce entities.
  Examples: a spin-coating run, a sputtering experiment, an XRD measurement.

All INL schemas follow this model. Entity entries (under the *INL Entities*
category) are created once and referenced throughout the experiment lifecycle.
Activity entries record what was done and point to the involved entities.

---

## The thin-film chain

A complete thin-film sample in NOMAD is represented by a chain of three linked
entries:

```
INLSubstrate  ──► INLThinFilmStack ◄──  INLThinFilm  (one per layer)
```

`INLThinFilmStack` holds:

- A **substrate** reference (via `INLSubstrateReference`)
- One or more **layer** references (via `INLThinFilmReference`)
- A `components` list built automatically during normalization containing
  `SystemComponent` objects pointing to the actual entries

Normalization also propagates substrate geometry (width, length) to every
layer, keeping the stack self-consistent.

All deposition methods and characterization schemas reference the
`INLThinFilmStack` as the sample object, ensuring full provenance traceability
from raw substrate to final measurement.

### Why separate entries?

Storing each object as its own NOMAD entry means:

- The same substrate can be referenced by many depositions without duplication
- Measurements can be linked directly to the specific stack measured
- NOMAD's graph and search features can traverse the full chain

---

## Auto-creation of film/stack entries

When **Creates new thin film** is set to `True` on a deposition entry,
normalization:

1. Creates an `INLThinFilm` YAML entry in the upload
2. Creates an `INLThinFilmStack` YAML entry linking the film and substrate
3. Sets the deposition entry's `thin_film_stack` reference to the new stack
4. Resets the toggle to `False` so the action is not repeated

If a stack reference already exists, the step is skipped, so re-normalizing
a saved entry is safe.

---

## Recipe system

Both deposition families (wet deposition and STAR sputtering) support
**reusable recipe entries**.

### WetDepositionRecipe

A `WetDepositionRecipe` entry stores template values for instrument,
atmosphere, substrate, solutions, annealing, and quenching. When
**Apply recipe** is triggered on a deposition entry, each template field
is copied into the deposition *only if that field is currently empty*.
This non-destructive merge means a recipe can be partially overridden per
experiment without modifying the recipe itself.

### StarSputteringRecipe

A `StarSputteringRecipe` stores a sequence of `StarStep` objects (pre-sputtering,
stabilization, sputtering). When applied, the recipe's steps are appended to
the experiment's step list.

---

## Target inventory and calibration tracking

The `SputteringTarget` entry acts as a persistent logbook for a physical
magnetron target. Each time a `StarSputtering` experiment that references
the target is normalized, the target's deposition records list gains a new
`TargetDepositionRecord` entry with:

- The experiment reference
- The source slot index
- The total deposition time (sum of all powered steps)
- The total deposition energy (sum of power × duration for all steps)

The target's normalization then recomputes:

| Quantity | Description |
|----------|-------------|
| `total_deposition_time` | Sum across all records |
| `total_deposition_energy` | Sum across all records |
| `time_since_last_calibration` | Sum since `last_calibration_date` |
| `energy_since_last_calibration` | Sum since `last_calibration_date` |
| `needs_calibration` | `True` if either interval threshold is exceeded |

This automates target lifecycle management without requiring manual bookkeeping.

---

## Electrochemistry schemas

The cyclic voltammetry schema (`PotentiostatMeasurement`) and chronoamperometry
schema (`ChronoamperometryMeasurement`) store raw time-series data and
auto-generate Plotly figures during normalization.

Both schemas optionally accept an **area electrode** value (in m²).
When provided, the displayed y-axis quantity switches from raw current (mA)
to current density (mA cm⁻²), enabling direct comparison across different
electrode sizes.

The working electrode (`WorkingElectrode`) extends `INLThinFilmStack` so the
exact sample geometry (substrate, layer stack) used in the measurement is
always recorded.

---

## Shared entities vs. method-specific aliases

The `INLThinFilm`, `INLThinFilmStack`, and related reference classes live in
`entities.py` and are shared across all schema modules. The STAR sputtering
schema re-exports them as `StarThinFilm`, `StarStack`, etc. for backwards
compatibility with existing NOMAD archives; these names are simple aliases
and refer to exactly the same classes.
