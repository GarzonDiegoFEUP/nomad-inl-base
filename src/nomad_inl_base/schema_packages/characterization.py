from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

import numpy as np
import plotly.express as px
from nomad.datamodel.data import EntryData, EntryDataCategory
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import Measurement
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.metainfo import Category, Quantity, SchemaPackage, Section, SubSection
from nomad_material_processing.general import TimeSeries
from nomad_material_processing.solution.general import Solution
from nomad_measurements.transmission.schema import ELNUVVisNirTransmission
from nomad_measurements.xrd.schema import ELNXRayDiffraction
from plotly.subplots import make_subplots

from nomad_inl_base.schema_packages.entities import INLSampleReference, INLThinFilmStack

m_package = SchemaPackage()


class INLCharacterizationCategory(EntryDataCategory):
    m_def = Category(label='INL Characterization', categories=[EntryDataCategory])


class INLCharacterization(Measurement, EntryData):
    """Base class for all INL characterization measurements."""

    m_def = Section(
        categories=[INLCharacterizationCategory],
        a_eln=dict(hide=['lab_id', 'location', 'steps', 'instruments']),
    )

    operator = Quantity(
        type=str,
        description='Name of the person who performed this measurement.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    samples = SubSection(
        section_def=INLSampleReference,
        repeats=True,
        description='Sample(s) measured in this characterization.',
    )


class INLXRayDiffraction(INLCharacterization, ELNXRayDiffraction):
    m_def = Section(
        label='INL XRD',
        categories=[INLCharacterizationCategory],
    )


class INLUVVisTransmission(INLCharacterization, ELNUVVisNirTransmission):
    m_def = Section(
        label='INL UV-Vis Transmission',
        categories=[INLCharacterizationCategory],
    )


# ---------------------------------------------------------------------------
# Cyclic voltammetry / electrochemistry
# ---------------------------------------------------------------------------


class CurrentTimeSeries(TimeSeries):
    m_def = Section(
        label_quantity='set_value',
        a_eln={'hide': ['set_value', 'set_time']},
    )
    value = Quantity(
        type=np.float64,
        description='The observed current as a function of time.',
        shape=['*'],
        unit='ampere',
    )


class CurrentDensityTimeSeries(TimeSeries):
    m_def = Section(
        label_quantity='set_value',
        a_eln={'hide': ['set_value', 'set_time']},
    )
    value = Quantity(
        type=np.float64,
        description='The observed current density as a function of time.',
        shape=['*'],
        unit='ampere/meter**2',
    )


class ScanTimeSeries(TimeSeries):
    m_def = Section(
        label_quantity='set_value',
        a_eln={'hide': ['set_value', 'set_time']},
    )
    value = Quantity(
        type=np.float64,
        description='The observed scan as a function of time.',
        shape=['*'],
    )


class VoltageTimeSeries(TimeSeries):
    m_def = Section(
        label_quantity='set_value',
        a_eln={'hide': ['set_value', 'set_time']},
    )
    value = Quantity(
        type=np.float64,
        description='The observed voltage as a function of time.',
        shape=['*'],
        unit='volt',
    )


class ElectrolyteSolution(Solution):
    m_def = Section(
        links=['https://w3id.org/nfdi4cat/voc4cat_0007206'],
        categories=[INLCharacterizationCategory],
    )
    molar_concentration = Quantity(
        type=np.float64,
        description='Concentration of the electrolyte',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mole/liter',
        ),
        unit='mole/m**3',
    )
    molal_concentration = Quantity(
        type=np.float64,
        description='Concentration of the electrolyte',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mole/kg',
        ),
        unit='mole/kg',
    )


class WorkingElectrode(INLThinFilmStack, EntryData):
    m_def = Section(
        links=['https://w3id.org/nfdi4cat/voc4cat_0007206'],
        categories=[INLCharacterizationCategory],
        a_eln={'hide': ['name', 'datetime', 'ID', 'description']},
    )
    area_electrode = Quantity(
        type=np.float64,
        description='Area of the electrode',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='centimeter**2',
        ),
        unit='meter**2',
    )


class ChronoamperometryMeasurement(INLCharacterization, PlotSection):
    m_def = Section(
        links=['https://w3id.org/nfdi4cat/voc4cat_0007206'],
        categories=[INLCharacterizationCategory],
        label='INL Chronoamperometry',
    )
    area_electrode = Quantity(
        type=np.float64,
        description='Area of the electrode',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='centimeter**2',
        ),
        unit='meter**2',
    )
    voltage_applied = Quantity(
        type=np.float64,
        description='Voltage applied to the electrode',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
        unit='V',
    )
    current = SubSection(section_def=CurrentTimeSeries)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        self.figures = []
        y_current = np.array(self.current.value) * 1000
        x_time = self.current.time
        y_label = 'Current (mA)'
        if self.area_electrode is not None:
            y_current /= self.area_electrode
            y_label = 'Current density (mA cm' + r'$^{-2}$' + ')'
        first_line = px.scatter(x=x_time, y=y_current)
        figure1 = make_subplots(rows=1, cols=1)
        figure1.add_trace(first_line.data[0], row=1, col=1)
        figure1.update_layout(
            template='plotly_white',
            height=400,
            width=716,
            xaxis_title='Time (s)',
            yaxis_title=y_label,
            title_text='ED curve',
        )
        self.figures.append(
            PlotlyFigure(label='figure 1', figure=figure1.to_plotly_json())
        )


class PotentiostatMeasurement(INLCharacterization, PlotSection):
    m_def = Section(
        links=['https://w3id.org/nfdi4cat/voc4cat_0007206'],
        categories=[INLCharacterizationCategory],
        label='INL Cyclic Voltammetry',
    )
    area_electrode = Quantity(
        type=np.float64,
        description='Area of the electrode',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='centimeter**2',
        ),
        unit='meter**2',
    )
    rate = Quantity(
        type=np.float64,
        description='Rate of the CV measurement',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='millivolt/second',
        ),
        unit='volt/second',
    )
    current = SubSection(section_def=CurrentTimeSeries)
    voltage = SubSection(section_def=VoltageTimeSeries)
    scan = SubSection(section_def=ScanTimeSeries)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        self.figures = []
        scan_plotted = 3.0
        scan = np.array(self.scan.value)
        voltage = np.array(self.voltage.value)
        current = np.array(self.current.value) * 1000
        x_voltage = voltage[scan == scan_plotted]
        y_current = current[scan == scan_plotted]
        y_label = 'Current (mA)'
        if self.area_electrode is not None:
            y_current /= self.area_electrode
            y_label = 'Current density (mA cm' + r'$^{-2}$' + ')'
        if np.isnan(y_current).all():
            scan_plotted = 2.0
            x_voltage = voltage[scan == scan_plotted]
            y_current = current[scan == scan_plotted]
        first_line = px.scatter(x=x_voltage, y=y_current)
        figure1 = make_subplots(rows=1, cols=1)
        figure1.add_trace(first_line.data[0], row=1, col=1)
        figure1.update_layout(
            template='plotly_white',
            height=400,
            width=716,
            xaxis_title='Voltage (V)',
            yaxis_title=y_label,
            title_text='CV curve, scan ' + str(int(scan_plotted)),
        )
        self.figures.append(
            PlotlyFigure(label='figure 1', figure=figure1.to_plotly_json())
        )


# ---------------------------------------------------------------------------
# 4-Point Probe Sheet Resistance
# ---------------------------------------------------------------------------


class INLFourPointProbe(INLCharacterization, PlotSection):
    """Sheet resistance and resistivity map measured by a 4-point probe system."""

    m_def = Section(
        label='INL 4-Point Probe',
        categories=[INLCharacterizationCategory],
        a_eln=dict(
            hide=[
                'lab_id',
                'location',
                'steps',
                'instruments',
                'lot_id',
                'data_file_name',
                'thickness',
                'sample_material',
                'material_resistivity',
            ]
        ),
    )

    # --- Hidden metadata (parsed but not shown in ELN) ---
    lot_id = Quantity(
        type=str,
        description='Lot ID from the instrument header.',
    )
    data_file_name = Quantity(
        type=str,
        description='Data file name reported by the instrument.',
    )
    thickness = Quantity(
        type=np.float64,
        description='Substrate/film thickness as reported in the instrument header.',
        unit='m',
    )
    sample_material = Quantity(
        type=str,
        description='Sample material identifier from the instrument header.',
    )
    material_resistivity = Quantity(
        type=np.float64,
        description='Reference material bulk resistivity from the instrument header.',
        unit='ohm*m',
    )

    # --- Visible metadata ---
    x_size = Quantity(
        type=np.float64,
        description='Wafer / sample X dimension.',
        unit='m',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mm',
        ),
    )
    y_size = Quantity(
        type=np.float64,
        description='Wafer / sample Y dimension.',
        unit='m',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mm',
        ),
    )
    exclusion_size = Quantity(
        type=np.float64,
        description='Edge exclusion zone.',
        unit='m',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mm',
        ),
    )
    correction_factor = Quantity(
        type=np.float64,
        description='Geometric correction factor F applied by the instrument.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    probe_spacing = Quantity(
        type=np.float64,
        description='Distance between adjacent probe tips.',
        unit='m',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mm',
        ),
    )
    temperature_coefficient = Quantity(
        type=np.float64,
        description='Temperature coefficient of resistance used for correction.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    measurement_temperature = Quantity(
        type=np.float64,
        description='Temperature at which the measurement was performed.',
        unit='K',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='degC',
        ),
    )
    reference_temperature = Quantity(
        type=np.float64,
        description='Reference temperature for resistance correction.',
        unit='K',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='degC',
        ),
    )
    measurement_mode = Quantity(
        type=str,
        description='Measurement mode used by the instrument (e.g. SetPoint).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    # --- Analysis summary (machine-computed statistics) ---
    sigma_3_max = Quantity(
        type=np.float64,
        description='3-Sigma upper bound of sheet resistance [ohm/sq].',
        unit='ohm',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ohm',
        ),
    )
    sigma_3_min = Quantity(
        type=np.float64,
        description='3-Sigma lower bound of sheet resistance [ohm/sq].',
        unit='ohm',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ohm',
        ),
    )
    sheet_resistance_max = Quantity(
        type=np.float64,
        description='Maximum sheet resistance across all measurement points [ohm/sq].',
        unit='ohm',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ohm',
        ),
    )
    sheet_resistance_min = Quantity(
        type=np.float64,
        description='Minimum sheet resistance across all measurement points [ohm/sq].',
        unit='ohm',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ohm',
        ),
    )
    sheet_resistance_ave = Quantity(
        type=np.float64,
        description='Mean sheet resistance across all measurement points [ohm/sq].',
        unit='ohm',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ohm',
        ),
    )
    sheet_resistance_std_dev = Quantity(
        type=np.float64,
        description='Standard deviation of sheet resistance [ohm/sq].',
        unit='ohm',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ohm',
        ),
    )
    uniformity_pct = Quantity(
        type=np.float64,
        description='Uniformity Uni(%) as reported by the instrument.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    sheet_resistance_range = Quantity(
        type=np.float64,
        description='Max-Min range of sheet resistance [ohm/sq].',
        unit='ohm',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ohm',
        ),
    )
    std_dev_over_ave_pct = Quantity(
        type=np.float64,
        description='StDev/Ave(%) as reported by the instrument.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    # --- Per-point measurement arrays ---
    x_position = Quantity(
        type=np.float64,
        shape=['*'],
        description='X coordinate of each measurement point.',
        unit='m',
        a_eln=ELNAnnotation(defaultDisplayUnit='mm'),
    )
    y_position = Quantity(
        type=np.float64,
        shape=['*'],
        description='Y coordinate of each measurement point.',
        unit='m',
        a_eln=ELNAnnotation(defaultDisplayUnit='mm'),
    )
    sheet_resistance = Quantity(
        type=np.float64,
        shape=['*'],
        description='Sheet resistance at each measurement point [ohm/sq].',
        unit='ohm',
        a_eln=ELNAnnotation(defaultDisplayUnit='ohm'),
    )
    resistivity = Quantity(
        type=np.float64,
        shape=['*'],
        description='Resistivity at each measurement point [ohm·cm in source, stored as ohm·m].',
        unit='ohm*m',
        a_eln=ELNAnnotation(
            defaultDisplayUnit='ohm*cm',
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        self.figures = []

        if (
            self.x_position is None
            or self.y_position is None
            or self.sheet_resistance is None
        ):
            return

        x_mm = np.array(self.x_position) * 1e3
        y_mm = np.array(self.y_position) * 1e3
        rs = np.array(self.sheet_resistance)

        import plotly.graph_objects as go

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=x_mm,
                y=y_mm,
                mode='markers',
                marker=dict(
                    size=14,
                    color=rs,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title='Rs (ohm/sq)'),
                ),
                text=[f'Rs = {v:.5f} ohm/sq' for v in rs],
                hovertemplate='X: %{x:.1f} mm<br>Y: %{y:.1f} mm<br>%{text}<extra></extra>',
            )
        )
        fig.update_layout(
            template='plotly_white',
            height=480,
            width=520,
            xaxis_title='X (mm)',
            yaxis_title='Y (mm)',
            yaxis=dict(scaleanchor='x', scaleratio=1),
            title='Sheet Resistance Map',
        )
        self.figures.append(
            PlotlyFigure(label='Sheet Resistance Map', figure=fig.to_plotly_json())
        )


# ---------------------------------------------------------------------------
# KLA-Tencor Stylus Profiler
# ---------------------------------------------------------------------------


class INLKLATencorProfiler(INLCharacterization):
    """Stylus profilometry measurement from the KLA-Tencor P-series profiler."""

    m_def = Section(
        label='INL KLA-Tencor Profiler',
        categories=[INLCharacterizationCategory],
        a_eln=dict(
            hide=['lab_id', 'location', 'steps', 'instruments'],
        ),
    )

    # --- Primary results ---
    step_height = Quantity(
        type=np.float64,
        description='Step height (St Height) measured between left and right cursor regions.',
        unit='m',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='angstrom',
        ),
    )
    Ra = Quantity(
        type=np.float64,
        description='Average roughness (Ra) over the roughness trace.',
        unit='m',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='angstrom',
        ),
    )
    max_Ra = Quantity(
        type=np.float64,
        description='Maximum Ra over the roughness trace.',
        unit='m',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='angstrom',
        ),
    )
    Rq = Quantity(
        type=np.float64,
        description='RMS roughness (Rq) over the roughness trace.',
        unit='m',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='angstrom',
        ),
    )
    Rh = Quantity(
        type=np.float64,
        description='Roughness height (Rh) — peak-to-valley height over the roughness trace.',
        unit='m',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='angstrom',
        ),
    )

    # --- Scan parameters ---
    recipe = Quantity(
        type=str,
        description='Recipe name used for the measurement.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    site_name = Quantity(
        type=str,
        description='Site name recorded by the instrument.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    scan_length = Quantity(
        type=np.float64,
        description='Total scan length.',
        unit='m',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='um',
        ),
    )
    scan_speed = Quantity(
        type=np.float64,
        description='Stylus scan speed.',
        unit='m/s',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='um/s',
        ),
    )
    sample_rate = Quantity(
        type=np.float64,
        description='Data acquisition rate.',
        unit='Hz',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='Hz',
        ),
    )
    scan_direction = Quantity(
        type=str,
        description='Scan direction as reported by the instrument.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    repeats = Quantity(
        type=int,
        description='Number of scan repeats.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    stylus_force = Quantity(
        type=np.float64,
        description='Stylus contact force.',
        unit='kg',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mg',
        ),
    )
    noise_filter = Quantity(
        type=np.float64,
        description='Noise filter wavelength cut-off.',
        unit='m',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='um',
        ),
    )


m_package.__init_metainfo__()
