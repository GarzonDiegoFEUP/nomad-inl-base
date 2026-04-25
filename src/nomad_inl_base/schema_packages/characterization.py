from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

import numpy as np
import plotly.express as px
from nomad.datamodel.data import ArchiveSection, EntryData, EntryDataCategory
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import Measurement, MeasurementResult
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.metainfo import (
    Category,
    Quantity,
    SchemaPackage,
    Section,
    SubSection,
)
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


class INLFourPointProbeResults(MeasurementResult, PlotSection):
    """Statistics and per-point map for a single 4-point probe measurement run."""

    m_def = Section(label='4PP Results')

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


class INLFourPointProbe(INLCharacterization):
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

    results = SubSection(section_def=INLFourPointProbeResults, repeats=True)


# ---------------------------------------------------------------------------
# KLA-Tencor Stylus Profiler
# ---------------------------------------------------------------------------


class INLKLATencorProfilerResults(MeasurementResult):
    """Primary measurement results from a KLA-Tencor profilometry run."""

    m_def = Section(label='Profiler Results')

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


class INLKLATencorProfiler(INLCharacterization):
    """Stylus profilometry measurement from the KLA-Tencor P-series profiler."""

    m_def = Section(
        label='INL KLA-Tencor Profiler',
        categories=[INLCharacterizationCategory],
        a_eln=dict(
            hide=['lab_id', 'location', 'steps', 'instruments'],
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

    results = SubSection(section_def=INLKLATencorProfilerResults, repeats=True)


# ---------------------------------------------------------------------------
# External Quantum Efficiency (EQE)
# ---------------------------------------------------------------------------


class EQEResult(MeasurementResult):
    """Scalar parameters extracted from an EQE measurement."""

    jsc = Quantity(
        type=np.float64,
        description='Short-circuit current density from EQE integration (AM1.5G).',
        unit='milliampere/centimeter**2',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='milliampere/centimeter**2',
        ),
    )
    bandgap = Quantity(
        type=np.float64,
        description='Bandgap estimated from EQE.',
        unit='eV',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='eV',
        ),
    )
    device_id = Quantity(
        type=str,
        description='Device identifier.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    chopping_frequency = Quantity(
        type=np.float64,
        description='Chopping frequency used during EQE measurement.',
        unit='hertz',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='hertz',
        ),
    )
    light_bias_current = Quantity(
        type=np.float64,
        description='Light bias current.',
        unit='milliampere',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='milliampere',
        ),
    )
    voltage_bias = Quantity(
        type=np.float64,
        description='Voltage bias applied during measurement.',
        unit='volt',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='volt',
        ),
    )


class INLEQE(INLCharacterization, PlotSection):
    m_def = Section(
        label='INL EQE',
        categories=[INLCharacterizationCategory],
    )
    wavelength = Quantity(
        type=np.float64,
        description='Wavelength values.',
        shape=['*'],
        unit='nanometer',
    )
    quantum_efficiency = Quantity(
        type=np.float64,
        description='Quantum efficiency values (fraction, 0–1).',
        shape=['*'],
    )
    results = SubSection(section_def=EQEResult, repeats=True)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        import json

        import plotly.graph_objects as go
        import plotly.io as pio

        super().normalize(archive, logger)
        self.figures = []
        if self.wavelength is not None and self.quantum_efficiency is not None:
            wl_arr = np.array(self.wavelength)  # already in nm (unit='nanometer')
            qe_arr = np.array(self.quantum_efficiency) * 100  # fraction → %
            wl = [None if not np.isfinite(v) else float(v) for v in wl_arr]
            qe = [None if not np.isfinite(v) else float(v) for v in qe_arr]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=wl, y=qe, mode='lines', name='EQE'))
            fig.update_layout(
                template='plotly_white',
                height=400,
                width=716,
                xaxis_title='Wavelength (nm)',
                yaxis_title='EQE (%)',
                title_text='External Quantum Efficiency',
                dragmode='zoom',
                xaxis=dict(fixedrange=False),
                yaxis=dict(fixedrange=False),
            )
            self.figures.append(
                PlotlyFigure(label='EQE', figure=json.loads(pio.to_json(fig)))
            )


# ---------------------------------------------------------------------------
# Solar Cell IV
# ---------------------------------------------------------------------------


class SolarCellIVResult(MeasurementResult):
    """Extracted parameters for a single cell measurement."""

    measurement_name = Quantity(
        type=str,
        description='Name identifying this measurement.',
    )
    voc = Quantity(type=np.float64, description='Open-circuit voltage.', unit='volt')
    isc = Quantity(type=np.float64, description='Short-circuit current.', unit='ampere')
    jsc = Quantity(
        type=np.float64,
        description='Short-circuit current density.',
        unit='milliampere/centimeter**2',
    )
    vmax = Quantity(
        type=np.float64,
        description='Voltage at maximum power.',
        unit='volt',
    )
    imax = Quantity(
        type=np.float64,
        description='Current at maximum power.',
        unit='ampere',
    )
    pmax = Quantity(
        type=np.float64,
        description='Maximum power.',
        unit='milliwatt',
    )
    fill_factor = Quantity(
        type=np.float64,
        description='Fill factor (fraction, 0–1).',
    )
    efficiency = Quantity(
        type=np.float64,
        description='Power conversion efficiency (fraction, 0–1).',
    )
    cell_area = Quantity(
        type=np.float64,
        description='Active cell area calculated from Isc / Jsc.',
        unit='centimeter**2',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='centimeter**2',
        ),
    )
    r_shunt = Quantity(
        type=np.float64,
        description='Area-normalised shunt resistance (R_at_Isc × cell_area).',
        unit='ohm * centimeter**2',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ohm * centimeter**2',
        ),
    )
    r_at_voc = Quantity(
        type=np.float64,
        description='Differential resistance measured at open-circuit voltage (≈ series resistance).',
        unit='ohm',
    )
    r_at_isc = Quantity(
        type=np.float64,
        description='Differential resistance measured at short-circuit current (≈ shunt resistance).',
        unit='ohm',
    )
    r_series = Quantity(
        type=np.float64,
        description='Area-normalised series resistance (R_at_Voc × cell_area).',
        unit='ohm * centimeter**2',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ohm * centimeter**2',
        ),
    )
    exposure = Quantity(
        type=np.float64,
        description='Illumination exposure time.',
        unit='second',
    )
    datetime = Quantity(
        type=str,
        description='Date and time of the measurement.',
    )


class SolarCellIVCurve(ArchiveSection):
    """I-V curve data for a single cell measurement."""

    measurement_name = Quantity(
        type=str,
        description='Name identifying this measurement.',
    )
    voltage = Quantity(
        type=np.float64,
        description='Measured voltage.',
        shape=['*'],
        unit='volt',
    )
    current = Quantity(
        type=np.float64,
        description='Measured current.',
        shape=['*'],
        unit='ampere',
    )


class INLSolarCellIV(INLCharacterization, PlotSection):
    m_def = Section(
        label='INL Solar Cell IV',
        categories=[INLCharacterizationCategory],
    )
    results = SubSection(section_def=SolarCellIVResult, repeats=True)
    iv_curves = SubSection(section_def=SolarCellIVCurve, repeats=True)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        import json

        import plotly.graph_objects as go
        import plotly.io as pio

        super().normalize(archive, logger)
        self.figures = []

        # Plot best-cell JV curve (highest efficiency)
        if self.iv_curves:
            best_idx = 0
            if self.results:
                effs = [
                    r.efficiency if r.efficiency is not None else 0.0
                    for r in self.results
                ]
                best_idx = int(np.argmax(effs))
                if best_idx >= len(self.iv_curves):
                    best_idx = 0

            curve = self.iv_curves[best_idx]
            if curve.voltage is not None and curve.current is not None:
                v_arr = np.array(curve.voltage)  # volts

                # Look up cell area from matching result for mA/cm² conversion
                area_cm2 = None
                if self.results:
                    matching = next(
                        (r for r in self.results if r.measurement_name == curve.measurement_name),
                        None,
                    )
                    if matching is None and best_idx < len(self.results):
                        matching = self.results[best_idx]
                    if matching is not None and matching.cell_area is not None:
                        area_cm2 = float(
                            matching.cell_area.to('centimeter**2').magnitude
                        )

                if area_cm2 and area_cm2 > 0:
                    # Convert A → mA/cm²
                    j_arr = np.array(curve.current) * 1000.0 / area_cm2
                    y_label = 'Current Density (mA/cm²)'
                else:
                    # Fallback: plot in mA
                    j_arr = np.array(curve.current) * 1000.0
                    y_label = 'Current (mA)'

                v = [None if not np.isfinite(x) else float(x) for x in v_arr]
                j = [None if not np.isfinite(x) else float(x) for x in j_arr]
                label = curve.measurement_name or 'Best cell'
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=v, y=j, mode='lines', name=label))
                fig.update_layout(
                    template='plotly_white',
                    height=400,
                    width=716,
                    xaxis_title='Voltage (V)',
                    yaxis_title=y_label,
                    title_text=f'JV Curve — {label}',
                    dragmode='zoom',
                    xaxis=dict(fixedrange=False),
                    yaxis=dict(fixedrange=False),
                )
                self.figures.append(
                    PlotlyFigure(label='Best JV', figure=json.loads(pio.to_json(fig)))
                )

        # Boxplots of key parameters
        if self.results and len(self.results) > 1:
            params = {
                'Voc (V)': [
                    r.voc.to('volt').magnitude
                    for r in self.results
                    if r.voc is not None
                ],
                'Jsc (mA/cm²)': [
                    r.jsc.to('milliampere/centimeter**2').magnitude
                    for r in self.results
                    if r.jsc is not None
                ],
                'Fill Factor': [
                    r.fill_factor for r in self.results if r.fill_factor is not None
                ],
                'Efficiency': [
                    r.efficiency for r in self.results if r.efficiency is not None
                ],
            }
            fig = make_subplots(rows=1, cols=4, subplot_titles=list(params.keys()))
            for col_idx, (name, vals) in enumerate(params.items(), start=1):
                if vals:
                    fig.add_trace(
                        go.Box(y=vals, name=name, boxmean=True),
                        row=1,
                        col=col_idx,
                    )
            fig.update_layout(
                template='plotly_white',
                height=400,
                width=900,
                showlegend=False,
                title_text='Solar Cell Parameters',
            )
            self.figures.append(
                PlotlyFigure(label='Parameters', figure=json.loads(pio.to_json(fig)))
            )


# ---------------------------------------------------------------------------
# GDOES (Glow Discharge Optical Emission Spectroscopy)
# ---------------------------------------------------------------------------


class GDOESElementProfile(ArchiveSection):
    """Concentration profile for a single element."""

    element_name = Quantity(
        type=str,
        description='Element label as it appears in the data file header.',
    )
    concentration = Quantity(
        type=np.float64,
        description='Concentration values (mol %).',
        shape=['*'],
    )


class INLGDOES(INLCharacterization, PlotSection):
    m_def = Section(
        label='INL GDOES',
        categories=[INLCharacterizationCategory],
    )
    depth = Quantity(
        type=np.float64,
        description='Depth profile values.',
        shape=['*'],
        unit='micrometer',
    )
    element_profiles = SubSection(section_def=GDOESElementProfile, repeats=True)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        self.figures = []
        if self.depth is not None and self.element_profiles:
            import json

            import plotly.graph_objects as go
            import plotly.io as pio

            # self.depth is in µm (schema unit='micrometer', returned as-is)
            depth_arr = np.array(self.depth)
            # Use None for non-finite values so plotly renders them as gaps
            # (avoids NaN in JSON which crashes the browser renderer)
            depth = [None if not np.isfinite(v) else float(v) for v in depth_arr]
            fig = go.Figure()
            for profile in self.element_profiles:
                if profile.concentration is not None:
                    conc_arr = np.array(profile.concentration)
                    n = min(len(depth), len(conc_arr))
                    conc = [
                        None if not np.isfinite(v) else float(v)
                        for v in conc_arr[:n]
                    ]
                    fig.add_trace(
                        go.Scatter(
                            x=depth[:n],
                            y=conc,
                            mode='lines',
                            name=profile.element_name or 'Unknown',
                            hovertemplate=(
                                '<b>%{fullData.name}</b><br>'
                                'Depth: %{x:.4f} µm<br>'
                                'Concentration: %{y:.2f} mol %<extra></extra>'
                            ),
                        )
                    )
            fig.update_layout(
                template='plotly_white',
                height=400,
                width=716,
                xaxis_title='Depth (µm)',
                yaxis_title='Concentration (mol %)',
                title_text='GDOES Depth Profile',
                dragmode='zoom',
                xaxis=dict(fixedrange=False),
                yaxis=dict(fixedrange=False),
                showlegend=True,
                legend=dict(
                    title='Elements',
                    itemclick='toggle',
                    itemdoubleclick='toggleothers',
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='lightgrey',
                    borderwidth=1,
                ),
            )
            # Use pio.to_json + json.loads to guarantee a JSON-safe dict
            # (handles NaN/Inf that would otherwise break browser JS)
            self.figures.append(
                PlotlyFigure(
                    label='Depth Profile',
                    figure=json.loads(pio.to_json(fig)),
                )
            )


# ---------------------------------------------------------------------------
# SEM (Scanning Electron Microscopy)
# ---------------------------------------------------------------------------


class INLSEMImage(MeasurementResult, PlotSection):
    """Single SEM image with acquisition metadata parsed from FEI/TFS TIFF tag 34682."""

    m_def = Section(label='SEM Image')

    file_name = Quantity(
        type=str,
        description='File name of this image within the uploaded ZIP.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    label = Quantity(
        type=str,
        description='User annotation for this image.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    image_array = Quantity(
        type=np.uint8,
        shape=['*', '*'],
        description='Grayscale pixel data (data bar cropped, downsampled to ≤1024 px for storage).',
    )
    width_pixels = Quantity(
        type=np.int64,
        description='Image width in pixels (Image/ResolutionX).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    height_pixels = Quantity(
        type=np.int64,
        description='Image height in pixels (Image/ResolutionY).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    accelerating_voltage = Quantity(
        type=np.float64,
        description='Accelerating voltage (EBeam/HV).',
        unit='volt',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='kilovolt',
        ),
    )
    magnification = Quantity(
        type=np.float64,
        description='Nominal magnification (Image/MagCanvasRealWidth / EBeam/HFW).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    horizontal_field_width = Quantity(
        type=np.float64,
        description='Physical width of the full image (EBeam/HFW).',
        unit='meter',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='micrometer',
        ),
    )
    pixel_width = Quantity(
        type=np.float64,
        description='Physical width of one pixel (Scan/PixelWidth).',
        unit='meter',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='nanometer',
        ),
    )
    working_distance = Quantity(
        type=np.float64,
        description='Working distance (EBeam/WD).',
        unit='meter',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='millimeter',
        ),
    )
    detector_name = Quantity(
        type=str,
        description='Detector name (Detectors/Name), e.g. ETD, CBS.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    detector_mode = Quantity(
        type=str,
        description='Detector signal mode (Detectors/Mode), e.g. SE, BSE.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    emission_current = Quantity(
        type=np.float64,
        description='Source emission current (EBeam/EmissionCurrent).',
        unit='ampere',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='microampere',
        ),
    )
    dwell_time = Quantity(
        type=np.float64,
        description='Pixel dwell time (Scan/Dwelltime).',
        unit='second',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='microsecond',
        ),
    )
    stage_x = Quantity(
        type=np.float64,
        description='Stage X position (Stage/StageX).',
        unit='meter',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='millimeter',
        ),
    )
    stage_y = Quantity(
        type=np.float64,
        description='Stage Y position (Stage/StageY).',
        unit='meter',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='millimeter',
        ),
    )
    stage_z = Quantity(
        type=np.float64,
        description='Stage Z position (Stage/StageZ).',
        unit='meter',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='millimeter',
        ),
    )
    stage_tilt = Quantity(
        type=np.float64,
        description='Stage tilt angle in radians (Stage/StageT).',
        unit='radian',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='degree',
        ),
    )
    acquisition_datetime = Quantity(
        type=str,
        description='Date and time of image acquisition (User/Date + User/Time).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    operator = Quantity(
        type=str,
        description='Operator username (User/User).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        self.figures = []
        if self.image_array is None:
            return
        arr = np.array(self.image_array)
        h, w = arr.shape
        if self.pixel_width is not None:
            pw_um = self.pixel_width.to('micrometer').magnitude
            x_um = np.linspace(0.0, w * pw_um, w, endpoint=False)
            y_um = np.linspace(0.0, h * pw_um, h, endpoint=False)
            fig = px.imshow(
                arr,
                x=x_um,
                y=y_um,
                labels={'x': 'x (µm)', 'y': 'y (µm)', 'color': 'Intensity'},
                color_continuous_scale='gray',
                aspect='equal',
            )
        else:
            fig = px.imshow(arr, color_continuous_scale='gray', aspect='equal')
        det = self.detector_name or 'SEM'
        mag_str = f' ×{int(self.magnification):,}' if self.magnification else ''
        hfw_str = (
            f'  HFW={self.horizontal_field_width.to("micrometer").magnitude:.2f} µm'
            if self.horizontal_field_width
            else ''
        )
        kv_str = (
            f'  {self.accelerating_voltage.to("kilovolt").magnitude:.0f} kV'
            if self.accelerating_voltage
            else ''
        )
        fig.update_layout(
            template='plotly_white',
            height=500,
            width=716,
            title_text=f'{det}{mag_str}{hfw_str}{kv_str}',
            coloraxis_showscale=False,
        )
        lbl = self.label or self.file_name or 'SEM Image'
        self.figures.append(PlotlyFigure(label=lbl, figure=fig.to_plotly_json()))


class INLSEMSession(INLCharacterization, PlotSection):
    """SEM session: one or more images acquired during a single microscope session."""

    m_def = Section(
        label='INL SEM Session',
        categories=[INLCharacterizationCategory],
    )

    microscope_model = Quantity(
        type=str,
        description='Microscope model (System/SystemType), e.g. "Quanta FEG".',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    source_type = Quantity(
        type=str,
        description='Electron source type (System/Source), e.g. "FEG".',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    raw_dir = Quantity(
        type=str,
        description=(
            'Path to the directory containing the source TIFF files, '
            'relative to the upload raw root. Set by the parser; used by '
            'normalize to load pixel data without storing arrays in the archive.'
        ),
    )

    images = SubSection(section_def=INLSEMImage, repeats=True)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        # ----------------------------------------------------------------
        # Load pixel data from source TIFFs.
        # image_array is intentionally excluded from the sidecar YAML to
        # keep the file small.  We reload it here on every normalization
        # from the original TIFF files stored in the upload.
        # ----------------------------------------------------------------
        if self.raw_dir and self.images and hasattr(archive.m_context, 'raw_path'):
            import os

            from PIL import Image as _PilImage

            _MAX_PX = 1024
            raw_root = archive.m_context.raw_path()
            tif_dir = os.path.join(raw_root, self.raw_dir)
            for img in self.images:
                if img.file_name and os.path.isdir(tif_dir):
                    tif_path = os.path.join(tif_dir, img.file_name)
                    if os.path.exists(tif_path):
                        try:
                            res_x = int(img.width_pixels) if img.width_pixels is not None else None
                            res_y = int(img.height_pixels) if img.height_pixels is not None else None
                            with _PilImage.open(tif_path) as pil_img:
                                if res_x is None:
                                    res_x = pil_img.width
                                if res_y is None:
                                    res_y = pil_img.height
                                arr = np.array(pil_img.convert('L'))[:res_y, :res_x]
                            ih, iw = arr.shape
                            if max(ih, iw) > _MAX_PX:
                                scale = _MAX_PX / max(ih, iw)
                                new_h = max(1, int(ih * scale))
                                new_w = max(1, int(iw * scale))
                                arr = np.array(
                                    _PilImage.fromarray(arr).resize(
                                        (new_w, new_h), _PilImage.LANCZOS
                                    )
                                )
                            img.image_array = arr.astype(np.uint8)
                            # Also trigger per-image figure now that array is loaded
                            img.normalize(archive, logger)
                        except Exception as exc:
                            logger.warning(
                                f'INLSEMSession: could not load pixel data for {img.file_name}',
                                exc_info=exc,
                            )

        self.figures = []
        if not self.images:
            return
        import json

        import plotly.graph_objects as go
        import plotly.io as pio

        n = len(self.images)
        # One column, one row per image — compute per-image height to match aspect ratio
        PLOT_WIDTH = 716
        row_heights = []
        for img in self.images:
            if img.image_array is not None:
                arr = np.array(img.image_array)
                ih, iw = arr.shape
                row_heights.append(PLOT_WIDTH * ih / iw if iw > 0 else PLOT_WIDTH)
            else:
                row_heights.append(PLOT_WIDTH)

        subtitles = []
        for img in self.images:
            det = img.detector_name or 'SEM'
            mag_str = f' ×{int(img.magnification):,}' if img.magnification else ''
            hfw_str = (
                f'  HFW={img.horizontal_field_width.to("micrometer").magnitude:.1f} µm'
                if img.horizontal_field_width
                else ''
            )
            subtitles.append(f'{det}{mag_str}{hfw_str}')

        fig = make_subplots(
            rows=n,
            cols=1,
            subplot_titles=subtitles,
            row_heights=row_heights,
            vertical_spacing=0.02,
        )

        for idx, img in enumerate(self.images):
            if img.image_array is None:
                continue
            row = idx + 1
            arr = np.array(img.image_array)
            ih, iw = arr.shape

            if img.pixel_width is not None:
                pw_um = img.pixel_width.to('micrometer').magnitude
                x_um = np.linspace(0.0, iw * pw_um, iw, endpoint=False)
                y_um = np.linspace(0.0, ih * pw_um, ih, endpoint=False)
                heatmap = go.Heatmap(
                    z=arr,
                    x=x_um,
                    y=y_um,
                    colorscale='gray',
                    showscale=False,
                    name=subtitles[idx],
                )
                x_title = 'x (µm)'
                y_title = 'y (µm)'
            else:
                heatmap = go.Heatmap(
                    z=arr,
                    colorscale='gray',
                    showscale=False,
                    name=subtitles[idx],
                )
                x_title = 'x (px)'
                y_title = 'y (px)'

            fig.add_trace(heatmap, row=row, col=1)
            fig.update_xaxes(
                title_text=x_title,
                fixedrange=True,
                row=row,
                col=1,
            )
            fig.update_yaxes(
                title_text=y_title,
                autorange='reversed',
                fixedrange=True,
                scaleanchor=f'x{idx + 1 if idx > 0 else ""}',
                scaleratio=1,
                row=row,
                col=1,
            )

        total_height = int(sum(row_heights)) + 60 * n  # extra for titles
        fig.update_layout(
            template='plotly_white',
            height=total_height,
            width=PLOT_WIDTH,
            title_text='SEM Session Gallery',
            dragmode=False,
        )
        self.figures.append(
            PlotlyFigure(label='Gallery', figure=json.loads(pio.to_json(fig)))
        )


# ---------------------------------------------------------------------------
# EDX / EDS Spectrum (EMSA/MAS format)
# ---------------------------------------------------------------------------


class EDXSpectrumResult(MeasurementResult):
    """Raw spectral data from a single EDX/EDS acquisition."""

    m_def = Section(label='EDX Spectrum')

    energy_axis = Quantity(
        type=np.float64,
        shape=['*'],
        description='Energy axis values (one per channel).',
        unit='keV',
    )
    counts = Quantity(
        type=np.float64,
        shape=['*'],
        description='Raw X-ray counts per channel.',
    )


class INLEDXSpectrum(INLCharacterization, PlotSection):
    """EDX/EDS spectrum acquired in a SEM, stored as an EMSA/MAS text file."""

    m_def = Section(
        label='INL EDX Spectrum',
        categories=[INLCharacterizationCategory],
        a_eln=dict(hide=['lab_id', 'location', 'steps', 'instruments']),
    )

    # --- Acquisition parameters (from EMSA header) ---
    beam_energy = Quantity(
        type=np.float64,
        description='Accelerating voltage of the electron beam.',
        unit='keV',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='keV',
        ),
    )
    live_time = Quantity(
        type=np.float64,
        description='Detector live time during acquisition.',
        unit='second',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='s',
        ),
    )
    real_time = Quantity(
        type=np.float64,
        description='Real (clock) time during acquisition.',
        unit='second',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='s',
        ),
    )
    probe_current = Quantity(
        type=np.float64,
        description='Electron probe current.',
        unit='nA',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='nA',
        ),
    )
    magnification = Quantity(
        type=np.float64,
        description='SEM magnification at time of acquisition.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    tilt_angle = Quantity(
        type=np.float64,
        description='Stage X tilt angle.',
        unit='degree',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='degree',
        ),
    )
    elevation_angle = Quantity(
        type=np.float64,
        description='Detector elevation angle above the horizontal plane.',
        unit='degree',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='degree',
        ),
    )
    azimuth_angle = Quantity(
        type=np.float64,
        description='Detector azimuth angle.',
        unit='degree',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='degree',
        ),
    )
    x_stage_position = Quantity(
        type=np.float64,
        description='Stage X position at time of acquisition.',
        unit='mm',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mm',
        ),
    )
    y_stage_position = Quantity(
        type=np.float64,
        description='Stage Y position at time of acquisition.',
        unit='mm',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mm',
        ),
    )
    z_stage_position = Quantity(
        type=np.float64,
        description='Stage Z (working distance) position at time of acquisition.',
        unit='mm',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mm',
        ),
    )
    signal_type = Quantity(
        type=str,
        description='Signal type as reported in the EMSA header (e.g. EDS).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    n_channels = Quantity(
        type=int,
        description='Number of spectrum channels (NPOINTS).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    energy_per_channel = Quantity(
        type=np.float64,
        description='Energy width of each channel (XPERCHAN).',
        unit='keV',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='keV',
        ),
    )
    energy_offset = Quantity(
        type=np.float64,
        description='Energy offset of channel zero (OFFSET).',
        unit='keV',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='keV',
        ),
    )
    vendor_annotations = Quantity(
        type=str,
        description='Raw vendor-specific header lines (e.g. Oxford Instruments ##OXINST* keys) preserved for provenance.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.RichTextEditQuantity),
    )

    results = SubSection(section_def=EDXSpectrumResult, repeats=True)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        import json

        import plotly.graph_objects as go
        import plotly.io as pio

        super().normalize(archive, logger)
        self.figures = []
        if not self.results:
            return
        spectrum = self.results[0]
        if spectrum.energy_axis is None or spectrum.counts is None:
            return
        energy = [float(v) for v in np.array(spectrum.energy_axis)]
        counts = [float(v) for v in np.array(spectrum.counts)]
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=energy, y=counts, mode='lines', name='EDX spectrum')
        )
        fig.update_layout(
            template='plotly_white',
            height=400,
            width=716,
            xaxis_title='Energy (keV)',
            yaxis_title='Counts',
            title_text='EDX Spectrum',
            dragmode='zoom',
            xaxis=dict(fixedrange=False, range=[0, self.beam_energy.to('keV').magnitude * 1.1 if self.beam_energy else None]),
            yaxis=dict(fixedrange=False),
        )
        self.figures.append(
            PlotlyFigure(label='EDX Spectrum', figure=json.loads(pio.to_json(fig)))
        )


m_package.__init_metainfo__()
