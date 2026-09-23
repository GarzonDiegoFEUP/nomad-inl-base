# Tutorial: Raman Measurement Example Walkthrough

This tutorial uses real example data to demonstrate the complete Raman spectroscopy workflow in nomad-inl-base.

## Example Data

We'll use a measurement of a carbon-based sample (boron carbide) acquired on a Witec Alpha300 system:

- **Sample**: BCS_001 (Boron Carbide Sample)
- **Laser**: 532.032 nm (green)
- **Operator**: Jane Doe
- **Date**: 2026-07-21

### Files

```
260721D11 BCS_001_Spec.Data 1.txt      (spectrum + position)
260721D11 BCS_001 Information.txt       (instrument config)
```

## Step 1: Understanding the Export Files

### Inspect Spectrum File (*.Spec.Data*.txt)

Open the `_Spec.Data` file with a text editor. You'll see:

```
[Header]
FileName = 260721D11 BCS_001_Spec.Data 1
GraphName = Spectrum
PositionX = 1234.5
PositionY = 2345.6
PositionZ = 0.0
XAxisUnit = rel. 1/cm
DataUnit = CCD cts

[Data]
0.0, 1050
10.2, 1102
20.4, 998
30.6, 1010
...
3200.0, 890
```

**What this contains**:
- **Header section**: Spatial coordinates (stage position) and units
- **Data section**: Comma-separated Raman shift and intensity values
- **X-axis**: Raman shift from ~0 to 3200 cm⁻¹
- **Y-axis**: CCD detector counts (1000–1100 range indicates good signal)

### Inspect Information File (Information.txt)

Open the `Information` file. You'll find sections like:

```
General
Excitation Wavelength [nm] = 532.032
Duration = 0h 0m 43s
User Name = Jane Doe
Configuration = Raman CCD1_532

UHTS300
Grating = G2: 1800 g/mm BLZ=500nm
Center Wavelength [nm] = 532.0
Spectral Center [rel. 1/cm] = 1000.0

DU401_BV
Width [Pixels] = 1024
Height [Pixels] = 127
Temperature [°C] = -60.0
Cycle Time [s] = 0.5125
Integration Time [s] = 0.5
Accumulations = 3
AD Converter = AD1 (16Bit)
Vertical Shift Speed = 0.3 µs
Horizontal Shift Speed = 5.0 MHz
Preamplifier Gain = 4
ReadMode = Full Vertical Binning

Objective
Name = Plan Apochromat 50x
Magnification = 50.0
Numerical Aperture = 0.8

Sample Location
PositionX [µm] = 1234.5
PositionY [µm] = 2345.6
PositionZ [µm] = 0.0
```

**Key observations**:
- Green laser (532 nm) typically used for carbon materials (resonance enhancement)
- High-resolution grating (1800 g/mm) for detailed spectral features
- Detector cooled to -60°C for low noise
- 3 accumulations: 0.5 s × 3 = 1.5 s total per spectrum
- Total duration: 43 seconds (includes motor movement, overhead)
- 50× objective with NA 0.8 (typical confocal setup)

## Step 2: Upload to NOMAD

### Via Web Upload

1. Log in to NOMAD instance
2. Click **Upload**
3. Create new upload or select existing entry
4. Drag both files into the upload area:
   - `260721D11 BCS_001_Spec.Data 1.txt`
   - `260721D11 BCS_001 Information.txt`
5. Click **Upload**

NOMAD's `RamanWitecParser` automatically:
- Detects the file pair by matching base name ("260721D11 BCS_001")
- Parses spectrum data (Raman shift array, intensity array)
- Extracts metadata from both files
- Creates `INLRaman` entry with all subsections populated

### Expected Processing

```
Parsing: 260721D11 BCS_001_Spec.Data 1.txt
  └─ [Header] PositionX: 1234.5 µm
  └─ [Data] 3200 spectral points

Parsing: 260721D11 BCS_001 Information.txt
  └─ Excitation: 532.032 nm
  └─ Detector: DU401_BV, -60°C, 3 acc
  └─ Objective: 50x NA0.8

Creating INLRaman entry:
  ✓ excitation → ExcitationBeam
  ✓ spectrometer → SpectrometerSettings
  ✓ detector → DetectorSettings
  ✓ objective → ObjectiveInfo
  ✓ sample_location → SampleLocation
  ✓ spectrum → SpectrumData
  ✓ normalize() → Plotly figure

Status: SUCCESS
```

## Step 3: Review Measurement Entry

After upload, navigate to the Raman measurement in NOMAD:

### Metadata Section

You'll see structured information:

```
operator: Jane Doe
configuration: Raman CCD1_532
duration: 43.0 s
system_id: WITec-Alpha300

Excitation Beam
├─ wavelength: 532.032 nm
└─ power: [manual entry - e.g., 50 mW]

Spectrometer Settings
├─ grating_type: G2: 1800 g/mm BLZ=500nm
├─ center_wavelength: 532.0 nm
└─ spectral_center: 1000.0 cm⁻¹

Detector Settings
├─ camera_model: DU401_BV
├─ pixels_width: 1024
├─ pixels_height: 127
├─ temperature: -60.0°C
├─ integration_time: 0.5 s
└─ accumulations: 3

Objective
├─ name: Plan Apochromat 50x
├─ magnification: 50.0
└─ numerical_aperture: 0.8

Sample Location
├─ x: 1234.5 µm
├─ y: 2345.6 µm
└─ z: 0.0 µm
```

### Add Manual Parameters

**Important**: Laser power was not in the export files. You must add it manually:

1. Edit the entry (click Edit or Pencil icon)
2. Navigate to **Excitation Beam** section
3. Enter **Power**: Type "50" and select unit "mW" from dropdown
4. Save

This is critical for reproducibility and future analysis.

## Step 4: View Raman Spectrum Plot

Scroll to **Plots/Figures** section. You'll see:

### Raman Spectrum Plot

```
Intensity (CCD cts)
       |
 1150  |      ╱╲
       |     ╱  ╲      ╱╲
 1100  |    ╱    ╲____╱  ╲___╱
       |   ╱                    ╲
 1050  |  ╱                      ╲
       | ╱
 1000  |╱
       |_________________________
    0     500    1000   1500   2000   2500   3000
           Raman Shift (cm⁻¹)
```

**Interactive features**:
- **Hover**: Shows exact Raman shift and intensity values
- **Zoom**: Click and drag to zoom into region of interest
- **Pan**: Hold shift and drag to move around
- **Reset**: Double-click to reset to original view
- **Download**: Camera icon saves as PNG

### Interpretation

**Features visible in this spectrum**:

1. **~500 cm⁻¹**: First-order diamond peak (boron carbide)
2. **~1200–1600 cm⁻¹**: D and G bands (disorder/graphite-like carbon)
3. **~2500–3000 cm⁻¹**: Overtone region (2D peak for graphene-like layers)

### Quality Assessment

From this plot, we can verify:
- ✓ **Good SNR**: ~100 counts above noise floor
- ✓ **No saturation**: Max ~1150 counts (well below 3000)
- ✓ **Clear peaks**: Well-resolved vibrational features
- ✓ **Smooth baseline**: No cosmic ray spikes or edge artifacts

## Step 5: Link to Sample Entry

To track provenance, link this measurement to a sample:

1. Scroll to **Samples** section
2. Click **Add Sample Reference**
3. Search for "BCS_001" or the sample ID
4. Select from results
5. Save entry

This creates bidirectional reference: Measurement ↔ Sample

## Step 6: Search and Export

### Search for Similar Measurements

In NOMAD search:

```
Query: def_name:INLRaman AND excitation.wavelength:532
Result: Find all Raman spectra measured with 532 nm laser
```

Other useful filters:
- `detector.temperature:[-60 TO -50]` — measurements at similar T
- `excitation.power:[40 TO 60]` — specific power range
- `samples.name:BCS*` — measurements on this sample family

### Export Data

Multiple export options:

1. **Download raw data**:
   - Raman shift array (X-axis, cm⁻¹)
   - Intensity array (Y-axis, CCD counts)
   - Full metadata as JSON or YAML

2. **Export plot**:
   - PNG image (high resolution)
   - SVG vector format (editable)
   - Plotly JSON (interactive)

3. **API access**:
   ```python
   # Python example
   from nomad.client import ArchiveClient
   
   client = ArchiveClient()
   raman = client.get_archive(upload_id='xxx', entry_id='yyy')
   
   # Access spectrum data
   x = raman.data.spectrum.x_values  # Raman shift
   y = raman.data.spectrum.y_values  # Intensity
   
   # Access metadata
   power = raman.data.excitation.power
   temp = raman.data.detector.temperature
   ```

## Step 7: Analysis and Interpretation

### Peak Identification

Use the Raman spectrum to identify phases and structure:

1. **Consult literature** or Raman spectral databases
2. **Peak position**: Determines molecular identity
3. **Peak intensity**: Related to concentration
4. **Peak width**: Indicates disorder/strain
5. **Area under peak**: Useful for quantitative analysis

### Multi-Sample Comparison

Plot multiple measurements on same sample:

```
Sample BCS_001 - Temperature Series
|
├─ T=300K: Power 50 mW → [Plot shows peaks at X cm⁻¹]
├─ T=400K: Power 50 mW → [Plot shows shifted peaks]
└─ T=500K: Power 50 mW → [Plot shows broadened peaks]

Observation: Peak position shifts with temperature
→ Thermal coefficient: Δν/ΔT = -0.02 cm⁻¹/K (typical for C-C)
```

## Common Issues and Solutions

### Issue: Spectrum looks noisy

**Possible causes**:
- Integration time too short
- Accumulations too low
- Laser power too weak
- Detector not cooled

**Solution**:
- Repeat measurement with increased integration time or accumulations
- Check detector temperature is < -50°C
- Verify laser power with power meter

### Issue: Peaks are very broad or shifted

**Possible causes**:
- Wavelength calibration drift
- Grating slightly misaligned
- Sample under thermal/mechanical stress
- High disorder in sample

**Solution**:
- Acquire calibration reference (e.g., silicon peak at 520.7 cm⁻¹)
- Check system calibration in Witec software

### Issue: "File pair not found" error

**Possible causes**:
- Base names don't match exactly (e.g., extra space)
- Only one file was uploaded
- Files in different upload batches

**Solution**:
- Verify filenames match: `260721D11 BCS_001_Spec.Data 1.txt` + `260721D11 BCS_001 Information.txt`
- Upload both files together in same batch

## Next Steps

1. **Analyze**: Use export tools to plot in origin, fit peaks, extract parameters
2. **Compare**: Acquire multiple measurements across sample or conditions
3. **Archive**: Store in NOMAD for long-term data management
4. **Share**: Use NOMAD's publishing features for open science

## Additional Resources

- [Reference Guide](../reference/raman_schema.md) - All schema fields
- [Background](../explanation/raman_setup.md) - Instrument details
- [How To](../how_to/using_raman.md) - Workflow guide
- NOMAD Documentation: https://nomad-lab.eu/docs
