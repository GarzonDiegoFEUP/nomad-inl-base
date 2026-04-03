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
from nomad_material_processing.vapor_deposition.general import GasFlow

from nomad_inl_base.schema_packages.entities import INLGraphiteBoxReference

_DEFAULT_TUBE_PRESSURE_MBAR = 1013.25

m_package = SchemaPackage()


class INLAnnealingCategory(EntryDataCategory):
    m_def = Category(label='INL Annealing', categories=[EntryDataCategory])


class INLChalcogenSource(ArchiveSection):
    """A solid chalcogen or chalcogenide source used in tube furnace annealing."""

    m_def = Section(
        label='Chalcogen Source',
    )

    material = SubSection(
        section_def=PureSubstanceSection,
        description='The source material (e.g. Se, S, Na2Se). Looked up via PubChem.',
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
        section_def=GasFlow,
        repeats=True,
        description='Gas flow(s) active during this step.',
    )


class INLTubeFurnaceAnnealing(Process, EntryData):
    """ELN schema for tube furnace annealing (selenization / sulfurization)."""

    m_def = Section(
        links=['http://purl.obolibrary.org/obo/CHMO_0001465'],
        categories=[INLAnnealingCategory],
        a_eln=dict(hide=['instruments', 'lab_id', 'location']),
    )

    graphite_box = SubSection(
        section_def=INLGraphiteBoxReference,
        description='The graphite box used in this annealing run.',
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
        section_def=GasFlow,
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
