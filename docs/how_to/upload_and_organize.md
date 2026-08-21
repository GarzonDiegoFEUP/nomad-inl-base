# How-to – Upload data and organize entries

This guide covers the most common questions when uploading experimental data and creating entry structures in NOMAD:
what to upload first, which entries NOMAD creates automatically, how to organize files in an upload, and how to fix
common linking issues.

---

## What is an "upload"?

An **upload** is a container in NOMAD that holds one or more entries (experiments, measurements, entities).
You can think of it as a logical "batch" of related work:

- **One experiment** – e.g., all steps of a CIGSe device fabrication (substrate, Mo, In, CuGa+Se, CdS, contacts)
- **One measurement session** – e.g., all XRD patterns measured on a single day
- **One project** – e.g., all data from a 3-month study of a new deposition recipe

Each upload has a unique ID in NOMAD. Entries within the same upload can reference each other directly.

---

## Uploading strategy

### Option A – One upload per experiment / device

**Best for:** small lab groups, focused projects, or a single device run

1. Create one upload in NOMAD
2. Add all entries for that device: substrate, deposition(s), characterization
3. Link measurements to samples using references
4. Publish or close the upload when complete

**Pros:**
- Clear separation of experiments
- Easy to find all data for one device together
- Minimal cross-upload linking needed

**Cons:**
- Many uploads if you run many small experiments

---

### Option B – One upload per month / project

**Best for:** high-throughput labs, shared data repositories

1. Create one upload per month (or project)
2. Add all entries for that period: all substrates, depositions, measurements
3. Use references freely within the upload
4. Periodically publish and archive

**Pros:**
- Fewer, larger uploads
- Good for shared lab data organization

**Cons:**
- May need to manually organize entries by sample within the upload
- Cross-upload references (if needed) are more complex

---

## Creating entries manually vs. automatic parser creation

### Manual entry types

These entry types you **always create manually** by clicking **Create new entry** in NOMAD:

- `INLSubstrate` – shared entity, created once per physical substrate
- `INLSpinCoating`, `StarRFSputtering`, `METEORDeposition`, etc. – deposition processes
- `INLChemicalBathDeposition`, `INLWetDepositionRecipe`, `StarSputteringRecipe` – recipes and processes
- `SputteringTarget`, `SeleniumCell` – equipment entities
- Manual measurement entries (if you do not upload an instrument file)

---

### Automatic parser-created entries

Upload an instrument file and NOMAD **auto-creates** these entries if you have the parser installed:

| Upload this | NOMAD creates | You then fill |
|-------------|--------------|---------------|
| `.asc` file | `INLUVVisTransmission` | Operator, Samples reference |
| `.xrdml`, `.rasx`, `.brml`, `.raw` | `INLXRayDiffraction` | Operator, Samples reference |
| `*mVs.xlsx` (CV data) | `PotentiostatMeasurement` | Operator, Samples reference, Area electrode |
| `*ED.xlsx` (CA data) | `ChronoamperometryMeasurement` | Operator, Samples reference, Area electrode |
| `*.txt` (EQE) | `INLEQE` | Operator, Samples reference |
| `*Results Table*.txt` (IV) | `INLSolarCellIV` | Operator, Samples reference |
| `*.tif` (SEM images) | `INLSEMSession` | Operator, Labels, Samples reference |
| `.xls` / `.xlsx` (4-point probe) | `INLFourPointProbe` | Operator, Samples reference |
| `.nbl` (METEOR log) | `METEORDeposition` | Operator, Mask, Pockets (materials), Samples reference |

---

### Auto-created thin-film entries

When you tick **Creates new thin film** on a deposition entry and save:

- `<deposition_name>_thin_film` – the deposited layer (auto-created)
- `<deposition_name>_thin_film_stack` – the substrate + layer(s) stack (auto-created)

These appear in your upload's entry list after normalization completes.

---

## Organizing files in an upload

### Upload file structure (best practice)

```
my_experiment_upload/
├── substrate_info.txt          (optional documentation)
├── deposition_log.csv          (if you want to attach notes)
├── sample_name.xrdml           (XRD file)
├── sample_name.asc             (UV-Vis file)
├── YYMMDD - sample.tif         (SEM images)
│   YYMMDD - sample_001.tif
│   YYMMDD - sample_002.tif
└── (other instrument files)
```

### Upload via web interface

1. Click **Upload** in NOMAD
2. Drag and drop all files, or browse to select them
3. Click **Upload** to create a new upload
4. NOMAD processes files and creates entries automatically

### Upload via Python client

```python
from nomad.client import upload_file

# Simple single-file upload
archive = upload_file('sample.xrdml')  # Creates INLXRayDiffraction entry

# Multiple files in one batch
from pathlib import Path
for file in Path('.').glob('*.xrdml'):
    upload_file(str(file))
```

---

## Linking measurements to samples

### After upload: the linking workflow

1. **Upload instrument files** (`.asc`, `.xrdml`, etc.)
2. **NOMAD creates measurement entries** (e.g., `INLUVVisTransmission`, `INLXRayDiffraction`)
3. **You manually add references** by opening each measurement entry and setting:
   - **Operator** – your name
   - **Samples** – click the reference field and select your thin-film stack
4. **Save** – the measurement is now linked to the sample graph

### Finding the right sample to reference

When you open a measurement entry and click the **Samples** field, you see a list of available entries.
To find your sample:

1. Look for entries named `<deposition_name>_thin_film_stack` (these are stacks, the right choice)
2. Or search by substrate name, material, or operator
3. Select the entry and click **Save**

!!! tip
    If you have many samples, use the search box in the reference picker to filter by name, material, or date.

### If you uploaded the measurement but the sample entry does not exist yet

**Scenario:** You uploaded an XRD file, and now you need to link it to a sample, but the sample entry is not yet created.

**Solution:**

1. Create the sample entry first (click **Create new entry** → `INLSubstrate`, then the deposition)
2. Tick **Creates new thin film** on the deposition and save
3. Once the stack entry is created, go back to the measurement entry
4. Set the **Samples** reference to the newly created stack
5. Save

---

## Troubleshooting

### Parser did not create an entry

**Issue:** I uploaded a `.xrdml` file but no `INLXRayDiffraction` entry was created.

**Possible causes:**
- The parser is not installed or enabled in your NOMAD instance
- The file format is not standard (e.g., corrupted file, different file extension, vendor-specific variant)
- The file is a non-XRD measurement (check the file contents)

**Solution:**
1. Check the upload's **Errors** or **Parser Issues** tab for diagnostic messages
2. Verify the file format by opening it in a text editor (if text) or with your instrument's software
3. Try uploading a sample file from a known working measurement to test
4. Contact your NOMAD administrators if the parser registration is missing

---

### I want to re-name an entry

**Issue:** The parser created an entry with a bad name (e.g., `export_001`), and I want to rename it to `sample_XRD`.

**Solution:**
1. Open the entry in the ELN
2. Edit the **Name** field and click **Save**
3. The graph and all references update automatically

---

### I need to move an entry from one upload to another

**Issue:** I accidentally created an entry in the wrong upload.

**Current limitation:** NOMAD does not yet support moving entries between uploads. 

**Workaround:**
1. Export or note the entry data
2. Create a new entry in the correct upload and re-fill the data
3. Update any references to point to the new location
4. Archive or delete the old entry if it is in the wrong upload

(This is a known workflow gap; future NOMAD versions may improve this.)

---

### I linked the wrong sample to a measurement

**Issue:** I set the **Samples** reference on an XRD entry to the wrong thin-film stack.

**Solution:**
1. Open the measurement entry
2. Click the **Samples** field
3. Remove the old reference (click the **X** button)
4. Add the correct sample reference
5. Click **Save**

The graph and all analysis entries update automatically.

---

### A thin-film stack was not auto-created

**Issue:** I ticked **Creates new thin film** on a deposition, but the stack entry never appeared.

**Possible causes:**
- The deposition entry has neither a **Substrate** reference nor a **Sample** reference
- Normalization did not complete (check the entry status)
- The toggle reset to `False` after the first application (expected behavior)

**Solution:**
1. Verify the deposition entry has a **Substrate** reference (or existing **Sample** reference)
2. Save the entry and wait for normalization to complete (usually <1 min)
3. Refresh your browser and check the upload's **Entries** list for entries named `<deposition_name>_thin_film` and `<deposition_name>_thin_film_stack`
4. If still missing, check the entry's **Normalization** tab for error messages

---

## Best practices

1. **Create shared entities first** – substrate, targets, cells – before depositions
2. **Use `Creates new thin film` on every deposition** – this ensures each layer is tracked
3. **Upload characterization files in one batch** – NOMAD processes and groups related measurements automatically
4. **Name entries clearly** – include date, sample ID, and process type (e.g., `SLG-UV-001`, `STAR-Mo-2026-08-21`)
5. **Link measurements immediately after upload** – do not wait; this keeps your graph accurate as you work
6. **Use recipes for repeated processes** – save time and ensure consistency
7. **Search by operator, material, or date** – keep your upload organized and searchable

---

## Next steps

- [How to use recipes](use_this_plugin.md#using-recipes)
- [Reference – Wet Deposition](../reference/wet_deposition.md)
- [Reference – Characterization](../reference/characterization.md) – full list of supported file formats
