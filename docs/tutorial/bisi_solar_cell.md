# Tutorial – Full BiSI Solar Cell Workflow

This tutorial guides you through fabricating a complete **BiSI (Bismuth Iodide) perovskite photovoltaic device**.
Unlike the CIGSe workflow which combines PVD and chemistry, the BiSI workflow uses **spin coating** for most layers,
ending with a metal contact deposited by **e-beam evaporation**.

This example demonstrates how wet-chemistry and PVD techniques can be combined for perovskite and halide devices.

## Prerequisites

- A running NOMAD Oasis with the `nomad-inl-base` plugin installed
- An upload where you can create and link entries
- Familiarity with the [onboarding tutorial](tutorial.md) for basic upload and linking concepts
- (Optional) characterization files for XRD or other post-device measurements

---

## Lab workflow overview

| Lab step | NOMAD entry type | Created | Recipe? |
|----------|------------------|---------|---------|
| Clean FTO substrate | `INLSubstrate` | Manually | – |
| Deposit SnO₂ (spin coat) | `INLSpinCoating` | Manually | ✓ |
| Deposit BiSI (spin coat) | `INLSpinCoating` | Manually | ✓ |
| Deposit PTAA (spin coat) | `INLSpinCoating` | Manually | ✓ |
| Deposit Au (e-beam) | `METEORDeposition` | Manually | – |
| (Optional) XRD measurement | `INLXRayDiffraction` | Parser (`.xrdml` etc.) | – |

---

## Step 1 – Substrate

### Create the FTO substrate

1. Create **INL Substrate** entry:
   - **Name** – e.g. `FTO-BiSI-001`
   - **Material** – `FTO` (Fluorine-doped tin oxide) or leave as a free text field
   - **Geometry** – leave empty (auto-fills to 25 × 25 × 1 mm)
2. Optionally set **Lab ID** for easy cross-referencing in later searches.
3. Save.

!!! info
    If your substrates are pre-cleaned and stored, you can create the substrate
    entry weeks before the deposition run. It is a persistent entity that you
    reference from each deposition and measurement.

---

## Step 2 – Electron transport layer (SnO₂ spin coating)

1. Create **INL Spin Coating** entry:
   - **Name** – e.g. `SnO2-BiSI-001`
   - **Operator** – your name
   - **Substrate** – reference `FTO-BiSI-001`
   
2. **Solution** – add a `PrecursorSolution` sub-section:
   - **Solvent** – e.g. `2-Methoxyethanol`
   - **Solute** – e.g. `SnCl₄·5H₂O` or similar precursor
   - (Optional) **Concentration** and **Volume** if tracked
   
3. **Steps** – add spin-coating recipe steps:
   - **Spin Coating Step** #1: speed (rpm), duration (s), acceleration (rpm/s)
   - (Optional) **Hotplate Annealing Step**: temperature (°C), duration (min)
   - (Optional) **Hotplate Annealing Step** #2: different temperature if multi-step anneal
   
4. Tick **Creates new thin film** and save.

!!! tip
    Create a **Spin Coating Recipe** entry with the SnO₂ precursor, solvent,
    and spin/anneal parameters. Then on future BiSI runs, reference the recipe
    and tick **Apply recipe** to auto-fill these fields.

After normalization:
- `SnO2-BiSI-001_thin_film` (SnO₂ layer)
- `SnO2-BiSI-001_thin_film_stack` (FTO + SnO₂)

---

## Step 3 – Absorber layer (BiSI spin coating)

1. Create **INL Spin Coating** entry:
   - **Name** – e.g. `BiSI-BiSI-001`
   - **Operator** – your name
   - **Substrate** – reference `SnO2-BiSI-001_thin_film_stack` from Step 2
   
2. **Solution** – add a `PrecursorSolution` sub-section:
   - **Solvent** – e.g. `DMSO`, `DMF`, or mixed solvent
   - **Solute** – e.g. `BiI₃` or other BiSI precursor mix
   - (Optional) **Concentration** and **Volume**
   
3. **Steps** – add spin-coating steps with your deposition recipe:
   - **Spin Coating Step**: speed, duration, acceleration
   - (Optional) **Antisolvent Quenching Step**: volume (ml), dispensing speed (ml/s)
     if you use an antisolvent for crystallization
   - **Hotplate Annealing Step**: temperature, duration (typically to crystallize the perovskite)
   
4. Tick **Creates new thin film** and save.

After normalization:
- `BiSI-BiSI-001_thin_film`
- `BiSI-BiSI-001_thin_film_stack` (FTO + SnO₂ + BiSI)

---

## Step 4 – Hole transport layer (PTAA spin coating)

1. Create **INL Spin Coating** entry:
   - **Name** – e.g. `PTAA-BiSI-001`
   - **Operator** – your name
   - **Substrate** – reference `BiSI-BiSI-001_thin_film_stack` from Step 3
   
2. **Solution** – add a `PrecursorSolution` sub-section:
   - **Solvent** – e.g. `Chlorobenzene`
   - **Solute** – `PTAA` (Poly(triaryl amine)) or similar hole transporter
   - (Optional) **Additives** if tracked as a separate solute
   
3. **Steps** – add spin-coating steps (typically simpler than absorber):
   - **Spin Coating Step**: speed (rpm), duration (s), acceleration (rpm/s)
   - (Optional) **Hotplate Annealing Step** at moderate temperature if needed
   
4. Tick **Creates new thin film** and save.

After normalization:
- `PTAA-BiSI-001_thin_film`
- `PTAA-BiSI-001_thin_film_stack` (FTO + SnO₂ + BiSI + PTAA)

---

## Step 5 – Metal contact (Au by METEOR e-beam)

The final step is a metal contact, typically gold, deposited by **e-beam evaporation**.

1. Create **METEOR E-Beam Evaporation** entry:
   - **Name** – e.g. `Au-BiSI-001`
   - **Operator** – your name
   - **Substrate** – reference `PTAA-BiSI-001_thin_film_stack` from Step 4
   - **Mask** – describe your contact mask (e.g., "4 pixels of 0.5 × 0.5 cm each")
   
2. **Pockets** – set the **Material** field to `Gold` (or `Au`) on the active pocket
   
3. **QCM** – The `.nbl` parser will auto-fill **Thickness** from the log file.
   Optionally set **Thickness override** if you have an independent measurement.
   
4. Tick **Creates new thin film** and save.

After normalization:
- `Au-BiSI-001_thin_film`
- `Au-BiSI-001_thin_film_stack` (final complete device: FTO + SnO₂ + BiSI + PTAA + Au)

---

## Step 6 – Characterization (optional)

If you perform structural or optical characterization on the final device:

### XRD measurement

1. Upload your XRD diffractogram (`.xrdml`, `.rasx`, `.brml`, or `.raw`).
2. NOMAD creates an `INLXRayDiffraction` entry automatically.
3. Open the entry and set:
   - **Operator**
   - **Samples** → reference `Au-BiSI-001_thin_film_stack` (the final device)
4. Save. The XRD pattern is stored and linked to the device.

### Additional characterization

If you perform UV-Vis, SEM, or other measurements on intermediate or final samples,
follow the same pattern: upload the file, NOMAD creates an entry, then link it to
the appropriate thin-film stack.

---

## Step 7 – Inspect the provenance graph

Use NOMAD's **Graph** view to verify the complete chain:

```
FTO Substrate
    ↓
SnO₂ (electron transport)
    ↓
BiSI (absorber)
    ↓
PTAA (hole transport)
    ↓
Au (metal contact)
    ↓
(Optional) XRD and other characterization
```

Verify that:
- Each spin-coating layer references the previous stack
- The gold contact references the complete device stack
- Any characterization entries link to the final stack
- Operators and timestamps are filled

---

## Recipe reuse

Spin-coating workflows are ideal for recipes because the same solvent + precursor
combinations often repeat across many samples.

1. Create a **Spin Coating Recipe** for SnO₂:
   - Solvent, precursor, spin parameters, anneal profile
2. Create a **Spin Coating Recipe** for BiSI:
   - Solvent, precursor mix, spin, quench (if used), anneal profile
3. Create a **Spin Coating Recipe** for PTAA:
   - Solvent, polymer, spin, optional anneal

On the next device run, reference each recipe and tick **Apply recipe**. This
ensures consistency across batches and reduces data-entry time.

---

## Common questions

### Q: Can I deposit multiple pixels on the same substrate in one METEOR run?

**A:** Yes. The METEOR deposition applies to the entire substrate. If your mask
defines multiple contact pixels, the gold evaporates across all pixels in one run.
The **Mask** field describes the contact geometry. If you later want to measure
individual pixels separately, you can create multiple **INLSEMSession** or
characterization entries that each reference a region of the substrate.

### Q: What if the spin-coating step fails and I need to re-deposit a layer?

**A:** Create a new **INL Spin Coating** entry with the same name (or a variant
like `BiSI-BiSI-001-retry`). Reference the previous stack (e.g., `SnO2-BiSI-001_thin_film_stack`).
NOMAD will track this as a new deposition event in the provenance graph, and the
previous failed attempt remains in the upload history for reference.

### Q: Should I create separate substrate entries for each device, or reuse one?

**A:** That depends on your lab's conventions:
- **Reuse one substrate entry** if you deposit multiple BiSI devices on the same
  FTO piece and want to track them together.
- **Create separate substrate entries** if each FTO piece is distinct or if you
  want to isolate experiments by physical sample.

Choose the approach that best reflects your lab's workflow.

---

## Next steps

- [How to use recipes](../how_to/use_this_plugin.md#using-recipes)
- [Reference – Wet Deposition](../reference/wet_deposition.md) for all spin-coating options
- [Reference – METEOR E-Beam](../reference/meteor.md) for e-beam evaporation specifics
- [Reference – Characterization](../reference/characterization.md) for measurement file formats
