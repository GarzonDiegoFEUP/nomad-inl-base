# Tutorial – Battery deposition workflow

This tutorial walks through a complete battery deposition workflow using INL's PC03 CathodeChamber and PC04 ElectrolyteChamber.
You'll learn how battery chamber logs are automatically parsed, how samples are automatically linked via filename convention,
how to organize and upload your data, and how to troubleshoot common issues.

---

## Battery chambers at INL

INL operates two programmable sputtering/annealing chambers dedicated to battery research:

- **PC03 Cathode Chamber** – sputtering system for cathode thin films
- **PC04 Electrolyte Chamber** – multi-function chamber for both electrolyte sputtering and substrate annealing

Both chambers log all process parameters (temperature, pressure, gas flows, source power, substrate shutter, rotation)
continuously to a CSV file. When you upload a CSV log to NOMAD, the `BatteryChamberParser` automatically creates
a corresponding `PC03CathodeChamberDeposition`, `PC04ElectrolyteChamberDeposition`, or `PC04SubstrateAnnealing` entry.

---

## What the parser automatically creates

### Upload a PC03 or PC04 CSV log

Upload any CSV file whose filename starts with `PC03_` or `PC04_` and NOMAD will create one of these entry types:

| Filename pattern | Entry type created | Triggered by |
|---|---|---|
| `PC03_All Signals_*.csv` | `PC03CathodeChamberDeposition` | File starts with `PC03` |
| `PC04_All Signals_*.csv` (sputtering active) | `PC04ElectrolyteChamberDeposition` | File starts with `PC04` + sputtering source columns present |
| `PC04_All Signals_*.csv` (annealing only) | `PC04SubstrateAnnealing` | File starts with `PC04` + only heater channels (no sputtering) |

The parser examines the CSV column headers at parse time to determine which PC04 entry type to create—no configuration needed.

**What gets automatically populated:**

- `recording_name` — from the log header
- `operator` — operator name from the log header
- `start_datetime` — experiment start time
- `substrate_type` — chamber-detected substrate identifier
- Time-series data — ~460 channels sampled at ~1 Hz: temperatures, pressures, gas flows, shutter position, rotation speed, source power, etc.
- `base_pressure` — minimum pressure during run (auto-computed)
- `deposition_time` — time with substrate shutter open (auto-computed)
- Per-source data (for PC03/PC04 deposition) — material, target, shutter history, rate, deposited thickness

---

## Automatic sample linking via filename convention

### How it works

Battery chamber CSVs must follow the filename convention to enable automatic sample linking:

```
PC0X_All Signals_[Sample Name] Date.csv
```

**Examples:**
- `PC03_All Signals_LNbO_001 2026.08.15-14.30.22.csv` → sample name `LNbO_001`
- `PC04_All Signals_LCO_Battery_02 2026.08.16-09.15.45.csv` → sample name `LCO_Battery_02`

The parser extracts the sample name (text between `_` and the date) and stores it in the entry's `sample_name` quantity.
During normalization, NOMAD automatically **searches your current upload** for a matching sample and links it.

### Matching logic

When the entry normalizes, NOMAD searches for an existing entry whose `name` matches `sample_name`:

1. **INLThinFilmStack found** (preferred) – a new thin film (for deposition) is appended as a new layer, or the stack is linked (for annealing)
2. **INLSubstrate found** – a new `INLThinFilmStack` is created referencing that substrate, with the deposited film as the first layer
3. **INLSampleFragment found** – linked as-is (note: annealing entries cannot reference fragments, a warning is logged)
4. **No match** – a brand-new `INLThinFilmStack` is created with the sample name

This means **you do not need to manually create or link samples** if you follow the filename convention—NOMAD handles it automatically.

### If filename doesn't match the convention

If the filename does not follow `PC0X_All Signals_[Name] Date.csv`:
- `sample_name` remains empty
- A new sample is still created with a generic name
- A warning is logged to help you identify the issue
- The entry parses and normalizes normally

---

## Naming your samples consistently

### Best practice

Use clear, descriptive sample names that map directly to your lab notebook:

- `LNbO_001`, `LNbO_002`, `LNbO_003` – for a series of lithium niobate samples
- `LCO_Battery_01`, `LCO_Battery_02` – for lithium cobalt oxide battery assemblies
- `TestRun_BeforeOptimization`, `TestRun_AfterOptimization` – for before/after studies

### Why it matters

- **Automatic linking** – NOMAD finds the right sample on first upload if the name matches existing samples
- **Consistency** – using the same name in lab notes, filenames, and NOMAD makes tracking experiments effortless
- **Searchability** – descriptive names make it easy to find samples later in NOMAD's search interface

---

## Uploading strategy for battery experiments

### Option A – One upload per batch run

**Best for:** high-throughput studies, comparing multiple samples in a single chamber session

1. Create one upload in NOMAD
2. Load multiple samples into the chamber (e.g., 4–6 substrate pieces with different coatings)
3. Run the batch and save one CSV log per sample or per chamber session
4. Upload all logs at once (or upload them one-by-one and link to the same upload)
5. NOMAD automatically creates one `PC03CathodeChamberDeposition` or `PC04ElectrolyteChamberDeposition` entry per log
6. Each entry is automatically linked to its corresponding sample via filename

**Pros:**
- All related experiments in one place
- Sample linking happens automatically
- Easy to track reproducibility across batch runs

**Cons:**
- Large uploads if you run many samples
- Manual organization if samples have different purposes

---

### Option B – One upload per sample

**Best for:** focused studies on individual samples, when each sample has a distinct preparation history

1. Create one upload per sample
2. Add all deposition and annealing logs for that sample to the upload
3. Create a manual `INLSubstrate` or `INLThinFilmStack` entry for the sample
4. Upload all chamber logs; automatic sample linking uses your manual substrate entry
5. Optionally add characterization measurements (XRD, SEM, electrochemistry) to the same upload

**Pros:**
- Clear separation of experiments by sample
- All data for one sample in one place
- Simple to publish or archive when complete

**Cons:**
- Many uploads if you run many samples
- Requires you to manually create the substrate entry first

---

## Best practices for organizing battery uploads

### Before uploading: prepare your filenames

1. **Extract the sample name** from your lab notebook or chamber log header
2. **Rename the CSV** to match the convention: `PC03_All Signals_YourSampleName YYYY.MM.DD-HH.MM.SS.csv`
   - Use the date/time from the log file's `Date Started` field
   - Do not omit the `_All Signals_` prefix (it's required by the parser)
3. **Verify the date format** — use `YYYY.MM.DD-HH.MM.SS` (period-separated date, hyphen-separated time)

**Example:**
```
Original: CathodeChamber_2026-08-15_LNbO_001.csv
Renamed:  PC03_All Signals_LNbO_001 2026.08.15-14.30.22.csv
          (matches convention: PC03_All Signals_[SampleName] [Date])
```

### During upload: group logically

- **Option A (batch mode):** upload all logs from one chamber session together
- **Option B (sample mode):** upload all logs for one sample together, across multiple chamber sessions if needed

Either way, make sure sample names are consistent across log files.

### After upload: verify links

1. Open each created entry (PC03/PC04 deposition or annealing)
2. Check the `sample_name` field — should match your filename
3. Check the `samples` list (deposition) or `thin_film_stack` field (annealing) — should reference the expected sample
4. If the link is missing or wrong, check that:
   - The filename was renamed correctly
   - A matching sample exists in the upload
   - The upload index has caught up (wait ~30 seconds and refresh)

---

## Manual entry creation

### When to create entries manually

**Normally, battery chamber entries are created by uploading a CSV log.** You only create them manually if:

- You do not have a CSV log (e.g., you ran the chamber before data export was enabled, or you are reconstructing historical experiments)
- You need to create a `PC03CathodeChamberDeposition` or `PC04ElectrolyteChamberDeposition` entry by hand

### Manual sample references

Both deposition and annealing entries have sample reference fields you can fill manually:

| Entry type | Sample field | Use case |
|---|---|---|
| `PC03CathodeChamberDeposition` / `PC04ElectrolyteChamberDeposition` | `samples` (repeats) | Link one or more existing samples (e.g., if automatic linking did not work, or to add additional samples) |
| `PC04SubstrateAnnealing` | `thin_film_stack` | Link a specific stack that was annealed in this run |

If you fill these fields manually, they are preserved during normalization.

---

## Troubleshooting battery chamber uploads

### Issue 1: Sample name not extracted (sample_name is empty)

**Symptom:** The entry parses successfully, but `sample_name` is empty and no sample is linked.

**Likely causes:**
1. Filename does not match `PC0X_All Signals_[Name] Date.csv`
2. The date format is wrong (e.g., uses hyphens instead of periods: `2026-08-15` instead of `2026.08.15`)
3. There is no space between the sample name and the date

**Fix:**
1. Rename the file to match the convention exactly
2. Re-upload the file
3. NOMAD will re-parse and extract the sample name
4. If the sample already exists in the upload, the link will be created automatically

**Example corrections:**
```
Wrong:  PC03_All Signals_LNbO_001.csv
        → missing date; parser cannot extract sample name

Wrong:  PC03_All Signals_LNbO_001-2026-08-15-14-30-22.csv
        → hyphens in date instead of periods; format not recognized

Correct: PC03_All Signals_LNbO_001 2026.08.15-14.30.22.csv
```

### Issue 2: No sample is linked, even though the filename is correct

**Symptom:** `sample_name` is populated correctly, but `samples` list is empty (deposition) or `thin_film_stack` is unset (annealing).

**Likely causes:**
1. No matching sample exists in the upload yet
2. The sample name in NOMAD does not match the filename exactly (case-sensitive, spaces matter)
3. NOMAD's search index has not caught up yet
4. The sample is in a different upload

**Fix:**
1. **Create the sample first:** add an `INLSubstrate` or `INLThinFilmStack` entry to the upload with the same name as `sample_name`
2. **Check case and spaces:** verify that the `name` field in the sample entry matches `sample_name` exactly
3. **Wait for re-indexing:** if you just created the sample, wait ~30 seconds and re-open the chamber entry
4. **Manual linking:** if automatic linking still does not work, manually fill the `samples` or `thin_film_stack` field

### Issue 3: Wrong entry type created (PC04 made an annealing entry, expected a deposition)

**Symptom:** You uploaded a `PC04_` log expecting a `PC04ElectrolyteChamberDeposition`, but got `PC04SubstrateAnnealing` instead.

**Likely cause:** The log file contains only heater channels (temperature, resistance) and no sputtering source columns (power, current, rate). This can happen if:
- The sputtering sources were powered off during the run
- The log was exported only from the annealing phase, not the full run
- The chamber configuration is different than expected

**Fix:**
1. Check that the CSV contains the column `PC Source 1 Active` (or similar)
2. If the run did include sputtering, re-export the log from the chamber
3. If the run was annealing-only, the entry type created is correct; manually add a `thin_film_stack` reference if needed

### Issue 4: Time-series data looks truncated or wrong

**Symptom:** Times don't match the log file, or there are large gaps in the data.

**Explanation:** The parser automatically trims inactive time steps—the time axis is re-zeroed to start at 0 s when the first source becomes active.
This is normal behavior and intended to focus on the active deposition window.

**If you need the full original timestamps:**
1. Refer to the raw CSV file for comparison
2. The `start_datetime` field stores the absolute start time; other timestamps are relative

---

## Working with PC03 and PC04 together

### Sample series: cathode, then electrolyte

A common workflow is to deposit a cathode in PC03, then deposit an electrolyte in PC04 on the same substrate:

1. Load substrate in PC03, run deposition → upload CSV, automatic sample link to (e.g.) `LCO_001`
2. Transfer substrate to PC04, run electrolyte deposition → upload CSV, automatic sample link to same `LCO_001`
3. Optional: run annealing in PC04 → upload CSV, same sample link

**Result:** In the upload, you have one `INLThinFilmStack` named `LCO_001` with two deposited layers (cathode + electrolyte),
plus an annealing event linked to the stack. NOMAD maintains the layer order automatically.

---

## Advanced: recipe reuse and parameter tracking

### Re-running a successful deposition

If you used the same recipe in PC03 or PC04 multiple times:

1. Upload all logs from different runs to the same upload (or different uploads if you prefer)
2. The automatic sample linking ensures each sample is linked to its corresponding deposition entry
3. To compare deposition parameters across runs, open each entry and review the time-series data
4. NOMAD generates plots automatically (pressure, temperature, power vs. time) for visual comparison

### Tracking recipe changes

If you modified a recipe between runs:
- The log files capture the **actual parameters** (temperatures, pressures, power) at each moment
- These are independent of the "recipe" concept in NOMAD
- You can manually add notes in the entry's `notes` field or create a custom analysis entry to document the recipe iteration

---

## Next steps

- **Learn more about samples:** see [Upload data and organize entries](../how_to/upload_and_organize.md) for general sample linking and upload strategies
- **More workflows:** check out [material characterization](material_characterization.md), [CIGSe solar cells](cigs_solar_cell.md), and [BiSI solar cells](bisi_solar_cell.md) for other lab workflows
- **Characterization:** after battery deposition and annealing, you can link measurements (electrochemistry, XRD, SEM) using the same sample references
- **Reference pages:** for detailed field descriptions, see [Batteries reference](../reference/batteries.md)
