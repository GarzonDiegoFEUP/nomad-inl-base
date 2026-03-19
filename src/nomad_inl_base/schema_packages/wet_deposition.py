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

from baseclasses.atmosphere import Atmosphere
from baseclasses.material_processes_misc import Annealing, Quenching
from baseclasses.wet_chemical_deposition.blade_coating import BladeCoatingProperties
from baseclasses.wet_chemical_deposition.dip_coating import DipCoatingProperties
from baseclasses.wet_chemical_deposition.inkjet_printing import InkjetPrintingProperties
from baseclasses.wet_chemical_deposition.slot_die_coating import (
    SlotDieCoatingProperties,
)
from baseclasses.wet_chemical_deposition.spin_coating import SpinCoatingRecipeSteps
from baseclasses.wet_chemical_deposition.spray_pyrolysis import SprayPyrolysisProperties
from baseclasses.wet_chemical_deposition.wet_chemical_deposition import (
    PrecursorSolution,
)
from nomad.datamodel.data import (
    EntryData,
    EntryDataCategory,
)
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import EntityReference, InstrumentReference
from nomad.metainfo import (
    Category,
    Quantity,
    SchemaPackage,
    Section,
    SubSection,
)
from nomad_material_processing.general import (
    SampleDeposition,
    SubstrateReference,
    ThinFilm,
    ThinFilmReference,
    ThinFilmStack,
    ThinFilmStackReference,
)

from nomad_inl_base.utils import create_archive, create_filename, get_hash_ref

m_package = SchemaPackage()


class INLWetDepositionCategory(EntryDataCategory):
    m_def = Category(label='INL Wet Deposition', categories=[EntryDataCategory])


class WetDepositionRecipe(EntryData):
    """A re-usable recipe template for wet deposition methods."""

    m_def = Section(
        label='Wet Deposition Recipe', categories=[INLWetDepositionCategory]
    )

    name = Quantity(
        type=str,
        description='Recipe name.',
        a_eln=ELNAnnotation(component='StringEditQuantity', label='Recipe name'),
    )

    description = Quantity(
        type=str,
        description='Recipe description.',
        a_eln=ELNAnnotation(component='RichTextEditQuantity', label='Description'),
    )

    instrument = SubSection(
        section_def=InstrumentReference,
        description='Instrument template for the recipe.',
    )

    atmosphere = SubSection(
        section_def=Atmosphere,
        description='Atmosphere template for the recipe.',
    )

    substrate = SubSection(
        section_def=SubstrateReference,
        description='Substrate template for the recipe.',
    )

    solution = SubSection(
        section_def=PrecursorSolution,
        repeats=True,
        description='Solution/precursor template for the recipe.',
    )

    annealing = SubSection(
        section_def=Annealing,
        description='Annealing template for the recipe.',
    )

    quenching = SubSection(
        section_def=Quenching,
        description='Quenching template for the recipe.',
    )


class WetDepositionRecipeReference(EntityReference):
    """A reference to a WetDepositionRecipe entry."""

    m_def = Section(hide=['name', 'lab_id'])

    reference = Quantity(
        type=WetDepositionRecipe,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Wet deposition recipe',
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        # Skip EntityReference.normalize() — WetDepositionRecipe is not an Entity
        # and does not have lab_id.
        pass


class INLThinFilmDeposition(SampleDeposition, EntryData):
    """Base ELN schema for all INL wet deposition processes."""

    m_def = Section(
        links=['https://purl.archive.org/tfsco/TFSCO_00002051'],
        categories=[INLWetDepositionCategory],
    )

    tags = Quantity(
        type=str,
        shape=['*'],
        description='Tags for categorizing this deposition.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    operator = Quantity(
        type=str,
        description='Name of the person who performed this deposition.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    instrument = SubSection(
        section_def=InstrumentReference,
        description='Reference to the instrument used for this deposition.',
    )

    atmosphere = SubSection(section_def=Atmosphere)

    substrate = SubSection(section_def=SubstrateReference)

    creates_new_thin_film = Quantity(
        type=bool,
        default=False,
        description='If True, create a ThinFilm + ThinFilmStack entry via normalize.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.BoolEditQuantity),
    )

    recipe = SubSection(
        section_def=WetDepositionRecipeReference,
        description='Reference to a wet deposition recipe to apply.',
    )

    apply_recipe = Quantity(
        type=bool,
        default=False,
        description='If True, apply the selected recipe (once) when normalizing.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.BoolEditQuantity),
    )

    thin_film_stack = SubSection(section_def=ThinFilmStackReference)

    solution = SubSection(
        section_def=PrecursorSolution,
        repeats=True,
    )

    annealing = SubSection(section_def=Annealing)

    quenching = SubSection(section_def=Quenching)

    def _create_thin_film_stack(
        self, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        """Auto-create ThinFilm + ThinFilmStack entries and set thin_film_stack."""

        if (
            self.thin_film_stack is not None
            and self.thin_film_stack.reference is not None
        ):
            return

        data_file = (self.name or 'wet_deposition').replace(' ', '_')

        # Create ThinFilm entry
        new_film = ThinFilm()
        film_filename, film_archive = create_filename(
            data_file + '_thin_film', new_film, 'ThinFilm', archive, logger
        )

        if not archive.m_context.raw_path_exists(film_filename):
            film_ref = create_archive(
                film_archive.m_to_dict(),
                archive.m_context,
                film_filename,
                'yaml',
                logger,
            )
        else:
            film_ref = get_hash_ref(archive.m_context.upload_id, film_filename)

        film_reference = ThinFilmReference(reference=film_ref)

        # Create ThinFilmStack entry
        stack = ThinFilmStack()
        if self.substrate is not None:
            stack.substrate = self.substrate
        stack.layers = [film_reference]

        stack_filename, stack_archive = create_filename(
            data_file + '_thin_film_stack', stack, 'ThinFilmStack', archive, logger
        )

        if not archive.m_context.raw_path_exists(stack_filename):
            stack_ref = create_archive(
                stack_archive.m_to_dict(),
                archive.m_context,
                stack_filename,
                'yaml',
                logger,
            )
        else:
            stack_ref = get_hash_ref(archive.m_context.upload_id, stack_filename)

        self.thin_film_stack = ThinFilmStackReference(reference=stack_ref)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        if not self.method:
            self.method = 'Wet Deposition'
        super().normalize(archive, logger)

        if (
            self.apply_recipe
            and self.recipe is not None
            and getattr(self.recipe, 'reference', None) is not None
        ):
            recipe = self.recipe.reference
            if recipe.instrument is not None and self.instrument is None:
                self.instrument = recipe.instrument
            if recipe.atmosphere is not None and self.atmosphere is None:
                self.atmosphere = recipe.atmosphere
            if recipe.substrate is not None and self.substrate is None:
                self.substrate = recipe.substrate
            if recipe.solution is not None and not self.solution:
                self.solution = recipe.solution
            if recipe.annealing is not None and self.annealing is None:
                self.annealing = recipe.annealing
            if recipe.quenching is not None and self.quenching is None:
                self.quenching = recipe.quenching
            self.apply_recipe = False

        if self.creates_new_thin_film:
            self._create_thin_film_stack(archive, logger)
            self.creates_new_thin_film = False


class INLSpinCoating(INLThinFilmDeposition):
    """ELN schema for spin coating of thin films."""

    m_def = Section(
        links=['http://purl.obolibrary.org/obo/CHMO_0001472'],
    )

    recipe_steps = SubSection(section_def=SpinCoatingRecipeSteps, repeats=True)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Spin Coating'
        super().normalize(archive, logger)


class INLSlotDieCoating(INLThinFilmDeposition):
    """ELN schema for slot-die coating of thin films."""

    m_def = Section(
        links=['https://purl.archive.org/tfsco/TFSCO_00000075'],
    )

    properties = SubSection(section_def=SlotDieCoatingProperties)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Slot-Die Coating'
        super().normalize(archive, logger)


class INLBladeCoating(INLThinFilmDeposition):
    """ELN schema for blade (doctor blade) coating of thin films."""

    m_def = Section(
        links=['https://purl.archive.org/tfsco/TFSCO_00002060'],
    )

    properties = SubSection(section_def=BladeCoatingProperties)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Blade Coating'
        super().normalize(archive, logger)


class INLInkjetPrinting(INLThinFilmDeposition):
    """ELN schema for inkjet printing of thin films."""

    m_def = Section(
        links=['https://purl.archive.org/tfsco/TFSCO_00002053'],
    )

    properties = SubSection(section_def=InkjetPrintingProperties)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Inkjet Printing'
        super().normalize(archive, logger)


class INLSprayPyrolysis(INLThinFilmDeposition):
    """ELN schema for spray pyrolysis deposition of thin films."""

    m_def = Section(
        links=['http://purl.obolibrary.org/obo/CHMO_0001516'],
    )

    properties = SubSection(section_def=SprayPyrolysisProperties)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Spray Pyrolysis'
        super().normalize(archive, logger)


class INLDipCoating(INLThinFilmDeposition):
    """ELN schema for dip coating of thin films."""

    m_def = Section(
        links=['http://purl.obolibrary.org/obo/CHMO_0001471'],
    )

    properties = SubSection(section_def=DipCoatingProperties)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Dip Coating'
        super().normalize(archive, logger)


class INLChemicalBathDeposition(INLThinFilmDeposition):
    """ELN schema for chemical bath deposition (CBD) of thin films."""

    m_def = Section(
        links=['http://purl.obolibrary.org/obo/CHMO_0001465'],
    )

    bath_temperature = Quantity(
        type=float,
        unit='celsius',
        description='Temperature of the chemical bath during deposition.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='celsius',
        ),
    )

    duration = Quantity(
        type=float,
        unit='minute',
        description='Total duration of the chemical bath deposition.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='minute',
        ),
    )

    ph = Quantity(
        type=float,
        description='pH of the chemical bath.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    stirring_speed = Quantity(
        type=float,
        unit='rpm',
        description='Stirring speed of the bath during deposition.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='rpm',
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Chemical Bath Deposition'
        super().normalize(archive, logger)


m_package.__init_metainfo__()
