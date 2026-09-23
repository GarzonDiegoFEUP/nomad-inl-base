# Raman Spectroscopy Schema Reference

Complete documentation of all fields and subsections in the `INLRaman` measurement schema.

## Main Entry: INLRaman

**Base classes**: `INLCharacterization`, `PlotSection`

**Label**: INL Raman Spectroscopy

**Purpose**: Records a single Raman spectroscopy measurement with complete instrument configuration and spectrum data.

### Inherited Fields

#### From INLCharacterization

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `operator` | str | — | Name/ID of person who performed the measurement |
| `samples` | SubSection (repeats) | — | References to linked INLSampleReference entries |
| `datetime` | datetime | — | Timestamp of measurement |
| `lab_id` | str | — | Laboratory or location identifier (hidden in ELN) |

#### From PlotSection

| Field | Type | Description |
|-------|------|-------------|
| `figures` | SubSection (repeats) | Array of PlotlyFigure objects (auto-generated on normalize) |

### Measurement-Specific Fields

| Field | Type | Unit | Description | ELN Editable |
|-------|------|------|-------------|--------------|
| `configuration` | str | — | System configuration name (e.g., "Raman CCD1_532") | Yes |
| `duration` | float | second | Total measurement acquisition time | Yes |
| `system_id` | str | — | Instrument system identifier | Yes |

### Subsections

#### excitation: ExcitationBeam

Laser excitation beam parameters.

| Field | Type | Unit | Description | ELN Editable |
|-------|------|------|-------------|--------------|
| `wavelength` | float | nm | Excitation laser wavelength | Yes |
| `power` | float | mW | Laser power at sample | Yes |

**Example**: 532 nm, 50 mW laser for green Raman

#### spectrometer: SpectrometerSettings

Monochromator and grating configuration.

| Field | Type | Unit | Description | ELN Editable |
|-------|------|------|-------------|--------------|
| `grating_type` | str | — | Grating specification (e.g., "1800 g/mm, blazed 500 nm") | Yes |
| `center_wavelength` | float | nm | Center wavelength setting | Yes |
| `spectral_center` | float | 1/cm | Spectral center in Raman shift units | Yes |

**Notes**:
- Grating blazing angle affects diffraction efficiency
- Center wavelength affects accessible Raman shift range
- Spectral center typically maps 0 cm⁻¹ to a specific pixel position

#### detector: DetectorSettings

CCD/sCMOS camera and data acquisition settings.

| Field | Type | Unit | Description | ELN Editable |
|-------|------|------|-------------|--------------|
| `camera_model` | str | — | Detector model (e.g., "DU401_BV") | Yes |
| `pixels_width` | int | — | Detector width in pixels | Yes |
| `pixels_height` | int | — | Detector height in pixels | Yes |
| `temperature` | float | °C | Operating temperature | Yes |
| `cycle_time` | float | s | Time per complete read cycle | Yes |
| `integration_time` | float | s | Exposure time per frame | Yes |
| `accumulations` | int | — | Number of frames averaged | Yes |
| `ad_converter` | str | — | Analog-to-digital converter specification | Yes |
| `vertical_shift_speed` | float | µs | Vertical pixel shift speed | Yes |
| `horizontal_shift_speed` | float | MHz | Horizontal pixel shift speed | Yes |
| `preamplifier_gain` | int | — | Pre-amplifier gain setting (1–5) | Yes |
| `readout_mode` | str | — | Readout mode (e.g., "Full Vertical Binning") | Yes |

**Notes**:
- Cooled detectors (temperature < 0°C) reduce dark noise
- Higher integration time increases signal but may cause saturation
- Binning (vertical) reduces noise at the cost of spatial resolution
- Pre-amplifier gain affects read noise vs. dynamic range trade-off

#### objective: ObjectiveInfo

Microscope objective specifications.

| Field | Type | Unit | Description | ELN Editable |
|-------|------|------|-------------|--------------|
| `name` | str | — | Objective model/part number | Yes |
| `magnification` | float | — | Magnification (e.g., 50.0) | Yes |
| `numerical_aperture` | float | — | Numerical aperture (NA) | Yes |

**Example**: 50× NA 0.8 objective for confocal Raman

#### sample_location: SampleLocation

Sample stage position in global coordinates.

| Field | Type | Unit | Description | ELN Editable |
|-------|------|------|-------------|--------------|
| `x` | float | µm | Stage X position (global) | Yes |
| `y` | float | µm | Stage Y position (global) | Yes |
| `z` | float | µm | Stage Z position (global/height) | Yes |

**Notes**:
- Coordinates are absolute stage positions, useful for sample mapping
- Z coordinate often indicates focal plane or sample height
- Can be used to correlate multiple measurements from the same sample

#### spectrum: SpectrumData

Raman spectrum data arrays.

| Field | Type | Unit | Shape | Description | ELN Editable |
|-------|------|------|-------|-------------|--------------|
| `x_values` | float | 1/cm | [*] | Raman shift axis (X data) | No |
| `y_values` | float | count | [*] | Intensity values (Y data, CCD counts) | No |
| `y_unit` | str | — | — | Unit label for intensity (e.g., "CCD cts") | Yes |

**Notes**:
- X-axis units are always Raman shift (cm⁻¹)
- Y-axis is raw detector counts (not normalized/corrected)
- Arrays must have matching length for valid plot generation
- Witec export typically uses comma-separated format in data file

## Data Structure Example

```python
measurement = INLRaman(
    operator='Jane Doe',
    configuration='Raman CCD1_532',
    duration=43.0,  # seconds
    system_id='WITec-Alpha300',
    
    excitation=ExcitationBeam(
        wavelength=532.032,  # nm
        power=50.0,  # mW
    ),
    
    spectrometer=SpectrometerSettings(
        grating_type='G2: 1800 g/mm BLZ=500nm',
        center_wavelength=532.0,  # nm
        spectral_center=1000.0,  # 1/cm
    ),
    
    detector=DetectorSettings(
        camera_model='DU401_BV',
        pixels_width=1024,
        pixels_height=127,
        temperature=-60.0,  # °C
        integration_time=0.5,  # s
        accumulations=3,
        readout_mode='Full Vertical Binning',
    ),
    
    objective=ObjectiveInfo(
        name='Plan Apochromat 50x',
        magnification=50.0,
        numerical_aperture=0.8,
    ),
    
    sample_location=SampleLocation(
        x=1234.5,  # µm
        y=2345.6,  # µm
        z=0.0,  # µm
    ),
    
    spectrum=SpectrumData(
        x_values=[0.0, 10.2, 20.4, ...],  # Raman shift (1/cm)
        y_values=[1050, 1102, 998, ...],  # CCD counts
        y_unit='CCD cts',
    ),
)
```

## Auto-Generated Plots

### Raman Spectrum

**Type**: Line plot

**X-Axis**: Raman Shift (cm⁻¹)

**Y-Axis**: Intensity (CCD cts)

**Features**:
- Interactive hover shows exact values
- Zoom and pan enabled
- Displayed in NOMAD search results and entry view

## Metadata Extraction from Files

### From `_Spec.Data` file

The `[Header]` section contains:

```
PositionX = 1234.5
PositionY = 2345.6
PositionZ = 0.0
XAxisUnit = rel. 1/cm
DataUnit = CCD cts
```

Mapped to:
- `sample_location.x` ← PositionX
- `sample_location.y` ← PositionY
- `sample_location.z` ← PositionZ

The `[Data]` section contains comma-separated spectrum:

```
0.0, 1050
10.2, 1102
20.4, 998
...
```

Mapped to:
- `spectrum.x_values` ← first column
- `spectrum.y_values` ← second column

### From `Information` file

Key-value pairs by section:

```
General
Excitation Wavelength [nm] = 532.032
Duration = 0h 0m 43s
User Name = Jane Doe

UHTS300
Grating = G2: 1800 g/mm BLZ=500nm

DU401_BV
Width [Pixels] = 1024
Height [Pixels] = 127
Temperature [°C] = -60.0
Accumulations = 3
Integration Time [s] = 0.5

Objective
Name = Plan Apochromat 50x
Magnification = 50.0
```

Automatically mapped to corresponding schema fields.

## Units and Conventions

| Parameter | Unit | Notes |
|-----------|------|-------|
| Raman Shift | cm⁻¹ | Standard in spectroscopy (1/wavelength) |
| Wavelength | nm | Standard for optical measurements |
| Power | mW | Typical laser power range |
| Temperature | °C | Display unit; stored internally in Kelvin |
| Stage position | µm | Microscope stage convention |
| Integration time | s | Can range from µs to s depending on detector |
| Intensity | count | Raw CCD/sCMOS detector counts |

## Related Entries

- **INLCharacterization**: Base class for all INL characterization measurements
- **INLSampleReference**: Sample linking (in `samples` field)
- **PlotSection**: Provides automatic plot generation framework
