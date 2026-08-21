# Tutorial – Full CIGSe Solar Cell Workflow

This tutorial guides you through fabricating a complete **CIGSe (Copper Indium Gallium Selenide) photovoltaic device**.
The workflow combines multiple PVD and wet-chemistry techniques to build up the absorber and contacts, then characterizes
the final device with standard solar-cell measurements.

## Prerequisites

- A running NOMAD Oasis with the `nomad-inl-base` plugin installed
- An upload where you can create and link entries
- Sample files from characterization instruments (`.txt` for EQE and IV results,
  `.xrdml`/`.rasx`/`.brml`/`.raw` for XRD)
- Familiarity with the [onboarding tutorial](tutorial.md) for basic upload and linking concepts

---

## Lab workflow overview

| Lab step | NOMAD entry type | Created | Recipe? |
|----------|------------------|---------|---------|
| Clean SLG substrate | `INLSubstrate` | Manually | – |
| Deposit Mo (cathode) | `StarDCSputtering` | Manually | ✓ |
| Deposit In (METEOR) | `METEORDeposition` | Manually | – |
| Deposit CuGa (STAR) | `STARDCReactiveSputtering` | Manually | ✓ |
| Selenize (STAR) | `STARSelenizationAnnealing` | Manually | ✓ |
| Deposit CdS (CBD) | `INLChemicalBathDeposition` | Manually | ✓ |
| Deposit iZnO + ZnO:Al (STAR RF) | `StarRFSputtering` | Manually | ✓ |
| EQE measurement | `INLEQE` | Parser (`.txt`) | – |
| Solar cell IV | `INLSolarCellIV` | Parser (`.txt`) | – |
| XRD measurement | `INLXRayDiffraction` | Parser (`.xrdml` etc.) | – |

---

## Step 1 – Substrate and first metal contact (Mo)

### Create the SLG substrate

1. Create **INL Substrate** entry:
   - **Name** – e.g. `SLG-CIGS-001`
   - **Material** – `SLG`
   - **Geometry** – leave empty (auto-fills to 25 × 25 × 1 mm)

### Deposit Mo cathode

1. Create **STAR DC Sputtering** entry:
   - **Name** – e.g. `Mo-CIGS-001`
   - **Operator** – your name
   - **Samples** – reference `SLG-CIGS-001`
   - **Base pressure** – chamber base pressure
2. **Steps** – add DC sputtering step(s) with:
   - Duration, voltage, current, argon flow
   - Substrate set temperature (if heating)
3. **Sources** – add one source referencing a **Sputtering Target** entry (Mo).
   If you haven't created the target yet, create it first:
   - Create **Sputtering Target** entry with name, delivery date, components (pure Mo)
   - Reference it in the Mo deposition entry
4. Tick **Creates new thin film** and save.

!!! tip
    After normalization, you will have:
    - `Mo-CIGS-001_thin_film` (Mo layer)
    - `Mo-CIGS-001_thin_film_stack` (SLG + Mo)
    
    Use the stack entry in all subsequent depositions.

---

## Step 2 – In layer (METEOR e-beam)

1. Create **METEOR E-Beam Evaporation** entry:
   - **Name** – e.g. `In-CIGS-001`
   - **Operator** – your name
   - **Substrate** – select `Mo-CIGS-001_thin_film_stack` from Step 1
   - **Mask** – describe any shadow mask
2. **Pockets** – set **Material** to `Indium` on the active pocket
3. **QCM** – The parser will fill **Thickness** from the `.nbl` log file
4. Tick **Creates new thin film** and save.

After normalization:
- `In-CIGS-001_thin_film` (In layer appended to the stack)
- `In-CIGS-001_thin_film_stack` (SLG + Mo + In)

---

## Step 3 – CuGa co-deposition (STAR reactive DC with selenium)

This is the most complex step: simultaneous metal sputtering and pulsed selenium.

1. Create **STAR DC Reactive Sputtering** entry:
   - **Name** – e.g. `CuGa-Se-CIGS-001`
   - **Operator** – your name
   - **Samples** – reference `In-CIGS-001_thin_film_stack`
   - **Base pressure**
2. **Sources** – add two sources (Cu and Ga targets)
3. **Steps** – add one or more sputtering steps, each with:
   - Duration, voltage, current, argon/gas flow
   - **Substrate set temperature** (typically 400–550 °C)
   - **Substrate rotation** enabled if applicable
   - **Selenium Pulse Parameters** sub-section:
     - **Selenium cell** – reference a **Selenium Cell** entity (create one first if needed)
     - **Valve opening** (mm)
     - **Time on / Time off** (s) – pulse duty cycle
     - **Cell temperature** (°C)
     - **Cracker current** (A) and **Cracker voltage** (V)
     - **Process time** (min) – total duration of Se pulsing
     - **Cracker power** and **Total Se on time** auto-compute on normalization
4. Tick **Creates new thin film** and save.

!!! info
    If this is a recurring process, consider creating a **STAR Sputtering Recipe**
    entry with the step(s) and reusing it in future CuGa runs by ticking **Apply recipe**.

After normalization:
- `CuGa-Se-CIGS-001_thin_film` (CuGa layer)
- `CuGa-Se-CIGS-001_thin_film_stack` (SLG + Mo + In + CuGa)

---

## Step 4 – Selenization annealing (STAR)

Post-deposition annealing in a selenium atmosphere to improve absorber quality.

1. Create **STAR Selenization Annealing** entry:
   - **Name** – e.g. `Selenize-CIGS-001`
   - **Operator** – your name
   - **Samples** – reference `CuGa-Se-CIGS-001_thin_film_stack`
   - **Base pressure**
2. Add one or more **Se Annealing Step** sub-sections, each with:
   - **Duration** (min)
   - **Substrate set temperature** (°C)
   - **Selenium Pulse Parameters** (same fields as reactive DC sputtering)
3. Tick **Creates new thin film** if the selenization is considered a distinct layer
   (typically not), or leave it off if you want to treat it as in-situ processing.
4. Save.

!!! note
    Unlike deposition, selenization annealing may not create a new film entry
    if it is considered part of the absorber processing rather than a distinct layer.
    Consult your lab's conventions.

---

## Step 5 – CdS window layer (CBD)

Chemical bath deposition of the CdS buffer layer.

1. Create **INL Chemical Bath Deposition** entry:
   - **Name** – e.g. `CdS-CIGS-001`
   - **Operator** – your name
   - **Samples** – reference the absorber stack from Step 4
   - **Bath temperature** (°C), **pH**, **Duration** (min), **Stirring speed** (rpm)
2. **Bath composition** – add `INLCBDComponentMixture` entries for each bath component:
   - **CdCl₂** solution
   - **Thiourea** solution
   - **Ammonia** solution
   
   Each component can reference a pre-made **Solution** entry or use an inline
   `solution_template` for auto-creation. Set **Order** to specify addition sequence.
3. Optionally set **Color change time** if a reaction was observed.
4. Tick **Creates new thin film** and save.

!!! tip
    CdS is typically a thin, uniform window layer. Consider using a **CBD Recipe**
    if your standard CdS bath conditions are reused across samples.

After normalization:
- `CdS-CIGS-001_thin_film`
- `CdS-CIGS-001_thin_film_stack` (absorber + CdS)

---

## Step 6 – Front contacts (iZnO + ZnO:Al, STAR RF sputtering)

Two RF sputtering layers for the transparent conductive oxide window.

1. Create **STAR RF Sputtering** entry:
   - **Name** – e.g. `TCO-CIGS-001` (TCO = transparent conductive oxide)
   - **Operator** – your name
   - **Samples** – reference the CdS stack from Step 5
   - **Base pressure**
2. **Sources** – add one or two sources depending on your setup:
   - One for **iZnO** (intrinsic ZnO)
   - One for **ZnO:Al** (aluminum-doped ZnO)
3. **Steps** – add RF sputtering steps (typically two: iZnO, then ZnO:Al):
   - **iZnO step**: duration, power, gas flow, substrate temperature
   - **ZnO:Al step**: duration, power, gas flow, substrate temperature
   - Both may include substrate rotation
4. Tick **Creates new thin film** and save.

After normalization:
- `TCO-CIGS-001_thin_film_stack` (full absorber + buffer + TCO)

---

## Step 7 – Final characterization

### EQE (External Quantum Efficiency)

1. Upload your EQE data file (`*.eqe*.txt`).
2. NOMAD creates an `INLEQE` entry automatically.
3. Open the entry and set:
   - **Operator**
   - **Samples** → reference the final stack from Step 6
4. Save. The EQE spectrum is plotted automatically.

### Solar cell IV curve

1. Upload your IV results file (e.g. `*Results Table*.txt`).
2. NOMAD creates an `INLSolarCellIV` entry automatically.
3. Open the entry and set:
   - **Operator**
   - **Samples** → reference the final stack
4. Save. The best-efficiency cell's JV curve and performance boxplot are plotted.

### XRD measurement

1. Upload your XRD diffractogram (`.xrdml`, `.rasx`, `.brml`, or `.raw`).
2. NOMAD creates an `INLXRayDiffraction` entry automatically.
3. Open the entry and set:
   - **Operator**
   - **Samples** → reference the final stack
4. Save.

---

## Step 8 – Final check

Use NOMAD's **Graph** view to verify the complete chain:

```
SLG Substrate
    ↓
Mo (cathode)
    ↓
In (seed layer)
    ↓
CuGa+Se (absorber)
    ↓
Selenization (annealing, if tracked)
    ↓
CdS (buffer)
    ↓
iZnO + ZnO:Al (front contacts)
    ↓
EQE, IV, XRD measurements
```

Check:
- Each deposition references the previous stack
- All characterization entries link to the final stack
- Operators and timestamps are filled in
- Recipes (if used) are applied consistently

---

## Recipe reuse

If you fabricate CIGSe devices regularly, create recipes for the repetitive steps:

1. **Mo sputtering recipe** – Save the DC parameters, argon flow, and heating profile
2. **CuGa+Se recipe** – Save the reactive DC step(s) with Se pulse parameters
3. **Selenization recipe** – Save the annealing profile
4. **CdS bath recipe** – Save the bath composition and temperature
5. **TCO recipe** – Save the iZnO and ZnO:Al RF parameters

Then on the next run, reference each recipe and tick **Apply recipe** to auto-fill
those fields. Recipes use non-destructive merging, so you can override fields per run
if needed.

---

## Common questions

### Q: Should I create a new thin-film stack after each step?

**A:** Yes. Tick **Creates new thin film** on every deposition so NOMAD tracks each layer
in the stack. This enables traceability and makes characterization linking unambiguous.

### Q: What if I need to re-deposit a layer?

**A:** Create a new deposition entry and reference the existing stack. Set the layer count
appropriately. NOMAD will track the replacement as a new measurement point in the provenance graph.

### Q: Can I upload all my characterization files in one go?

**A:** Yes. Upload all `.txt`, `.xrdml`, and other files in a single batch. NOMAD will
auto-create separate entries for EQE, IV, and XRD. Then open each measurement entry
and link them all to the final stack.

---

## Next steps

- [How to use recipes](../how_to/use_this_plugin.md#using-recipes)
- [Reference – STAR Sputtering](../reference/sputtering.md)
- [Reference – METEOR E-Beam](../reference/meteor.md)
- [Reference – Wet Deposition](../reference/wet_deposition.md) (for CBD specifics)
- [Reference – Characterization](../reference/characterization.md) (for EQE/IV/XRD formats)
