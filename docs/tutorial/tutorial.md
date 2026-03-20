# Tutorial

This tutorial guides you through a complete thin-film experiment using the
`nomad-inl-base` plugin: creating shared entity entries, running a spin-coating
deposition, and recording an XRD measurement – all linked together.

## Prerequisites

- A running NOMAD Oasis with this plugin installed (see
  [Install this plugin](../how_to/install_this_plugin.md))
- An upload created in NOMAD where you can add new entries

---

## Step 1 – Create a Substrate entry

The substrate is a **shared entity** that is referenced by the deposition
and characterization entries, so create it first.

1. In your upload, click **Create new entry**.
2. Select **INL Substrate** from the *INL Entities* category.
3. Fill in:
   - **Name** – e.g. `SLG-01`
   - **Material** – `SLG` (soda-lime glass, the default)
   - **Geometry** – leave empty to auto-fill 25 × 25 × 1 mm on first save.
4. Click **Save** (or trigger normalization). The geometry is auto-populated.

---

## Step 2 – Run a spin-coating deposition

1. Create a new entry and select **INL Spin Coating**.
2. Fill in:
   - **Name** – e.g. `SC-001`
   - **Operator** – your name
   - **Substrate** – click the reference field and select `SLG-01`
   - **Solution** – add a `PrecursorSolution` sub-section with solvent and solute
   - **Recipe steps** – add one or more `SpinCoatingRecipeSteps` (speed, time, acceleration)
   - **Annealing** – optionally add temperature and duration
3. Tick **Creates new thin film** and save.

!!! tip
    When **Creates new thin film** is `True`, normalization automatically creates
    - an `INLThinFilm` entry (named `SC-001_thin_film`)
    - an `INLThinFilmStack` entry (named `SC-001_thin_film_stack`) that links
      the film and the substrate together

    The **Thin film stack** reference in the spin-coating entry is set to point
    to the newly created stack.

4. After normalization you should see the three linked entries:
   `SC-001`, `SC-001_thin_film`, and `SC-001_thin_film_stack`.

---

## Step 3 – Record an XRD measurement

1. Upload your diffractogram file (`.xrdml`, `.rasx`, `.brml`, or `.raw`).
2. NOMAD automatically recognises the format and creates an `INLXRayDiffraction`
   entry (via the registered parser).
3. Open the entry and fill in:
   - **Operator** – your name
   - **Samples** – click **Add** and select `SC-001_thin_film_stack` as the
     sample reference.
4. Save. The XRD entry is now linked to the exact thin-film stack you measured.

---

## Step 4 – Explore the data

- Navigate to the `INLThinFilmStack` entry to see all layers and the substrate.
- Use NOMAD's **Graph** view to see the full provenance chain:
  *Substrate → ThinFilm → ThinFilmStack → SpinCoating → XRD*
- Search by material name or lab ID across all linked entries.

---

## Next steps

- [How to use recipes](../how_to/use_this_plugin.md#using-recipes) to stamp
  standard conditions onto new deposition entries
- [STAR sputtering guide](../how_to/use_this_plugin.md#star-sputtering) for
  PVD experiments
- [Reference – Wet Deposition](../reference/wet_deposition.md) for all
  available quantities on each deposition schema
