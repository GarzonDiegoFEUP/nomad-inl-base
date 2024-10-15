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
from nomad.config import config
from nomad.datamodel.data import (
    EntryData,
    EntryDataCategory,
)

# from nomad.metainfo.metainfo import (
#    Category,
# )
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import (
    CompositeSystem,
    EntityReference,
    ReadableIdentifiers,
    SystemComponent,
)
from nomad.metainfo import (
    Category,
    Datetime,
    Quantity,
    SchemaPackage,
    Section,
    SubSection,
)
from nomad.units import ureg
from nomad_material_processing.general import (
    Geometry,
    RectangleCuboid,
    Substrate,
    SubstrateReference,
    ThinFilm,
    ThinFilmReference,
    ThinFilmStack,
    ThinFilmStackReference,
)
from nomad_material_processing.solution.general import *
from nomad_material_processing.vapor_deposition.general import (
    ChamberEnvironment,
    GasFlow,
    GrowthRate,
    Pressure,
    VolumetricFlowRate,
)
from nomad_material_processing.vapor_deposition.pvd.general import (
    PVDEvaporationSource,
    PVDSource,
    SampleParameters,
    SourcePower,
    VaporDepositionStep,
)
from nomad_material_processing.vapor_deposition.pvd.sputtering import SputterDeposition

from nomad_inl_base.utils import *

ORDER_RF_STEPS = [
    'creates_new_thin_film',
    'name',
    'chamber_pressure',
    'duration',
    'set_power',
    'power',
    'voltage',
    'Ct_value',
    'Cl_value',
    'comment',
]

ORDER_DC_STEPS = [
    'creates_new_thin_film',
    'name',
    'chamber_pressure',
    'duration',
    'set_voltage',
    'set_current',
    'voltage',
    'current',
    'set_power',
    'power',
    'comment',
]


configuration = config.get_plugin_entry_point(
    'nomad_inl_base.schema_packages:star_entry_point'
)

m_package = SchemaPackage()


class STARCategory(EntryDataCategory):
    m_def = Category(label='STAR', categories=[EntryDataCategory])


# Classes regarding the calibration
class StarCalibrationData(EntryData):
    m_def = Section(
        label='Calibration Data',
        categories=[STARCategory],
    )
    calibration_date = Quantity(
        type=Datetime,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.DateEditQuantity,
        ),
    )

    deposition_rate = Quantity(
        type=np.float64,
        description="""The deposition rate of the thin film (length/time).""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Deposition rate',
            defaultDisplayUnit='nm/minute',
        ),
        unit='meter/second',
    )
    calibration_experiment = Quantity(
        type=SputterDeposition,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        if self.calibration_experiment is not None:
            self.calibration_date = self.calibration_experiment.start_time
            for step in self.calibration_experiment:
                if step.creates_new_thin_film is not None:
                    if step.sample_parameters is not None:
                        if step.sample_parameters[0].deposition_rate is not None:
                            self.deposition_rate = step.sample_parameters[
                                0
                            ].deposition_rate
        logger.info(
            'NewSchema.normalize.StarCalibrationData', parameter=configuration.parameter
        )
        # self.message = f'Hello {self.name}!'


class StarCalibrationDataReference(EntityReference):
    m_def = Section(hide=['name', 'lab_id'])
    reference = Quantity(
        type=StarCalibrationData,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
        ),
    )


# classes regarding the Vapor Source


class Magnetron(PVDEvaporationSource):
    """
    A representation of the magnetron device.
    """

    m_def = Section(
        a_plot=dict(
            x='power/time',
            y='power/value',
        ),
    )

    power = SourcePower()

    Description = Quantity(
        type=str,
        a_eln=ELNAnnotation(
            component='RichTextEditQuantity',
        ),
    )


class SputteringTarget(CompositeSystem, EntryData):
    """
    A representation of the target material used in sputtering. It cointains the target
    ID, the delivery date and the actual date where the target was installed
    inside the chamber.
    """

    m_def = Section(
        categories=[STARCategory],
        a_eln={
            'hide': ['datetime'],
            'properties': SectionProperties(
                visible=Filter(exclude=['elemental_composition'])
            ),
        },
    )

    target_id = SubSection(
        section_def=ReadableIdentifiers,
    )

    geometry = SubSection(
        section_def=Geometry,
        description='Section containing the geometry of the target.',
    )

    delivery_date = Quantity(
        type=Datetime,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.DateEditQuantity,
        ),
    )

    installation_date = Quantity(
        type=Datetime,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.DateEditQuantity,
        ),
    )

    last_calibration_date = Quantity(
        type=Datetime,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.DateEditQuantity,
        ),
    )

    calibration_data = Quantity(
        type=StarCalibrationDataReference,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
        ),
    )

    old_calibration_data = Quantity(
        type=StarCalibrationDataReference,
        shape=['*'],
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.lab_id is not None and self.target_id is None:
            new_target_ID = ReadableIdentifiers()
            new_target_ID.institute = 'INL'
            new_target_ID.owner = 'LaNaSC'
            new_target_ID.lab_id = self.lab_id
            if self.delivery_date is not None:
                new_target_ID.datetime = self.delivery_date

            if self.name is not None:
                new_target_ID.short_name = self.name

            self.target_id = new_target_ID

            if self.calibration_data is not None:
                self.last_calibration_date = (
                    self.calibration_data.reference.calibration_date
                )
                if self.old_calibration_data is None:
                    self.old_calibration_data = []
                if self.calibration_data not in self.old_calibration_data:
                    self.old_calibration_data.append(self.calibration_data)

        logger.info(
            'NewSchema.normalize.SputteringTarget', parameter=configuration.parameter
        )
        # self.message = f'Hello {self.name}!'


class SputteringTargetComponent(SystemComponent):
    m_def = Section(a_eln={'hide': ['mass_fraction', 'mass']})

    lab_id = Quantity(
        type=str,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Target ID',
        ),
    )
    system = Quantity(
        type=SputteringTarget,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.system is not None:
            if self.system.target_id is not None:
                self.lab_id = self.system.target_id.lab_id

        logger.info(
            'NewSchema.normalize.SputteringTargetComponent',
            parameter=configuration.parameter,
        )
        # self.message = f'Hello {self.name}!'


class SputteringSource(PVDSource):
    """
    A representation of both the magentron and the target material, which works as
    a source of atoms for sputtering.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            hide=['name'],
            properties=SectionProperties(
                visible=Filter(exclude=['impinging_flux', 'vapor_molar_flow_rate'])
            ),
        ),
        links=['http://purl.obolibrary.org/obo/CHMO_0002896'],
    )

    vapor_source = SubSection(section_def=Magnetron, repeats=True)


# Classes regarding the chamber environment


class StarVolumetricFlowRate(VolumetricFlowRate):
    m_def = Section(a_eln={'hide': ['value', 'set_time']})

    measurement_type = Quantity(
        type=MEnum(
            'Mass Flow Controller',
            'Flow Meter',
            'Other',
        ),
        default='Mass Flow Controller',
    )


class StarGasFlow(GasFlow):
    name = Quantity(
        type=str,
        description="""The name of the gas used in the chamber.""",
        a_eln=ELNAnnotation(component='StringEditQuantity', label='Gas name'),
    )

    flow_rate = SubSection(
        section_def=StarVolumetricFlowRate,
    )


class StarPressure(Pressure):
    m_def = Section(a_eln={'hide': ['time', 'set_value', 'set_time']})

    value = Quantity(
        type=np.float64,
        shape=['*'],
        description="""The pressure in the chamber.""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Chamber pressure',
            defaultDisplayUnit='millibar',
        ),
        unit='pascal',
    )


class StarChamberEnvironment(ChamberEnvironment):
    m_def = Section(
        a_eln={'overview': True},
        label='Chamber Environment',
    )

    step_name = Quantity(
        type=str,
        description="""The name of the step.""",
        a_eln=ELNAnnotation(component='StringEditQuantity', label='Step name'),
    )

    pressure = SubSection(
        section_def=StarPressure,
    )

    chamber_pressure = Quantity(
        type=np.float64,
        description="""The pressure in the chamber.""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Chamber pressure',
            defaultDisplayUnit='millibar',
        ),
        unit='pascal',
    )

    gasses = Quantity(
        type=str,
        shape=['*'],
        description="""The gasses used in the chamber.""",
        a_eln=ELNAnnotation(component='StringEditQuantity', label='Gasses'),
    )

    gas_flow = SubSection(
        section_def=StarGasFlow,
        repeats=True,
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.pressure is not None:
            if self.pressure.value is not None:
                self.chamber_pressure = self.pressure.value[0]

        gasses_ = []
        for idx, gas in enumerate(self.gas_flow):
            if gas.gas is not None:
                gas.name = gas.gas.name
            if gas.flow_rate is not None:
                flow_rate = str(
                    round(gas.flow_rate.set_value[0].to('cm**3 / minute').magnitude, 1)
                )
                txt = gas.gas.name + ' (' + flow_rate + ' sccm)'
                gasses_.append(txt)

        self.gasses = gasses_

        logger.info(
            'NewSchema.normalize.StarChamberEnvironment',
            parameter=configuration.parameter,
        )
        # self.message = f'Hello {self.name}!'


# Classes regarding the Sputtering Process


##Steps
class StarStep(VaporDepositionStep):
    m_def = Section(a_eln=None)

    name = Quantity(
        type=str,
        description="""A general step for STAR processes.""",
        a_eln=ELNAnnotation(
            component='StringEditQuantity',
            label='Step name',
        ),
    )

    chamber_pressure = Quantity(
        type=np.float64,
        description="""The pressure in the chamber.""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Chamber pressure',
            defaultDisplayUnit='millibar',
        ),
        unit='pascal',
    )

    duration = Quantity(
        type=np.float64,
        description="""The duration of the step.""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Duration',
            defaultDisplayUnit='minute',
        ),
        unit='s',
    )

    voltage = Quantity(
        type=np.float64,
        description="""The voltage during the process.""",
        unit='V',
        a_eln=ELNAnnotation(component='NumberEditQuantity', label='Voltage'),
    )

    power = Quantity(
        type=np.float64,
        description="""The power during the process.""",
        unit='W',
        a_eln=ELNAnnotation(component='NumberEditQuantity', label='Power'),
    )

    environment = SubSection(
        section_def=StarChamberEnvironment,
        description="""The chamber enviroment for the sputtering process.""",
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.chamber_pressure is not None:
            if self.environment is None:
                environment_ = StarChamberEnvironment()
            else:
                environment_ = self.environment

            pressure_ = StarPressure()
            pressure_.value = [self.chamber_pressure]
            environment_.pressure = pressure_

            self.environment = environment_

        # if self.start_time is not None and self.start_time.tzinfo is not ZoneInfo('Europe/Lisbon'):
        #    self.start_time = self.start_time.replace(tzinfo=ZoneInfo('Europe/Lisbon'))

        logger.info('NewSchema.normalize.StarStep', parameter=configuration.parameter)
        # self.message = f'Hello {self.name}!'


class StarRFStep(StarStep):
    m_def = Section(
        label='StartRFStep',
        a_eln=ELNAnnotation(properties=SectionProperties(order=ORDER_RF_STEPS)),
    )

    set_power = Quantity(
        type=np.float64,
        description="""The set power during the process.""",
        unit='W',
        a_eln=ELNAnnotation(component='NumberEditQuantity', label='Set Power'),
    )

    Ct_value = Quantity(
        type=np.float64,
        description="""The Ct value during the process.""",
        a_eln=ELNAnnotation(component='NumberEditQuantity', label='Ct value'),
    )

    Cl_value = Quantity(
        type=np.float64,
        description="""The Cl value during the process.""",
        a_eln=ELNAnnotation(component='NumberEditQuantity', label='Cl value'),
    )


class StarDCStep(StarStep):
    m_def = Section(
        label='StartDCStep',
        a_eln=ELNAnnotation(properties=SectionProperties(order=ORDER_DC_STEPS)),
    )

    current = Quantity(
        type=np.float64,
        description="""The current during the process.""",
        unit='A',
        a_eln=ELNAnnotation(component='NumberEditQuantity', label='Current'),
    )

    set_current = Quantity(
        type=np.float64,
        description="""The set current during the process.""",
        unit='A',
        a_eln=ELNAnnotation(component='NumberEditQuantity', label='Set Current'),
    )

    set_voltage = Quantity(
        type=np.float64,
        description="""The set voltage during the process.""",
        unit='V',
        a_eln=ELNAnnotation(component='NumberEditQuantity', label='Set Voltage'),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.set_voltage is not None and self.set_current is not None:
            self.set_power = self.set_voltage * self.set_current

        if self.voltage is not None and self.current is not None:
            self.power = self.voltage * self.current

        logger.info('NewSchema.normalize.StarDCStep', parameter=configuration.parameter)
        # self.message = f'Hello {self.name}!'


class PresputteringRFStep(StarRFStep):
    m_def = Section(
        label='Presputtering',
        a_eln=ELNAnnotation(properties=SectionProperties(order=ORDER_RF_STEPS)),
    )

    name = Quantity(
        type=str,
        description="""A general step for STAR processes.""",
        a_eln=ELNAnnotation(
            component='StringEditQuantity',
            label='Step name',
        ),
        # default='Presputtering',
    )

    duration = Quantity(
        type=np.float64,
        description="""The duration of the step.""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Duration',
            defaultDisplayUnit='minute',
        ),
        unit='s',
        default=3 * 60,
    )


class StabilizationRFStep(StarRFStep):
    m_def = Section(
        label='Stabilization',
        a_eln=ELNAnnotation(properties=SectionProperties(order=ORDER_RF_STEPS)),
    )

    name = Quantity(
        type=str,
        description="""A general step for STAR processes.""",
        a_eln=ELNAnnotation(
            component='StringEditQuantity',
            label='Step name',
        ),
        # default='Stabilization',
    )

    duration = Quantity(
        type=np.float64,
        description="""The duration of the step.""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Duration',
            defaultDisplayUnit='minute',
        ),
        unit='s',
        default=2 * 60,
    )


class SputteringRFStep(StarRFStep):
    m_def = Section(
        label='Sputtering',
        a_eln=ELNAnnotation(properties=SectionProperties(order=ORDER_RF_STEPS)),
    )

    name = Quantity(
        type=str,
        description="""A general step for STAR processes.""",
        a_eln=ELNAnnotation(
            component='StringEditQuantity',
            label='Step name',
        ),
        # default='Sputtering',
    )


class PresputteringDCStep(StarDCStep):
    m_def = Section(
        label='Presputtering',
        a_eln=ELNAnnotation(properties=SectionProperties(order=ORDER_DC_STEPS)),
    )

    name = Quantity(
        type=str,
        description="""A general step for STAR processes.""",
        a_eln=ELNAnnotation(
            component='StringEditQuantity',
            label='Step name',
        ),
        # default='Presputtering',
    )

    duration = Quantity(
        type=np.float64,
        description="""The duration of the step.""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Duration',
            defaultDisplayUnit='minute',
        ),
        unit='s',
        default=3 * 60,
    )


class StabilizationDCStep(StarDCStep):
    m_def = Section(
        label='Stabilization',
        a_eln=ELNAnnotation(properties=SectionProperties(order=ORDER_DC_STEPS)),
    )

    name = Quantity(
        type=str,
        description="""A general step for STAR processes.""",
        a_eln=ELNAnnotation(
            component='StringEditQuantity',
            label='Step name',
        ),
        # default='Stabilization',
    )

    duration = Quantity(
        type=np.float64,
        description="""The duration of the step.""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Duration',
            defaultDisplayUnit='minute',
        ),
        unit='s',
        default=2 * 60,
    )


class SputteringDCStep(StarDCStep):
    m_def = Section(
        label='Sputtering',
        a_eln=ELNAnnotation(properties=SectionProperties(order=ORDER_DC_STEPS)),
    )

    name = Quantity(
        type=str,
        description="""A general step for STAR processes.""",
        a_eln=ELNAnnotation(
            component='StringEditQuantity',
            label='Step name',
        ),
        # default='Sputtering',
    )


class PostSputteringDCStep(StarDCStep):
    m_def = Section(
        label='Postsputtering',
        a_eln=ELNAnnotation(properties=SectionProperties(order=ORDER_DC_STEPS)),
    )

    name = Quantity(
        type=str,
        description="""A general step for STAR processes.""",
        a_eln=ELNAnnotation(
            component='StringEditQuantity',
            label='Step name',
        ),
        default='Postsputtering',
    )

    duration = Quantity(
        type=np.float64,
        description="""The duration of the step.""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Duration',
            defaultDisplayUnit='minute',
        ),
        unit='s',
        default=5 * 60,
    )


# Classes regarding the Samples
class StarGrowthRate(GrowthRate):
    m_def = Section(
        a_plot=dict(
            # x=['time', 'set_time'],
            # y=['value', 'set_value'],
            x='time',
            y='value',
        ),
        a_eln={'hide': ['set_value', 'set_time', 'time']},
    )
    measurement_type = Quantity(
        type=MEnum(
            'Mechanial profilometer',
            'Reflectance',
            'RHEED',
            'Other',
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.EnumEditQuantity,
        ),
    )
    value = Quantity(
        type=float,
        unit='meter/second',
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Thickness',
            defaultDisplayUnit='nm/minute',
        ),
        shape=['*'],
    )


class StarThinFilm(ThinFilm):
    m_def = Section(label='Thin Film')

    material = Quantity(
        type=str,
        description="""The material of the thin film.""",
        a_eln=ELNAnnotation(component='StringEditQuantity', label='Material'),
    )

    thickness = Quantity(
        type=np.float64,
        description="""The thickness of the thin film.""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity', label='Thickness', defaultDisplayUnit='nm'
        ),
        unit='meter',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.geometry is None:
            thinfilm_geo = RectangleCuboid()
            self.geometry = thinfilm_geo

        if self.thickness is not None:
            self.geometry.height = self.thickness

        if self.material is None and self.components[0] is not None:
            self.material = self.components[0].name

        logger.info(
            'NewSchema.normalize.StarThinFilm', parameter=configuration.parameter
        )
        # self.message = f'Hello {self.name}!'


class StarSubstrate(Substrate, EntryData):
    m_def = Section(label='Substrate', categories=[STARCategory])

    material = Quantity(
        type=str,
        description="""The material of the substrate.""",
        a_eln=ELNAnnotation(component='StringEditQuantity', label='Material'),
        default='SLG',
    )

    geometry = SubSection(section_def=Geometry)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.geometry is None:
            substrate_geo = RectangleCuboid()
            substrate_geo.height = 1 * ureg('mm')
            substrate_geo.width = 2.5 * ureg('cm')  # Quantity(2.5, unit='cm')
            substrate_geo.length = 2.5 * ureg('cm')  # Quantity(2.5, unit='cm')
            self.geometry = substrate_geo

        logger.info(
            'NewSchema.normalize.StarSubstrate', parameter=configuration.parameter
        )
        # self.message = f'Hello {self.name}!'


class StarSubstrateReference(SubstrateReference):
    """
    A section for describing a system component and its role in a composite system.
    """

    reference = Quantity(
        type=StarSubstrate,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Substrate',
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.reference is not None:
            if self.reference.name is not None:
                self.name = self.reference.name
            if self.reference.lab_id is not None:
                self.lab_id = self.reference.lab_id


class StarThinFilmReference(ThinFilmReference):
    """
    Class autogenerated from yaml schema.
    """

    reference = Quantity(
        type=StarThinFilm,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Thin Film',
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.reference is not None:
            if self.reference.name is not None:
                self.name = self.reference.name
            if self.reference.lab_id is not None:
                self.lab_id = self.reference.lab_id


class StarStack(ThinFilmStack, EntryData):
    m_def = Section(label='Thin Film Stack', categories=[STARCategory])

    layers = SubSection(
        section_def=StarThinFilmReference,
        repeats=True,
    )

    substrate = SubSection(
        section_def=StarSubstrateReference,
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """
        The normalizer for the `ThinFilmStack` class.

        Args:
            archive (EntryArchive): The archive containing the section that is being
            normalized.
            logger (BoundLogger): A structlog logger.
        """
        self.components = []
        if self.layers:
            self.components = [
                SystemComponent(system=layer.reference)
                for layer in self.layers
                if layer.reference
            ]

        if self.substrate.reference is not None:
            self.components.append(SystemComponent(system=self.substrate.reference))
            for layer in self.layers:
                if layer.reference:
                    if layer.reference.geometry is not None:
                        if self.substrate.reference.geometry is not None:
                            layer.reference.geometry.width = (
                                self.substrate.reference.geometry.width
                            )
                            layer.reference.geometry.length = (
                                self.substrate.reference.geometry.length
                            )

        super().normalize(archive, logger)


class StarStackReference(ThinFilmStackReference):
    """
    A section for describing a system component and its role in a composite system.
    """

    reference = Quantity(
        type=StarStack,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='ThinFilmStack',
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.reference is not None:
            if self.reference.name is not None:
                self.name = self.reference.name
            if self.reference.lab_id is not None:
                self.lab_id = self.reference.lab_id

        logger.info(
            'NewSchema.normalize.StarStackReference', parameter=configuration.parameter
        )


class StarSampleParameters(SampleParameters):
    m_def = Section(label='Sample Parameters')

    deposition_rate = Quantity(
        type=np.float64,
        description="""The deposition rate of the thin film (length/time).""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Deposition rate',
            defaultDisplayUnit='nm/minute',
        ),
        unit='meter/second',
    )

    growth_rate = SubSection(
        section_def=StarGrowthRate,
        description="""
        The growth rate of the thin film (length/time).
        """,
    )

    substrate = SubSection(
        section_def=StarStackReference,
        description="""The substrate used in the process.""",
    )

    layer = SubSection(
        section_def=StarThinFilmReference,
        description="""The thin film created in the process.""",
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.deposition_rate is not None:
            logger.warn(self.deposition_rate)
            if self.growth_rate is None:
                growth_rate_ = StarGrowthRate()
                value_rate = []
                value_rate.append(self.deposition_rate)
                growth_rate_.value = value_rate
                self.growth_rate = growth_rate_
            else:
                self.growth_rate.value = [self.deposition_rate]

        logger.info(
            'NewSchema.normalize.StarSampleParameters',
            parameter=configuration.parameter,
        )
        # self.message = f'Hello {self.name}!'


class StarCalibrationSampleParameters(StarSampleParameters):
    m_def = Section(
        label='Calibration Parameters',
        categories=[STARCategory],
    )

    film_thickness = Quantity(
        type=np.float64,
        description="""The thickness of the thin film (length).""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Film thickness',
            defaultDisplayUnit='nm',
        ),
        unit='meter',
    )


# Classes regarding the complete Sputtering Process


class StarSputtering(SputterDeposition, EntryData):
    m_def = Section(label='General STAR Sputtering', categories=[STARCategory])

    base_pressure = Quantity(
        type=np.float64,
        description="""The base pressure in the chamber.""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Base pressure',
            defaultDisplayUnit='millibar',
        ),
        unit='pascal',
    )

    is_a_calibration_experiment = Quantity(
        type=bool,
        description="""A boolean to indicate if the experiment is a calibration.""",
        a_eln=ELNAnnotation(
            component='BooleanEditQuantity',
            label='Calibration experiment',
        ),
    )

    samples = SubSection(section_def=StarStackReference, repeats=True)

    sources = SubSection(
        section_def=SputteringSource,
        repeats=True,
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        filetype = 'yaml'
        data_file = self.name.replace(' ', '_')

        for idx, step in enumerate(self.steps):
            step.name = str(idx + 1) + '_' + step.m_def.label.replace(' ', '_')
            if step.environment is not None:
                step.environment.step_name = step.name
            else:
                environment_ = StarChamberEnvironment()
                environment_.step_name = step.name
                step.environment = environment_

            if 'Sputtering' in step.name and step.creates_new_thin_film is not None:
                step.creates_new_thin_film = True

            # Set the source of each step the same as the whole deposition
            if self.sources is not None:
                if len(self.sources) != len(step.sources):
                    for source in self.sources:
                        new_source = SputteringSource()
                        new_source.material = source.material
                        new_sputter = Magnetron()
                        if step.power is not None:
                            new_power = SourcePower()
                            new_power.value = [step.power]
                            new_sputter.power = new_power
                        new_source.vapor_source.append(new_sputter)
                        step.sources.append(new_source)

            # Create a sample for each step that creat a new film

            film_index = 0

            if step.creates_new_thin_film and self.sources is not None:
                film_index += 1

                deposited_system = self.sources[0].material[0].system.components

                sample_parameters = []

                # new thin film
                new_thinFilm = StarThinFilm()

                new_thinFilm.material = deposited_system[0].pure_substance.name
                new_thinFilm.components = deposited_system

                thinFilm_filename, thinFilm_archive = create_filename(
                    data_file + '_' + new_thinFilm.material + str(film_index),
                    new_thinFilm,
                    'thinFilm',
                    archive,
                    logger,
                )

                if not archive.m_context.raw_path_exists(thinFilm_filename):
                    thinFilmRef = create_archive(
                        thinFilm_archive.m_to_dict(),
                        archive.m_context,
                        thinFilm_filename,
                        filetype,
                        logger,
                    )
                else:
                    thinFilmRef = get_hash_ref(
                        archive.m_context.upload_id, thinFilm_filename
                    )

                new_thinFilmReference = StarThinFilmReference(reference=thinFilmRef)

                if len(self.samples) > 0:
                    for sample in self.samples:
                        new_sample_par = StarSampleParameters()
                        new_sample_substrate = StarStackReference(
                            reference=sample.reference
                        )
                        new_sample_par.substrate = new_sample_substrate
                        new_sample_par.layer = new_thinFilmReference

                        sample_parameters.append(new_sample_par)
                else:
                    # new substrate

                    new_substrate = StarSubstrate()
                    substrate_filename, substrate_archive = create_filename(
                        data_file + '_sub', new_substrate, 'substrate', archive, logger
                    )

                    substrateRef = create_archive(
                        substrate_archive.m_to_dict(),
                        archive.m_context,
                        substrate_filename,
                        filetype,
                        logger,
                    )

                    new_substrateReference = StarSubstrateReference(
                        reference=substrateRef
                    )

                    # new stack
                    new_Stack = StarStack()
                    stack_filename, stack_archive = create_filename(
                        data_file + '_sample',
                        new_Stack,
                        'ThinFilmStack',
                        archive,
                        logger,
                    )

                    new_Stack.substrate = new_substrateReference
                    new_Stack.layers.append(new_thinFilmReference)

                    stackRef = create_archive(
                        stack_archive.m_to_dict(),
                        archive.m_context,
                        stack_filename,
                        filetype,
                        logger,
                    )

                    new_StackReference = StarStackReference(reference=stackRef)

                    if self.is_a_calibration_experiment:
                        new_sample_par = StarCalibrationSampleParameters()

                    else:
                        new_sample_par = StarSampleParameters()

                    new_sample_par.substrate = new_StackReference
                    new_sample_par.layer = new_thinFilmReference

                    sample_parameters.append(new_sample_par)

                    if self.is_a_calibration_experiment:
                        new_sample_par.deposition_rate = (
                            new_sample_par.film_thickness / step.duration
                        )

                if step.sample_parameters is None:
                    step.sample_parameters = sample_parameters

                if len(self.samples) == 0:
                    self.samples.append(new_StackReference)

                for sample in self.samples:
                    if step.sample_parameters is not None:
                        for sample_par in step.sample_parameters:
                            if sample_par.substrate.reference == sample.reference:
                                logger.info(sample_par.substrate.reference)
                                sample.reference.layers.append(sample_par.layer)

        logger.info(
            'NewSchema.normalize.StarSputtering', parameter=configuration.parameter
        )
        # self.message = f'Hello {self.name}!'


class StarRFSputtering(StarSputtering):
    m_def = Section(label='STAR RF Sputtering', categories=[STARCategory])

    steps = SubSection(
        section_def=StarRFStep,
        repeats=True,
    )


class StarDCSputtering(StarSputtering):
    m_def = Section(label='STAR DC Sputtering', categories=[STARCategory])

    steps = SubSection(
        section_def=StarDCStep,
        repeats=True,
    )


m_package.__init_metainfo__()
