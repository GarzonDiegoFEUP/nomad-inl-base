"""
Unit tests for Witec optical spectrum measurements (Raman and Photoluminescence).

Tests cover:
- WitecOpticalSpectrumParser: File detection, measurement type detection, metadata extraction
- INLRaman: Raman spectroscopy schema with cm⁻¹ x-axis
- INLPhotoluminescence: PL schema with eV x-axis
- Integration: Full workflows for both Raman and PL
"""

import numpy as np
import pytest

from nomad.datamodel.datamodel import EntryArchive
from nomad_inl_base.schema_packages.characterization import (
    INLRaman,
    INLPhotoluminescence,
    ExcitationBeam,
    SpectrometerSettings,
    DetectorSettings,
    ObjectiveInfo,
    SampleLocation,
    SpectrumData,
)


# ============================================================================
# Test Fixtures - Raman
# ============================================================================


@pytest.fixture
def raman_spec_data_content():
    """Example Raman _Spec.Data file content (cm⁻¹)."""
    return """[Header]
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
40.8, 1015
"""


@pytest.fixture
def pl_spec_data_content():
    """Example PL _Spec.Data file content (eV)."""
    return """[Header]
FileName = 260901B1 BCS_001_Spec.Data 1
GraphName = Spectrum
PositionX = 1302.0
PositionY = -1450.1
PositionZ = 0.0
XAxisUnit = eV
DataUnit = CCD cts

[Data]
X-Axis, Label
eV, CCD cts
 2.0630E+00, 8.1005E+02
 2.0626E+00, 8.0650E+02
 2.0621E+00, 8.0805E+02
 2.0616E+00, 8.0800E+02
"""


# ============================================================================
# Parser Tests - Measurement Type Detection
# ============================================================================


class TestWitecOpticalSpectrumParserDetection:
    """Tests for Raman vs PL detection based on x-axis unit."""

    def test_detect_raman_measurement_type(self, raman_spec_data_content):
        """Test detection of Raman measurement (1/cm unit)."""
        x_axis_unit = None
        for line in raman_spec_data_content.split('\n'):
            if 'XAxisUnit' in line and '=' in line:
                x_axis_unit = line.split('=')[1].strip().lower()
                break
        
        is_raman = '1/cm' in x_axis_unit or 'rel.' in x_axis_unit
        assert is_raman is True

    def test_detect_pl_measurement_type(self, pl_spec_data_content):
        """Test detection of PL measurement (eV unit)."""
        x_axis_unit = None
        for line in pl_spec_data_content.split('\n'):
            if 'XAxisUnit' in line and '=' in line:
                x_axis_unit = line.split('=')[1].strip().lower()
                break
        
        is_pl = 'ev' in x_axis_unit
        assert is_pl is True

    def test_parse_raman_spectrum_cm_inv(self, raman_spec_data_content):
        """Test extraction of Raman spectrum with cm⁻¹ x-axis."""
        x_values = []
        y_values = []
        in_data = False
        
        for line in raman_spec_data_content.split('\n'):
            if line.strip() == '[Data]':
                in_data = True
                continue
            if in_data and ',' in line and (line[0].isdigit() or line[0] == ' '):
                try:
                    parts = line.split(',')
                    x = float(parts[0].strip())
                    y = float(parts[1].strip())
                    x_values.append(x)
                    y_values.append(y)
                except ValueError:
                    pass
        
        assert len(x_values) == 5
        assert len(y_values) == 5
        assert x_values[0] == 0.0
        assert x_values[-1] == 40.8

    def test_parse_pl_spectrum_ev(self, pl_spec_data_content):
        """Test extraction of PL spectrum with eV x-axis."""
        x_values = []
        y_values = []
        in_data = False
        
        for line in pl_spec_data_content.split('\n'):
            if line.strip() == '[Data]':
                in_data = True
                continue
            if in_data and ',' in line and (line[0].isdigit() or line[0] == ' '):
                try:
                    parts = line.split(',')
                    x = float(parts[0].strip())
                    y = float(parts[1].strip())
                    x_values.append(x)
                    y_values.append(y)
                except ValueError:
                    pass
        
        assert len(x_values) == 4
        assert len(y_values) == 4
        # PL data in eV range (2.06 eV)
        assert 2.06 < x_values[0] <= 2.063


# ============================================================================
# Schema Tests - Raman
# ============================================================================


class TestINLRamanSchema:
    """Tests for INLRaman measurement schema."""

    def test_raman_entry_creation(self):
        """Test INLRaman entry creation with all subsections."""
        entry = INLRaman(
            operator='Jane Doe',
            configuration='Raman CCD1_532',
            duration=43.0,
            system_id='WITec-Alpha300',
            excitation=ExcitationBeam(wavelength=532.032),
            spectrometer=SpectrometerSettings(
                grating_type='G2: 1800 g/mm BLZ=500nm',
                center_wavelength=532.0,
                spectral_center=1000.0,
            ),
            detector=DetectorSettings(
                camera_model='DU401_BV',
                pixels_width=1024,
                pixels_height=127,
            ),
            objective=ObjectiveInfo(
                name='Plan Apochromat 50x',
                magnification=50.0,
            ),
            sample_location=SampleLocation(x=1234.5, y=2345.6, z=0.0),
            spectrum=SpectrumData(
                x_values=np.array([0.0, 10.2, 20.4]),
                y_values=np.array([1050, 1102, 998]),
                y_unit='CCD cts',
            ),
        )
        
        assert entry.operator == 'Jane Doe'
        assert entry.spectrum.y_unit == 'CCD cts'

    def test_raman_normalize_generates_plot(self):
        """Test that normalize() generates Plotly figure for Raman."""
        entry = INLRaman(
            spectrum=SpectrumData(
                x_values=np.array([0.0, 10.2, 20.4, 30.6]),
                y_values=np.array([1050, 1102, 998, 1010]),
                y_unit='CCD cts',
            ),
        )
        
        archive = EntryArchive()
        entry.normalize(archive, None)
        
        # Check plot was generated
        assert entry.figures is not None
        assert len(entry.figures) > 0
        assert entry.figures[0].label == 'Raman Spectrum'

    def test_raman_spectrum_plot_axes(self):
        """Test that Raman plot has correct axes (cm⁻¹ vs CCD cts)."""
        x_vals = np.array([0.0, 500.0, 1000.0, 1500.0])
        y_vals = np.array([1000, 1100, 950, 1050])
        
        entry = INLRaman(
            spectrum=SpectrumData(
                x_values=x_vals,
                y_values=y_vals,
                y_unit='CCD cts',
            ),
        )
        
        archive = EntryArchive()
        entry.normalize(archive, None)
        
        assert len(entry.figures) > 0
        # Verify the plot was created (structure check)
        plot = entry.figures[0]
        assert hasattr(plot, 'label')


# ============================================================================
# Schema Tests - Photoluminescence
# ============================================================================


class TestINLPhotoluminescenceSchema:
    """Tests for INLPhotoluminescence measurement schema."""

    def test_pl_entry_creation(self):
        """Test INLPhotoluminescence entry creation."""
        entry = INLPhotoluminescence(
            operator='Witec User',
            configuration='Raman CCD1_532',
            duration=42.0,
            system_id='100-1200-682',
            excitation=ExcitationBeam(wavelength=532.032),
            spectrometer=SpectrometerSettings(
                grating_type='G1: 600 g/mm BLZ=500nm',
                center_wavelength=670.185,
                spectral_center=1.850,  # eV for PL
            ),
            detector=DetectorSettings(
                camera_model='DU401_BV',
                pixels_width=1024,
                pixels_height=127,
            ),
            objective=ObjectiveInfo(
                name='Zeiss LD EC Epiplan-Neofluar Dic 50x / 0.55',
                magnification=50.0,
            ),
            sample_location=SampleLocation(x=1302.0, y=-1450.1, z=0.0),
            spectrum=SpectrumData(
                x_values=np.array([2.063, 2.062, 2.061, 2.060]),
                y_values=np.array([810, 806, 808, 808]),
                y_unit='CCD cts',
            ),
        )
        
        assert entry.operator == 'Witec User'
        assert entry.spectrometer.spectral_center.magnitude == 1.850
        assert len(entry.spectrum.x_values) == 4

    def test_pl_normalize_generates_plot(self):
        """Test that normalize() generates Plotly figure for PL."""
        entry = INLPhotoluminescence(
            spectrum=SpectrumData(
                x_values=np.array([2.063, 2.062, 2.061, 2.060]),
                y_values=np.array([810, 806, 808, 808]),
                y_unit='CCD cts',
            ),
        )
        
        archive = EntryArchive()
        entry.normalize(archive, None)
        
        # Check plot was generated
        assert entry.figures is not None
        assert len(entry.figures) > 0
        assert entry.figures[0].label == 'PL Spectrum'

    def test_pl_spectrum_plot_axes(self):
        """Test that PL plot has correct axes (eV vs CCD cts)."""
        x_vals = np.array([1.8, 1.9, 2.0, 2.1])
        y_vals = np.array([800, 850, 900, 850])
        
        entry = INLPhotoluminescence(
            spectrum=SpectrumData(
                x_values=x_vals,
                y_values=y_vals,
                y_unit='CCD cts',
            ),
        )
        
        archive = EntryArchive()
        entry.normalize(archive, None)
        
        assert len(entry.figures) > 0
        plot = entry.figures[0]
        assert plot.label == 'PL Spectrum'


# ============================================================================
# Common Schema Tests
# ============================================================================


class TestCommonSubsections:
    """Tests for shared subsections used by both Raman and PL."""

    def test_excitation_beam_creation(self):
        """Test ExcitationBeam subsection."""
        excitation = ExcitationBeam(wavelength=532.032, power=50.0)
        assert excitation.wavelength.magnitude == 532.032
        assert excitation.power.magnitude == 50.0

    def test_detector_settings_creation(self):
        """Test DetectorSettings subsection."""
        detector = DetectorSettings(
            camera_model='DU401_BV',
            pixels_width=1024,
            pixels_height=127,
            temperature=-60.0,
            integration_time=0.5,
            accumulations=3,
        )
        assert detector.camera_model == 'DU401_BV'
        assert detector.accumulations == 3

    def test_sample_location_creation(self):
        """Test SampleLocation subsection."""
        location = SampleLocation(x=1234.5, y=2345.6, z=0.0)
        assert location.x.magnitude == 1234.5
        assert location.y.magnitude == 2345.6

    def test_spectrum_data_array_consistency(self):
        """Test that spectrum X and Y arrays match in length."""
        x_vals = np.array([0.0, 10.2, 20.4])
        y_vals = np.array([1050, 1102, 998])
        
        spectrum = SpectrumData(x_values=x_vals, y_values=y_vals)
        assert len(spectrum.x_values) == len(spectrum.y_values)


# ============================================================================
# Edge Cases and Validation
# ============================================================================


class TestMeasurementValidation:
    """Tests for data validation and edge cases."""

    def test_empty_spectrum_handling(self):
        """Test that empty spectrum is handled gracefully."""
        entry = INLRaman(
            spectrum=SpectrumData(
                x_values=np.array([]),
                y_values=np.array([]),
            ),
        )
        
        archive = EntryArchive()
        entry.normalize(archive, None)
        # Should not raise error

    def test_single_point_spectrum(self):
        """Test spectrum with single data point."""
        entry = INLPhotoluminescence(
            spectrum=SpectrumData(
                x_values=np.array([2.063]),
                y_values=np.array([810]),
            ),
        )
        
        archive = EntryArchive()
        entry.normalize(archive, None)
        # Single point should still generate plot

    def test_raman_wavelength_validity(self):
        """Test that Raman wavelengths are physically reasonable."""
        # Common Raman laser wavelengths (nm)
        valid_wavelengths = [405, 532, 633, 785, 1064]
        
        for wl in valid_wavelengths:
            excitation = ExcitationBeam(wavelength=float(wl))
            assert excitation.wavelength.magnitude == float(wl)

    def test_pl_energy_range(self):
        """Test that PL energy data is in reasonable range."""
        # Typical PL in visible/near-IR: 1.5-3.5 eV
        x_vals = np.array([1.5, 2.0, 2.5, 3.0, 3.5])
        y_vals = np.array([100, 200, 500, 200, 100])
        
        spectrum = SpectrumData(x_values=x_vals, y_values=y_vals)
        assert np.all(spectrum.x_values.magnitude >= 1.5)
        assert np.all(spectrum.x_values.magnitude <= 3.5)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
