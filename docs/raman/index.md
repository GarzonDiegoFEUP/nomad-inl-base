# Optical Spectroscopy: Raman and Photoluminescence

This section documents optical spectrum measurements from the Witec Alpha300 system integrated into nomad-inl-base following INL characterization standards.

## Overview

The Witec system supports two complementary optical spectroscopy techniques:

### Raman Spectroscopy
- Probes **vibrational states** via inelastic light scattering
- X-axis: **Raman shift (cm⁻¹)**
- Applications: Material structure identification, phase analysis, defect detection
- File marker: `XAxisUnit = rel. 1/cm`

### Photoluminescence (PL)
- Probes **electronic states** via emission after optical excitation
- X-axis: **Photon energy (eV)**
- Applications: Bandgap determination, defect levels, carrier dynamics
- File marker: `XAxisUnit = eV`

Both techniques use **identical file formats** and are handled by a **unified parser** that auto-detects the measurement type.

## Quick Start

### For Raman Measurements
1. Export from Witec → Two files with `XAxisUnit = rel. 1/cm`
2. Upload both files to NOMAD
3. Parser creates **INLRaman** entry → Interactive plot (Raman shift vs intensity)

### For Photoluminescence
1. Export from Witec → Two files with `XAxisUnit = eV`
2. Upload both files to NOMAD
3. Parser creates **INLPhotoluminescence** entry → Interactive plot (photon energy vs intensity)

## File Format (Common to Both)

### _Spec.Data*.txt
```
[Header]
PositionX = 1234.5        (spatial coordinate, µm)
PositionY = 2345.6
PositionZ = 0.0
XAxisUnit = rel. 1/cm     (Raman) or eV (PL)  ← Determines entry type
DataUnit = CCD cts

[Data]
0.0, 1050                 (x-axis value, intensity)
10.2, 1102
...
```

### *Information*.txt
Metadata organized by section:
- General: Wavelength, duration, user, configuration
- UHTS300: Grating, center wavelength, spectral center
- DU401_BV: Detector settings
- Objective: Name, magnification
- Sample Location: X/Y/Z coordinates

## Supported Instruments

- **Witec Alpha300** (INL Facility)
  - Laser: 532 nm excitation
  - Detector: CCD (DU401_BV, cooled to -60°C)
  - Objective: 50× confocal
  - **Raman**: 1800 g/mm grating, 0–3500 cm⁻¹
  - **PL**: 600 g/mm grating, 1.5–3.5 eV

## Key Differences

| Feature | Raman | Photoluminescence |
|---------|-------|-------------------|
| **Physical principle** | Inelastic scattering | Luminescence emission |
| **X-axis unit** | Raman shift (cm⁻¹) | Photon energy (eV) |
| **What it detects** | Vibrational modes | Electronic states |
| **Sample requirement** | Any material | Must be luminescent |
| **Typical spectra** | Sharp peaks | Broad features |
| **Grating** | 1800 g/mm (high res) | 600 g/mm (wide range) |
| **Use case** | Structure ID, phase analysis | Bandgap, defect levels |

## Auto-Detection Workflow

```
Upload Files
    ↓
Pair Files (by base name)
    ↓
Read XAxisUnit from _Spec.Data [Header]
    ↓
        ├─ "rel. 1/cm" → INLRaman
        ├─ "eV" → INLPhotoluminescence
        └─ Unknown → Warning, skip
    ↓
Extract Metadata
    ↓
Generate Plot
    ↓
Create NOMAD Entry
```

## Documentation

- **[How To](how_to/using_raman.md)** - Complete workflow for both measurements
- **[Reference](reference/raman_schema.md)** - Schema field documentation
- **[Explanation](explanation/raman_setup.md)** - Instrument & theory background
- **[Tutorial](tutorial/raman_example.md)** - Worked example walkthrough

## Parser Information

**Class**: `WitecOpticalSpectrumParser` (unified for both Raman and PL)

**Features**:
- ✓ Automatic file pairing by base name
- ✓ Measurement type detection (Raman vs PL)
- ✓ Metadata extraction from both files
- ✓ Auto-plot generation with correct axes
- ✓ Backward compatible (alias: `RamanWitecParser`)

**Supported File Patterns**:
- `*_Spec.Data*.txt` and `*Information*.txt` (any base name)
- Case-sensitive matching required

