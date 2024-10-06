from typing import (
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import (
        EntryArchive,
    )
    from structlog.stdlib import (
        BoundLogger,
    )

import numpy as np
import plotly.express as px
from nomad.config import config
from nomad.datamodel.data import EntryData
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import Measurement
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.metainfo import Quantity, SchemaPackage, Section, SubSection
from nomad_material_processing.general import (
    ThinFilmStack,
    TimeSeries,
)
from nomad_material_processing.solution.general import *
from plotly.subplots import make_subplots

configuration = config.get_plugin_entry_point(
    'nomad_inl_base.schema_packages:cyclic_voltammetry_entry_point'
)

m_package = SchemaPackage()


class CurrentTimeSeries(TimeSeries):
    m_def = Section(
        label_quantity='set_value',
        a_eln={
            'hide': [
                'set_value',
                'set_time',
            ]
        },
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
        a_eln={
            'hide': [
                'set_value',
                'set_time',
            ]
        },
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
        a_eln={
            'hide': [
                'set_value',
                'set_time',
            ]
        },
    )

    value = Quantity(
        type=np.float64,
        description='The observed scan as a function of time.',
        shape=['*'],
    )


class VoltageTimeSeries(TimeSeries):
    m_def = Section(
        label_quantity='set_value',
        a_eln={
            'hide': [
                'set_value',
                'set_time',
            ]
        },
    )

    value = Quantity(
        type=np.float64,
        description='The observed voltage as a function of time.',
        shape=['*'],
        unit='volt',
    )


class ChronoamperometryMeasurement(PlotSection, Measurement, EntryData):
    m_def = Section(
        links=['https://w3id.org/nfdi4cat/voc4cat_0007206'],
    )

    area_electrode = Quantity(
        type=np.float64,
        description='Area of the electrode ',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='centimeter**2',
        ),
        unit='meter**2',
    )

    Voltage_applied = Quantity(
        type=np.float64,
        description='Voltage applied to the electrode',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
        unit='V',
    )

    current = SubSection(section_def=CurrentTimeSeries)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super(ChronoamperometryMeasurement, self).normalize(archive, logger)

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

        logger.info('NewSchema.normalize', parameter=configuration.parameter)
        # self.message = f'Hello {self.name}!'


class PotentiostatMeasurement(PlotSection, Measurement, EntryData):
    m_def = Section(
        links=['https://w3id.org/nfdi4cat/voc4cat_0007206'],
    )

    # data_file = Quantity(
    #    type=str,
    #    a_eln=dict(component='FileEditQuantity'),
    #    a_browser=dict(adaptor='RawFileAdaptor'),
    # )

    area_electrode = Quantity(
        type=np.float64,
        description='Area of the electrode ',
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
        super(PotentiostatMeasurement, self).normalize(archive, logger)

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

        logger.info('NewSchema.normalize', parameter=configuration.parameter)
        # self.message = f'Hello {self.name}!'


class ElectrolyteSolution(Solution):
    m_def = Section(
        links=['https://w3id.org/nfdi4cat/voc4cat_0007206'],
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

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super(ElectrolyteSolution, self).normalize(archive, logger)

        logger.info('NewSchema.normalize', parameter=configuration.parameter)
        # self.message = f'Hello {self.name}!'


class WorkingElectrode(ThinFilmStack, EntryData):
    m_def = Section(
        links=['https://w3id.org/nfdi4cat/voc4cat_0007206'],
        a_eln={'hide': ['name', 'datetime', 'ID', 'description']},
    )

    area_electrode = Quantity(
        type=np.float64,
        description='Area of the electrode ',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='centimeter**2',
        ),
        unit='meter**2',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super(WorkingElectrode, self).normalize(archive, logger)

        logger.info('NewSchema.normalize', parameter=configuration.parameter)
        # self.message = f'Hello {self.name}!'


m_package.__init_metainfo__()
