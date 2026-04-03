from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

import numpy as np
import plotly.express as px
from nomad.datamodel.data import EntryData, EntryDataCategory
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import CompositeSystemReference, Measurement
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.metainfo import Category, Quantity, SchemaPackage, Section, SubSection
from nomad_material_processing.general import TimeSeries
from nomad_material_processing.solution.general import Solution
from nomad_measurements.transmission.schema import ELNUVVisNirTransmission
from nomad_measurements.xrd.schema import ELNXRayDiffraction
from plotly.subplots import make_subplots

from nomad_inl_base.schema_packages.entities import INLSample, INLThinFilmStack

m_package = SchemaPackage()


class INLCharacterizationCategory(EntryDataCategory):
    m_def = Category(label='INL Characterization', categories=[EntryDataCategory])


class INLSampleReference(CompositeSystemReference):
    m_def = Section(hide=['name', 'lab_id'])
    reference = Quantity(
        type=INLSample,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Sample',
        ),
    )


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


m_package.__init_metainfo__()
