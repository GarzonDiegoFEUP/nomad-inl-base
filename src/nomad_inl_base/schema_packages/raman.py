"""Raman spectroscopy measurement schemas for INL.

This module defines Raman measurement classes that are integrated into
the characterization schema package. Schemas are automatically registered
via the characterization package's m_package.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

import numpy as np
import plotly.graph_objects as go
from nomad.datamodel.data import ArchiveSection
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.metainfo import (
    Category,
    Quantity,
    Section,
    SubSection,
)


class ExcitationBeam(ArchiveSection):
    """Laser excitation beam parameters."""

    m_def = Section(label='Excitation Beam')

    wavelength = Quantity(
        type=np.float64,
        unit='nanometer',
        description='Laser excitation wavelength.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='nanometer',
        ),
    )

    power = Quantity(
        type=np.float64,
        unit='milliwatt',
        description='Laser excitation power.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='milliwatt',
        ),
    )


class SpectrometerSettings(ArchiveSection):
    """Spectrometer/monochromator configuration."""

    m_def = Section(label='Spectrometer Settings')

    grating_type = Quantity(
        type=str,
        description='Grating specification (e.g., "G2: 1800 g/mm BLZ=500nm").',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    center_wavelength = Quantity(
        type=np.float64,
        unit='nanometer',
        description='Center wavelength of the monochromator.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='nanometer',
        ),
    )

    spectral_center = Quantity(
        type=np.float64,
        unit='1/cm',
        description='Spectral center in Raman shift units.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='1/cm',
        ),
    )


class DetectorSettings(ArchiveSection):
    """Detector (camera) configuration."""

    m_def = Section(label='Detector Settings')

    camera_model = Quantity(
        type=str,
        description='Camera model name.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    pixels_width = Quantity(
        type=int,
        description='Width of detector in pixels.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    pixels_height = Quantity(
        type=int,
        description='Height of detector in pixels.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    temperature = Quantity(
        type=np.float64,
        unit='celsius',
        description='Detector operating temperature.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='celsius',
        ),
    )

    cycle_time = Quantity(
        type=np.float64,
        unit='second',
        description='Detector cycle time.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='millisecond',
        ),
    )

    integration_time = Quantity(
        type=np.float64,
        unit='second',
        description='Integration time per accumulation.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='millisecond',
        ),
    )

    accumulations = Quantity(
        type=int,
        description='Number of accumulations.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    ad_converter = Quantity(
        type=str,
        description='A/D converter specification (e.g., "AD1 (16Bit)").',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    vertical_shift_speed = Quantity(
        type=np.float64,
        unit='microsecond',
        description='Vertical shift speed.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='microsecond',
        ),
    )

    horizontal_shift_speed = Quantity(
        type=np.float64,
        unit='megahertz',
        description='Horizontal shift speed.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='megahertz',
        ),
    )

    preamplifier_gain = Quantity(
        type=int,
        description='Preamplifier gain setting.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    readout_mode = Quantity(
        type=str,
        description='Detector readout mode (e.g., "Full Vertical Binning").',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )


class ObjectiveInfo(ArchiveSection):
    """Microscope objective specifications."""

    m_def = Section(label='Objective Info')

    name = Quantity(
        type=str,
        description='Objective model name.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    magnification = Quantity(
        type=np.float64,
        description='Objective magnification (e.g., 50.0x).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    numerical_aperture = Quantity(
        type=np.float64,
        description='Objective numerical aperture.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )


class SampleLocation(ArchiveSection):
    """Sample stage position coordinates."""

    m_def = Section(label='Sample Location')

    x = Quantity(
        type=np.float64,
        unit='micrometer',
        description='Sample stage X position (global coordinate).',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='micrometer',
        ),
    )

    y = Quantity(
        type=np.float64,
        unit='micrometer',
        description='Sample stage Y position (global coordinate).',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='micrometer',
        ),
    )

    z = Quantity(
        type=np.float64,
        unit='micrometer',
        description='Sample stage Z position (global coordinate).',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='micrometer',
        ),
    )


class SpectrumData(ArchiveSection):
    """Raman spectrum data arrays."""

    m_def = Section(label='Spectrum Data')

    x_values = Quantity(
        type=np.float64,
        shape=['*'],
        unit='1/cm',
        description='Raman shift axis (X-axis).',
        a_eln=ELNAnnotation(defaultDisplayUnit='1/cm'),
    )

    y_values = Quantity(
        type=np.float64,
        shape=['*'],
        unit='count',
        description='Intensity values (Y-axis), in CCD counts.',
        a_eln=ELNAnnotation(defaultDisplayUnit='count'),
    )

    y_unit = Quantity(
        type=str,
        description='Unit of intensity values (typically "CCD cts" or "counts").',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )


class INLRaman(INLCharacterization, PlotSection):
    """Raman spectroscopy measurement following INL characterization standards."""

    m_def = Section(
        label='INL Raman Spectroscopy',
        categories=[INLCharacterizationCategory],
    )

    # Metadata subsections
    excitation = SubSection(section_def=ExcitationBeam)
    spectrometer = SubSection(section_def=SpectrometerSettings)
    detector = SubSection(section_def=DetectorSettings)
    objective = SubSection(section_def=ObjectiveInfo)
    sample_location = SubSection(section_def=SampleLocation)
    spectrum = SubSection(section_def=SpectrumData)

    # Configuration info
    configuration = Quantity(
        type=str,
        description='Measurement configuration (e.g., "Raman CCD1_532").',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    duration = Quantity(
        type=np.float64,
        unit='second',
        description='Total measurement duration.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='second',
        ),
    )

    system_id = Quantity(
        type=str,
        description='Instrument system ID.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        self.figures = []

        # Generate Raman spectrum plot
        if self.spectrum and self.spectrum.x_values is not None and self.spectrum.y_values is not None:
            x_values = np.array(self.spectrum.x_values)
            y_values = np.array(self.spectrum.y_values)

            if len(x_values) > 0 and len(y_values) > 0 and len(x_values) == len(y_values):
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode='lines',
                        name='Raman Spectrum',
                        line=dict(color='#1f77b4', width=2),
                        hovertemplate='Raman Shift: %{x:.2f} cm⁻¹<br>Intensity: %{y:.0f} cts<extra></extra>',
                    )
                )
                fig.update_layout(
                    template='plotly_white',
                    height=400,
                    width=716,
                    xaxis_title='Raman Shift (cm⁻¹)',
                    yaxis_title='Intensity (CCD cts)',
                    title='Raman Spectrum',
                    hovermode='x unified',
                )
                self.figures.append(
                    PlotlyFigure(label='Raman Spectrum', figure=fig.to_plotly_json())
                )
