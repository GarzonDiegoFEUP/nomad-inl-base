# Photoluminescence: Detailed Guide

## What is Photoluminescence?

Photoluminescence (PL) is the spontaneous emission of light from a material after optical excitation. When a photon with energy ≥ bandgap excites an electron-hole pair, radiative recombination produces a photon.

### Energy Diagram

```
Excitation (532 nm, 2.33 eV)
    ↓
    e⁻ ────────────── Conduction Band
    :           ↙ (relaxation)
    :        Emitted Photon (PL)
    :           ↙ (bandgap, Eg)
    h⁺ ────────────── Valence Band
```

## Measurement Basics

### Typical Setup
- **Laser**: 532 nm (2.33 eV) green photon
- **Detector**: CCD at -60°C (low dark current)
- **Grating**: 600 g/mm (wide spectral range)
- **Sample**: Any semiconductor or luminescent material

### Why 532 nm Excitation?
- **High energy**: Can excite across visible bandgaps (1.5–3.5 eV)
- **Safe**: Below UV, doesn't damage most materials
- **Efficient**: Strong absorption in many semiconductors
- **Common**: Available in many Raman/PL systems

### Typical Energy Range
PL measurements typically span:
- **IR**: 1.5–2.0 eV (low bandgap, narrow gap semiconductors)
- **Visible**: 2.0–3.0 eV (Si ~1.12 eV, GaN ~3.4 eV)
- **Theoretical max with 532 nm excitation**: 2.33 eV

## File Format Details

### Example _Spec.Data* (PL)
```
[Header]
FileName = 260901B1 BCS_001_Spec.Data 1
PositionX = 1302.0 µm
PositionY = -1450.1 µm
PositionZ = 0.0 µm
XAxisUnit = eV              ← Distinguishes PL from Raman
DataUnit = CCD cts

[Data]
X-Axis, Label
eV, CCD cts
2.0630E+00, 8.1005E+02     ← Energies in eV
2.0626E+00, 8.0650E+02
2.0621E+00, 8.0805E+02
...
1.8000E+00, 5.2000E+02     ← Lower energy tail
```

### Example Information* (PL)
```
General:
Duration: 0h 0m 42s
User Name: Witec User
Configuration: Raman CCD1_532    (same label, different mode)

UHTS300:
Excitation Wavelength [nm]: 532.032
Grating: G1: 600 g/mm BLZ=500nm   (lower res, wider range)
Center Wavelength [nm]: 670.185
Spectral Center [eV]: 1.850        ← In eV, not cm⁻¹

DU401_BV,35:
Integration Time [s]: 2.00000      (often longer for PL)
Accumulations: 20
Temperature [°C]: -59
```

## Data Interpretation

### Peak Position → Bandgap

The main peak in a PL spectrum typically corresponds to the bandgap:

```python
# Estimate bandgap energy
E_g ≈ E_peak  (for direct bandgap)

# Example: Si at 300K
# Peak at 1.12 eV ≈ bandgap at room temperature
```

### Peak Broadness → Defect Density

Broader peaks indicate:
- **Higher disorder** in the material
- **More defect states** acting as recombination centers
- **Lower quality** of the material

FWHM (Full Width at Half Max) < 50 meV → Good quality
FWHM > 100 meV → High defect density

### Multiple Peaks → Different Defects

Multiple peaks suggest:
- Main peak: Band-to-band transition
- Lower energy peaks: Defect-related transitions
- Indicates presence of specific defects/impurities

### Intensity → Luminescence Efficiency

Higher intensity → Better carrier collection (fewer non-radiative paths)

Relative intensity between samples indicates quantum efficiency.

## Advanced Analysis

### Temperature Dependence

PL changes with temperature due to:
1. **Bandgap shift** (moves to higher E at lower T)
2. **Peak broadening** (increases at higher T)
3. **Intensity change** (decreases at higher T)

Typical coefficient: dE_g/dT ≈ -2 to -3 meV/K

### Excitation Power Dependence

Plot PL intensity vs. laser power:
- Linear response → Equilibrium recombination
- Sublinear (slope < 1) → Saturation of defect states
- Superlinear (slope > 1) → Bimolecular recombination

### Time-Resolved PL

Lifetime (not measured here, but related):
- Short lifetime (<10 ns) → Defect-rich
- Long lifetime (>1 µs) → High quality

## Common Samples & Expected Spectra

### Silicon (Si)
- Bandgap: 1.12 eV @ 300K
- Peak: Sharp, centered at 1.12 eV
- FWHM: 20–50 meV (depends on quality)
- Note: Indirect bandgap → weaker PL intensity

### Gallium Nitride (GaN)
- Bandgap: 3.4 eV @ 300K
- Peak: Sharp, high intensity (direct bandgap)
- FWHM: 50–100 meV
- Often includes yellow luminescence (defect peak at 2.3 eV)

### Boron Carbide (B₄C)
- Bandgap: ~2.0 eV
- Peak: Can be broad (high defect concentration)
- PL used to assess quality of synthesis

### Diamond
- Bandgap: 5.5 eV
- Problem: 532 nm (2.33 eV) can't excite directly
- Two-photon excitation possible (requires high power)
- Usually no PL seen with single-photon 532 nm

## Troubleshooting PL Issues

### Issue: No signal (flat spectrum)
**Causes**:
- Laser misaligned (check alignment laser)
- Material not luminescent (try reference sample)
- Sample saturated/photobleached
- Detector not working

**Solutions**:
- Check laser power at sample position
- Verify sample is placed on stage
- Reduce laser power, let sample recover
- Test with calibration sample

### Issue: Noisy spectrum (random peaks)
**Causes**:
- Detector dark current high (not cooled)
- Integration time too short
- Cosmic rays hitting detector
- Laser noise

**Solutions**:
- Verify detector temperature is < -55°C
- Increase integration time/accumulations
- Use longer exposures (averaging reduces cosmic rays)
- Check laser power stability

### Issue: Broad/shifted peak
**Causes**:
- Material has defects (intentional or not)
- Thermal effects (sample heating under laser)
- Stray light contamination
- Misalignment shifting wavelength

**Solutions**:
- Characterize with Raman (complement PL info)
- Reduce laser power to minimize heating
- Check dark background (shutter closed)
- Re-center on sample

### Issue: Weird multi-peak structure
**Likely causes**:
- Multiple defect levels (expected for defective material)
- Substrate contribution (use different substrate)
- Surface vs. bulk transitions
- Laser line contamination

**Analysis**:
- Document peak positions and relative intensities
- Compare to literature values
- Link defect levels to material processing

## Comparison: PL vs. Raman on Same Sample

**Complementary information**:
- **Raman**: Structure of material (vibrational modes)
- **PL**: Electronic properties (bandgap, defects)

**Example: Defective Carbon**

Raman spectrum shows:
- D band (defects), G band (graphitic C)
- Indicates sp² disorder

PL spectrum shows:
- Weak or broad signal (defects reduce luminescence)
- Tells you how defects affect electronic properties

**Both together** = Complete picture of material quality.

## Export and Analysis

### From NOMAD
1. Click **Download** on spectrum plot
2. Save as PNG (image) or export raw data (CSV/JSON)

### Analysis Tools
- **Python**: scipy.optimize.curve_fit for peak fitting
- **Origin/GraphPad**: Built-in peak fitting
- **MATLAB**: Optimization toolbox

### Calculate Key Values
```python
# Fit Gaussian to PL peak
from scipy.optimize import curve_fit
import numpy as np

def gaussian(x, A, E0, sigma):
    return A * np.exp(-(x - E0)**2 / (2*sigma**2))

popt, _ = curve_fit(gaussian, energy, intensity)
E_peak = popt[1]        # Peak energy (bandgap)
FWHM = 2.355 * popt[2]  # Full Width Half Max
```

## References

- *Luminescence of Semiconductors and Their Nanostructures*, Wang et al., ed. (2005)
- Witec Alpha300 manual (instrument-specific)
- PL database: http://semiconductor.materials.center/ (example resource)

## See Also

- [Index: Raman vs PL Overview](./index.md)
- [Raman Tutorial](./tutorial/raman_example.md) (complementary technique)
- [Schema Reference](./reference/raman_schema.md) (INLPhotoluminescence fields)
