from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

from nomad.datamodel.data import ArchiveSection, EntryData, EntryDataCategory
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import (
    EntityReference,
    Process,
    PureSubstanceSection,
)
from nomad.metainfo import (
    Category,
    MEnum,
    Quantity,
    SchemaPackage,
    Section,
    SubSection,
)
from nomad_material_processing.general import AnnealingStep
from nomad_material_processing.vapor_deposition.general import (
    GasFlow,
    VolumetricFlowRate,
)

from nomad_inl_base.schema_packages.entities import (
    INLGraphiteBoxReference,
    INLInstrumentReference,
    INLSampleReference,
)

_DEFAULT_TUBE_PRESSURE_MBAR = 1013.25

m_package = SchemaPackage()


class INLAnnealingCategory(EntryDataCategory):
    m_def = Category(label='INL Annealing', categories=[EntryDataCategory])


class INLChalcogenSource(ArchiveSection):
    """A solid chalcogen or chalcogenide source used in tube furnace annealing."""

    m_def = Section(
        label='Chalcogen Source',
    )

    name = Quantity(
        type=str,
        description='Substance name — auto-populated from material after PubChem lookup.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Name',
        ),
    )

    material = SubSection(
        section_def=PureSubstanceSection,
        description='The source material (e.g. Se, S, Na2Se). Auto-filled via PubChem when name is set.',
    )

    amount = Quantity(
        type=float,
        unit='mg',
        description='Mass of the source material used.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mg',
            label='Amount',
        ),
    )

    location = Quantity(
        type=MEnum('Inside box', 'Outside box'),
        description='Whether the source is placed inside or outside the graphite box.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.RadioEnumEditQuantity,
            label='Location',
        ),
    )

    form = Quantity(
        type=MEnum('Powder', 'Pellets'),
        description='Physical form of the source material.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.RadioEnumEditQuantity,
            label='Form',
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        if self.material is not None:
            self.material.normalize(archive, logger)
            if not self.name and self.material.name:
                self.name = self.material.name


class INLVolumetricFlowRate(VolumetricFlowRate):
    """Flow rate section for INL tube furnace gas lines."""

    m_def = Section(a_eln={'hide': ['value', 'set_time']})

    measurement_type = Quantity(
        type=MEnum('Mass Flow Controller', 'Rotameter', 'Other'),
        description='Method used to measure or control the flow rate.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.RadioEnumEditQuantity,
            label='Measurement type',
        ),
    )


class INLGasFlow(GasFlow):
    """Gas flow for INL tube furnace processes."""

    m_def = Section(label='Gas Flow')

    name = Quantity(
        type=str,
        description='Name of the gas (e.g. "N2", "H2Se").',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Gas name',
        ),
    )

    flow_rate = SubSection(section_def=INLVolumetricFlowRate)


class INLAnnealingStep(AnnealingStep):
    """A single step of an INL tube furnace annealing temperature profile."""

    m_def = Section(label='Annealing Step')

    heating_rate = Quantity(
        type=float,
        unit='K/minute',
        description='Rate of temperature change during this step.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='°C/minute',
            label='Heating rate',
        ),
    )

    gas_flow = SubSection(
        section_def=INLGasFlow,
        repeats=True,
        description='Gas flow(s) active during this step.',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        if (
            self.duration is None
            and self.starting_temperature is not None
            and self.ending_temperature is not None
            and self.heating_rate is not None
        ):
            t_start = self.starting_temperature
            t_end = self.ending_temperature
            rate = self.heating_rate
            t_start = t_start.magnitude if hasattr(t_start, 'magnitude') else float(t_start)
            t_end = t_end.magnitude if hasattr(t_end, 'magnitude') else float(t_end)
            rate = rate.magnitude if hasattr(rate, 'magnitude') else float(rate)
            if rate != 0 and t_start != t_end:
                self.duration = abs(t_end - t_start) / rate * 60.0


class INLTubeFurnaceAnnealing(Process, EntryData):
    """ELN schema for tube furnace annealing (selenization / sulfurization)."""

    m_def = Section(
        links=['http://purl.obolibrary.org/obo/CHMO_0001465'],
        categories=[INLAnnealingCategory],
        a_eln=dict(hide=['instruments', 'lab_id', 'location']),
    )

    instrument = SubSection(
        section_def=INLInstrumentReference,
        description='The furnace or instrument used for this annealing run.',
    )

    graphite_box = SubSection(
        section_def=INLGraphiteBoxReference,
        description='The graphite box used in this annealing run.',
    )

    samples = SubSection(
        section_def=INLSampleReference,
        repeats=True,
        description='Sample(s) processed in this annealing run.',
    )

    tube_diameter = Quantity(
        type=float,
        unit='mm',
        description='Inner diameter of the quartz / alumina tube.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mm',
            label='Tube diameter',
        ),
    )

    boat_position = Quantity(
        type=str,
        description=(
            'Position of the sample boat inside the tube '
            '(e.g. "5 cm upstream from center").'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Boat position',
        ),
    )

    tube_pressure = Quantity(
        type=float,
        unit='mbar',
        default=_DEFAULT_TUBE_PRESSURE_MBAR,
        description='Total pressure in the tube during annealing.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mbar',
            label='Tube pressure',
        ),
    )

    chalcogen_sources = SubSection(
        section_def=INLChalcogenSource,
        repeats=True,
        description='Solid chalcogen / chalcogenide source(s) used in this run.',
    )

    gas_flow = SubSection(
        section_def=INLGasFlow,
        repeats=True,
        description='Global baseline gas flow(s) for the run (can be overridden per step).',
    )

    steps = SubSection(
        section_def=INLAnnealingStep,
        repeats=True,
        description='Temperature profile: list of ramp / soak steps.',
    )

    recipe = SubSection(
        section_def='INLTubeFurnaceAnnealingRecipeReference',
        description='Reference to a tube furnace annealing recipe to apply.',
    )

    apply_recipe = Quantity(
        type=bool,
        default=False,
        description='If True, apply the selected recipe (once) when normalizing.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
            label='Apply recipe',
        ),
    )

    def _apply_recipe(
        self,
        recipe: 'INLTubeFurnaceAnnealingRecipe',
        archive: 'EntryArchive',
        logger: 'BoundLogger',
    ) -> None:
        """Copy recipe fields into this run (only if not already set)."""
        if recipe.instrument is not None and self.instrument is None:
            self.instrument = recipe.instrument
        if recipe.graphite_box is not None and self.graphite_box is None:
            self.graphite_box = recipe.graphite_box
        if recipe.tube_diameter is not None and self.tube_diameter is None:
            self.tube_diameter = recipe.tube_diameter
        if recipe.boat_position and not self.boat_position:
            self.boat_position = recipe.boat_position
        if recipe.tube_pressure is not None and self.tube_pressure == _DEFAULT_TUBE_PRESSURE_MBAR:
            self.tube_pressure = recipe.tube_pressure
        if recipe.chalcogen_sources and not self.chalcogen_sources:
            self.chalcogen_sources = recipe.chalcogen_sources
        if recipe.gas_flow and not self.gas_flow:
            self.gas_flow = recipe.gas_flow
        if recipe.steps and not self.steps:
            self.steps = recipe.steps

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Tube Furnace Annealing'
        super().normalize(archive, logger)

        if (
            self.apply_recipe
            and self.recipe is not None
            and getattr(self.recipe, 'reference', None) is not None
        ):
            self._apply_recipe(self.recipe.reference, archive, logger)
            self.apply_recipe = False


class INLTubeFurnaceAnnealingRecipe(INLTubeFurnaceAnnealing, EntryData):
    """Reusable recipe template for tube furnace annealing."""

    m_def = Section(
        label='INL Tube Furnace Annealing Recipe',
        categories=[INLAnnealingCategory],
        a_eln=dict(hide=[
            'instruments', 'lab_id', 'location',
            'samples', 'datetime', 'end_time', 'apply_recipe',
            'recipe',
        ]),
    )


class INLTubeFurnaceAnnealingRecipeReference(EntityReference):
    """Reference to an INLTubeFurnaceAnnealingRecipe entry."""

    m_def = Section(hide=['name', 'lab_id'])

    reference = Quantity(
        type=INLTubeFurnaceAnnealingRecipe,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Tube furnace annealing recipe',
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        # INLTubeFurnaceAnnealingRecipe is not an Entity — skip EntityReference.normalize()
        pass


m_package.__init_metainfo__()
