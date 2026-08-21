# Tutorial – Material Characterization Workflow

This tutorial guides you through a typical materials characterization experiment:
**substrate preparation → thin-film deposition → structural and optical characterization**.

We use SLG (soda-lime glass) as the substrate, deposit a material (e.g., via sputtering),
and then characterize it with UV-Vis, XRD, and SEM.

## Prerequisites

- A running NOMAD Oasis with the `nomad-inl-base` plugin installed
  (see [Install this plugin](../how_to/install_this_plugin.md))
- An upload in NOMAD where you can add and edit entries
- Sample files from your characterization instruments (`.asc` for UV-Vis,
  `.xrdml` / `.rasx` / `.brml` / `.raw` for XRD, `.tif` for SEM images)

---

## Lab workflow → NOMAD mapping

| Lab step | NOMAD entry type | Created | Recipe? | Notes |
|----------|------------------|---------|---------|-------|
| Clean substrate | `INLSubstrate` | Manually | – | Create once, reference multiple times |
| Deposit material | `INLSpinCoating` *or* `StarRFSputtering` *or* other deposition | Manually | Optional | Use **Creates new thin film** toggle |
| UV-Vis measurement | `INLUVVisTransmission` | Parser (upload `.asc`) | – | Auto-parsed, set operator + samples ref |
| XRD measurement | `INLXRayDiffraction` | Parser (upload `.xrdml`/`.rasx`/etc.) | – | Auto-parsed, set operator + samples ref |
| SEM images | `INLSEMSession` | Parser (upload `.tif` images) | – | Auto-grouped, set labels on images |

---

## Step 1 – Create the substrate entry

1. In your upload, click **Create new entry**.
2. Select **INL Substrate** (in the *INL Entities* category).
3. Fill in:
   - **Name** – e.g. `SLG-MS-001` (MS = Material Scientist, or your lab ID)
   - **Material** – `SLG` (default)
   - **Geometry** – leave empty; a 25 × 25 × 1 mm rectangle will auto-fill
4. Click **Save**. The geometry auto-populates on normalization.

!!! tip
    The substrate is a **shared entity**. Create it once, then reference it from
    every deposition and characterization entry that uses it. This keeps your
    data graph clean and searchable.

---

## Step 2 – Record the deposition

The exact entry type depends on your deposition method. Here are common examples:

### Option A – Spin coating (e.g., for perovskites, organic semiconductors)

1. Create a new entry → **INL Spin Coating** (in *INL Wet Deposition*).
2. Fill in:
   - **Name** – e.g. `SC-MS-001`
   - **Operator** – your name
   - **Substrate** – reference `SLG-MS-001` from Step 1
   - **Solution** – add `PrecursorSolution` sub-section(s) with solvent and solute
   - **Steps** – add `SpinCoatingStep` (speed, duration, acceleration) and optional
     annealing step
3. Tick **Creates new thin film** and save.

After normalization, you will have created two new entries:
- `SC-MS-001_thin_film` – the deposited layer
- `SC-MS-001_thin_film_stack` – the substrate + film stack

### Option B – STAR RF/DC sputtering (e.g., for metal/oxide layers)

1. Create a new entry → **STAR RF Sputtering** or **STAR DC Sputtering**.
2. Fill in:
   - **Name** – e.g. `STAR-MS-001`
   - **Operator** – your name
   - **Base pressure** – chamber base pressure (mbar)
   - **Samples** – select `SLG-MS-001`
3. Add **Steps**:
   - Add one or more sputtering step(s) with power, duration, and gas flow
   - Set **Substrate set temperature** and **Rotation** if applicable
4. Add **Sources** – one per magnetron gun; reference the target material
5. Tick **Creates new thin film** on the step and save.

After normalization, the same auto-creation occurs: new film + stack entries.

### Option C – METEOR e-beam evaporation (e.g., for gold contacts, metal seed layers)

1. Create a new entry → **METEOR E-Beam Evaporation**.
2. Fill in:
   - **Name** – e.g. `METEOR-MS-001`
   - **Operator** – your name
   - **Substrate** – `SLG-MS-001`
   - **Mask** – description of any shadow mask used
3. **Pockets** – Set the **Material** field for each pocket that was active.
4. **QCM** – The `.nbl` parser will fill `thickness` from the log file.
   If you have an independent thickness measurement, set **Thickness override**.
5. Tick **Creates new thin film** and save.

---

## Step 3 – Upload and link characterization files

### UV-Vis transmission

1. Upload your `.asc` file from the UV-Vis instrument.
2. NOMAD auto-detects the format and creates an `INLUVVisTransmission` entry.
3. Open the entry and:
   - Set **Operator** to your name
   - Add a **Samples** reference pointing to the `<deposition_name>_thin_film_stack`
     entry from Step 2
4. Save. The measurement is now linked to your sample.

!!! info
    If the `.asc` file parsing fails or creates no entry, check the file format
    matches the expected columns. See [Characterization Reference](../reference/characterization.md)
    for supported formats.

### XRD diffractogram

1. Upload your XRD file (`.xrdml`, `.rasx`, `.brml`, or `.raw`).
2. NOMAD creates an `INLXRayDiffraction` entry automatically.
3. Open the entry and:
   - Set **Operator**
   - Add a **Samples** reference to the thin-film stack
4. Save. NOMAD's graph view will now show: *Substrate → ThinFilm → Stack → Deposition → XRD*.

### SEM images

1. Upload all your SEM `.tif` files in one batch.
   - If your filenames follow the FEI pattern `YYMMDD - <name>.tif` and related images
     (`YYMMDD - <name>_001.tif`, `_002.tif`, …), the parser groups them automatically
     into one `INLSEMSession` entry.
   - Otherwise, upload any `.tif` files and the parser creates an entry per image or
     session depending on metadata.
2. Open the `INLSEMSession` entry and:
   - Set **Operator**
   - Add a **Samples** reference
   - (Optional) Set **Label** on individual `INLSEMImage` sub-sections to annotate
     regions of interest
3. Save.

---

## Step 4 – Inspect the provenance graph

Once all entries are saved and linked, use NOMAD's **Graph** view to see the full chain:

```
Substrate (SLG-MS-001)
    ↓
Deposition (SC-MS-001 or STAR-MS-001 or METEOR-MS-001)
    ↓
Thin Film (auto-created)
    ↓
Thin Film Stack (auto-created)
    ↓
Characterization measurements (UV-Vis, XRD, SEM)
```

Verify that:
- All characterization entries have a **Samples** reference pointing to the stack
- The stack lists the substrate and deposited layer(s)
- The deposition entry shows the operator, conditions, and substrate reference

---

## Troubleshooting

### Parser did not recognize my file

**Issue:** I uploaded a `.asc` or `.xrdml` file but no entry was created.

**Solution:**
1. Verify the file format matches the expected standard for your instrument.
2. Check the upload's **Parser Issues** or **Errors** tab for diagnostic messages.
3. If the file is in a vendor-specific format not yet supported, ask your plugin maintainers to extend the parsers.

### I linked the wrong sample reference

**Issue:** I set the **Samples** reference on a measurement to the wrong thin-film stack.

**Solution:**
1. Open the measurement entry.
2. Edit the **Samples** field to remove the old reference.
3. Add the correct stack reference.
4. Save and re-normalize if needed.

### The thin-film stack was not auto-created

**Issue:** I ticked **Creates new thin film** but no stack entry appeared.

**Solution:**
1. Verify that you set either a **Substrate** reference (to create a new stack)
   or a **Sample** reference (to append a layer to an existing stack).
2. Save the deposition entry and wait for normalization to complete.
3. Check the upload's **Entries** list for entries named `<deposition_name>_thin_film`
   and `<deposition_name>_thin_film_stack`.

---

## Next steps

- [How to use recipes](../how_to/use_this_plugin.md#using-recipes) to standardize
  your deposition conditions
- [Reference – Wet Deposition](../reference/wet_deposition.md) for all spin-coating options
- [Reference – STAR Sputtering](../reference/sputtering.md) for PVD details
- [Reference – METEOR E-Beam](../reference/meteor.md) for e-beam evaporation
- [Reference – Characterization](../reference/characterization.md) for all supported
  measurement types and file formats
