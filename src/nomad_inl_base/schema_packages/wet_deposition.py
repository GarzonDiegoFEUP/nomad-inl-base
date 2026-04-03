from datetime import date as _date
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

import yaml
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
from nomad.datamodel.context import ClientContext
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
from nomad_material_processing.general import SampleDeposition
from nomad_material_processing.solution.general import Solution as NMPSolution

from nomad_inl_base.schema_packages.entities import (
    INLSampleReference,
    INLSubstrateReference,
    INLThinFilm,
    INLThinFilmReference,
    INLThinFilmStack,
    INLThinFilmStackReference,
)
from nomad_inl_base.utils import create_archive, create_filename, get_hash_ref

m_package = SchemaPackage()


class INLPrecursorSolution(PrecursorSolution):
    """PrecursorSolution that references a nomad-material-processing Solution entry."""

    m_def = Section(a_eln=dict(hide=['solution_details', 'reload_referenced_solution']))

    solution = Quantity(
        type=NMPSolution,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Solution Reference',
        ),
    )


class INLWetDepositionCategory(EntryDataCategory):
    m_def = Category(label='INL Wet Deposition', categories=[EntryDataCategory])


class WetDepositionRecipe(EntryData):
    """A re-usable recipe template for wet deposition methods."""

    m_def = Section(
        label='Wet Deposition Recipe',
        categories=[INLWetDepositionCategory],
        a_eln=dict(hide=['lab_id']),
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

    solution = SubSection(
        section_def=INLPrecursorSolution,
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


class INLSpinCoatingRecipe(WetDepositionRecipe):
    """Recipe template for INL spin coating."""

    m_def = Section(label='INL Spin Coating Recipe', categories=[INLWetDepositionCategory])

    recipe_steps = SubSection(
        section_def=SpinCoatingRecipeSteps,
        repeats=True,
        description='Spin coating steps template.',
    )


class INLSpinCoatingRecipeReference(WetDepositionRecipeReference):
    reference = Quantity(
        type=INLSpinCoatingRecipe,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Spin coating recipe',
        ),
    )


class INLSlotDieCoatingRecipe(WetDepositionRecipe):
    """Recipe template for INL slot-die coating."""

    m_def = Section(label='INL Slot-Die Coating Recipe', categories=[INLWetDepositionCategory])

    properties = SubSection(
        section_def=SlotDieCoatingProperties,
        description='Slot-die coating properties template.',
    )


class INLSlotDieCoatingRecipeReference(WetDepositionRecipeReference):
    reference = Quantity(
        type=INLSlotDieCoatingRecipe,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Slot-die coating recipe',
        ),
    )


class INLBladeCoatingRecipe(WetDepositionRecipe):
    """Recipe template for INL blade coating."""

    m_def = Section(label='INL Blade Coating Recipe', categories=[INLWetDepositionCategory])

    properties = SubSection(
        section_def=BladeCoatingProperties,
        description='Blade coating properties template.',
    )


class INLBladeCoatingRecipeReference(WetDepositionRecipeReference):
    reference = Quantity(
        type=INLBladeCoatingRecipe,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Blade coating recipe',
        ),
    )


class INLInkjetPrintingRecipe(WetDepositionRecipe):
    """Recipe template for INL inkjet printing."""

    m_def = Section(label='INL Inkjet Printing Recipe', categories=[INLWetDepositionCategory])

    properties = SubSection(
        section_def=InkjetPrintingProperties,
        description='Inkjet printing properties template.',
    )


class INLInkjetPrintingRecipeReference(WetDepositionRecipeReference):
    reference = Quantity(
        type=INLInkjetPrintingRecipe,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Inkjet printing recipe',
        ),
    )


class INLSprayPyrolysisRecipe(WetDepositionRecipe):
    """Recipe template for INL spray pyrolysis."""

    m_def = Section(label='INL Spray Pyrolysis Recipe', categories=[INLWetDepositionCategory])

    properties = SubSection(
        section_def=SprayPyrolysisProperties,
        description='Spray pyrolysis properties template.',
    )


class INLSprayPyrolysisRecipeReference(WetDepositionRecipeReference):
    reference = Quantity(
        type=INLSprayPyrolysisRecipe,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Spray pyrolysis recipe',
        ),
    )


class INLDipCoatingRecipe(WetDepositionRecipe):
    """Recipe template for INL dip coating."""

    m_def = Section(label='INL Dip Coating Recipe', categories=[INLWetDepositionCategory])

    properties = SubSection(
        section_def=DipCoatingProperties,
        description='Dip coating properties template.',
    )


class INLDipCoatingRecipeReference(WetDepositionRecipeReference):
    reference = Quantity(
        type=INLDipCoatingRecipe,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Dip coating recipe',
        ),
    )


class INLChemicalBathDepositionRecipe(WetDepositionRecipe):
    """Recipe template for INL chemical bath deposition."""

    m_def = Section(
        label='INL Chemical Bath Deposition Recipe',
        categories=[INLWetDepositionCategory],
        a_eln=dict(hide=['lab_id', 'annealing', 'quenching']),
    )

    bath_temperature = Quantity(
        type=float,
        unit='celsius',
        description='Template bath temperature.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='celsius',
        ),
    )

    duration = Quantity(
        type=float,
        unit='minute',
        description='Template total duration.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='minute',
        ),
    )

    ph = Quantity(
        type=float,
        description='Template pH of the chemical bath.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    stirring_speed = Quantity(
        type=float,
        unit='rpm',
        description='Template stirring speed.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='rpm',
        ),
    )

    deposited_material = Quantity(
        type=str,
        description=(
            'Material obtained after the chemical bath reaction (e.g. CdS, ZnS). '
            'Cannot be inferred from the solution reagents since a reaction occurs.'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Deposited material',
        ),
    )


class INLChemicalBathDepositionRecipeReference(WetDepositionRecipeReference):
    reference = Quantity(
        type=INLChemicalBathDepositionRecipe,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Chemical bath deposition recipe',
        ),
    )


class INLThinFilmDeposition(SampleDeposition, EntryData):
    """Base ELN schema for all INL wet deposition processes."""

    m_def = Section(
        links=['https://purl.archive.org/tfsco/TFSCO_00002051'],
        categories=[INLWetDepositionCategory],
        a_eln=dict(hide=['steps', 'instruments', 'lab_id', 'location', 'tags']),
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

    substrate = SubSection(
        section_def=INLSubstrateReference,
        description=(
            'The substrate this layer is deposited on. Set this for the first layer '
            'on a bare substrate — a new stack will be created automatically.'
        ),
    )

    sample = SubSection(
        section_def=INLThinFilmStackReference,
        description=(
            'The sample being built. For the first layer leave empty and set substrate. '
            'For multi-layer deposition set this to the existing stack — a new layer '
            'will be appended to it. After film creation this holds the resulting stack.'
        ),
    )

    samples = SubSection(
        section_def=INLSampleReference,
        repeats=True,
        description='References to INL samples (substrate, thin film, or stack) associated with this deposition.',
    )

    creates_new_thin_film = Quantity(
        type=bool,
        default=False,
        description=(
            'If True, create a new ThinFilm entry and append it to the sample stack '
            '(or create a new stack from the substrate if no sample is set yet).'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
            label='Create / append film',
        ),
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

    solution = SubSection(
        section_def=INLPrecursorSolution,
        repeats=True,
    )

    annealing = SubSection(section_def=Annealing)

    quenching = SubSection(section_def=Quenching)

    deposited_material = Quantity(
        type=str,
        description=(
            'Material of the deposited thin film. Auto-filled from the solution '
            'solute name if not set explicitly.'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Deposited material',
        ),
    )

    def _update_sample(
        self, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        """Create a new ThinFilm and register it with the sample stack.

        Case B — sample is None, substrate is set:
            Create INLThinFilm + new INLThinFilmStack (with that substrate),
            set self.sample to the new stack.
        Case A — sample already set:
            Create INLThinFilm, write-back the new layer to the existing stack
            yaml file so the change persists.
        Case C — neither set:
            Warn and return without creating anything.
        """
        data_file = (self.name or 'wet_deposition').replace(' ', '_')
        date_str = (
            self.start_time.strftime('%y%m%d')
            if self.start_time is not None
            else _date.today().strftime('%y%m%d')
        )
        material = self.deposited_material or 'film'
        film_label = f'{date_str}_{material}'

        # --- Case A: append to existing stack ---
        if self.sample is not None and self.sample.reference is not None:
            if isinstance(archive.m_context, ClientContext):
                logger.warning(
                    'INLThinFilmDeposition: running in ClientContext — '
                    'cannot write back to existing stack. Skipping film creation.'
                )
                return

            stack_path = getattr(self.sample.reference, 'raw_path', None)
            if not stack_path:
                logger.warning(
                    'INLThinFilmDeposition: existing sample stack has no raw_path — '
                    'normalize the stack entry first, then retry.'
                )
                return

            if not archive.m_context.raw_path_exists(stack_path):
                logger.warning(
                    f'INLThinFilmDeposition: stack file {stack_path!r} not found. '
                    'Skipping film creation.'
                )
                return

            # Create the new ThinFilm entry
            new_film = INLThinFilm()
            new_film.name = film_label
            if self.deposited_material:
                new_film.material = self.deposited_material
            film_filename, film_archive = create_filename(
                f'{film_label}_{data_file}', new_film, 'ThinFilm', archive, logger
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

            # Write-back: append new layer reference to the stack's raw yaml file
            with archive.m_context.raw_file(stack_path, 'r') as _f:
                stack_dict = yaml.safe_load(_f) or {}

            stack_data = stack_dict.setdefault('data', {})
            layers = stack_data.get('layers') or []
            layers.append({'reference': film_ref})
            stack_data['layers'] = layers

            with archive.m_context.raw_file(stack_path, 'w') as _f:
                yaml.dump(stack_dict, _f)

            archive.m_context.upload.process_updated_raw_file(
                stack_path, allow_modify=True
            )
            logger.info(
                f'INLThinFilmDeposition: appended new layer to existing stack {stack_path!r}.'
            )
            return

        # --- Case B: first layer on bare substrate — create new stack ---
        if self.substrate is not None:
            new_film = INLThinFilm()
            new_film.name = film_label
            if self.deposited_material:
                new_film.material = self.deposited_material
            film_filename, film_archive = create_filename(
                f'{film_label}_{data_file}', new_film, 'ThinFilm', archive, logger
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

            film_reference = INLThinFilmReference(reference=film_ref)

            stack = INLThinFilmStack()
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

            self.sample = INLThinFilmStackReference(reference=stack_ref)
            logger.info(
                'INLThinFilmDeposition: created new sample stack from substrate.'
            )
            return

        # --- Case C: nothing set ---
        logger.warning(
            'INLThinFilmDeposition: cannot create film — '
            'set either "substrate" (first layer) or "sample" (multi-layer append) first.'
        )

    def _apply_recipe(
        self, recipe: 'WetDepositionRecipe', archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        """Copy shared recipe fields. Override in subclasses to add technique-specific fields."""
        if recipe.instrument is not None and self.instrument is None:
            self.instrument = recipe.instrument
        if recipe.atmosphere is not None and self.atmosphere is None:
            self.atmosphere = recipe.atmosphere
        if recipe.solution is not None and not self.solution:
            self.solution = recipe.solution
        if recipe.annealing is not None and self.annealing is None:
            self.annealing = recipe.annealing
        if recipe.quenching is not None and self.quenching is None:
            self.quenching = recipe.quenching

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        if not self.method:
            self.method = 'Wet Deposition'
        super().normalize(archive, logger)

        if (
            self.apply_recipe
            and self.recipe is not None
            and getattr(self.recipe, 'reference', None) is not None
        ):
            self._apply_recipe(self.recipe.reference, archive, logger)
            self.apply_recipe = False

        if self.creates_new_thin_film:
            # Auto-fill deposited_material from solution solute name if not explicitly set
            if not self.deposited_material and self.solution:
                sol = self.solution[0]
                name = None
                # Try NMP Solution reference path first
                nmp_sol = getattr(sol, 'solution', None)
                if nmp_sol is not None:
                    solutes = getattr(nmp_sol, 'solutes', None)
                    if solutes:
                        pure = getattr(solutes[0], 'pure_substance', None)
                        name = getattr(pure, 'name', None) or getattr(
                            solutes[0], 'name', None
                        )
                if name:
                    self.deposited_material = name
            self._update_sample(archive, logger)
            self.creates_new_thin_film = False


class INLSpinCoating(INLThinFilmDeposition):
    """ELN schema for spin coating of thin films."""

    m_def = Section(
        links=['http://purl.obolibrary.org/obo/CHMO_0001472'],
        a_eln=dict(hide=['sample', 'tags', 'operator']),
    )

    recipe = SubSection(
        section_def=INLSpinCoatingRecipeReference,
        description='Reference to an INL spin coating recipe.',
    )

    recipe_steps = SubSection(section_def=SpinCoatingRecipeSteps, repeats=True)

    def _apply_recipe(
        self, recipe: 'INLSpinCoatingRecipe', archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        super()._apply_recipe(recipe, archive, logger)
        if recipe.recipe_steps and not self.recipe_steps:
            self.recipe_steps = recipe.recipe_steps

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Spin Coating'
        super().normalize(archive, logger)


class INLSlotDieCoating(INLThinFilmDeposition):
    """ELN schema for slot-die coating of thin films."""

    m_def = Section(
        links=['https://purl.archive.org/tfsco/TFSCO_00000075'],
    )

    recipe = SubSection(
        section_def=INLSlotDieCoatingRecipeReference,
        description='Reference to an INL slot-die coating recipe.',
    )

    properties = SubSection(section_def=SlotDieCoatingProperties)

    def _apply_recipe(
        self, recipe: 'INLSlotDieCoatingRecipe', archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        super()._apply_recipe(recipe, archive, logger)
        if recipe.properties is not None and self.properties is None:
            self.properties = recipe.properties

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Slot-Die Coating'
        super().normalize(archive, logger)


class INLBladeCoating(INLThinFilmDeposition):
    """ELN schema for blade (doctor blade) coating of thin films."""

    m_def = Section(
        links=['https://purl.archive.org/tfsco/TFSCO_00002060'],
    )

    recipe = SubSection(
        section_def=INLBladeCoatingRecipeReference,
        description='Reference to an INL blade coating recipe.',
    )

    properties = SubSection(section_def=BladeCoatingProperties)

    def _apply_recipe(
        self, recipe: 'INLBladeCoatingRecipe', archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        super()._apply_recipe(recipe, archive, logger)
        if recipe.properties is not None and self.properties is None:
            self.properties = recipe.properties

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Blade Coating'
        super().normalize(archive, logger)


class INLInkjetPrinting(INLThinFilmDeposition):
    """ELN schema for inkjet printing of thin films."""

    m_def = Section(
        links=['https://purl.archive.org/tfsco/TFSCO_00002053'],
    )

    recipe = SubSection(
        section_def=INLInkjetPrintingRecipeReference,
        description='Reference to an INL inkjet printing recipe.',
    )

    properties = SubSection(section_def=InkjetPrintingProperties)

    def _apply_recipe(
        self, recipe: 'INLInkjetPrintingRecipe', archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        super()._apply_recipe(recipe, archive, logger)
        if recipe.properties is not None and self.properties is None:
            self.properties = recipe.properties

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Inkjet Printing'
        super().normalize(archive, logger)


class INLSprayPyrolysis(INLThinFilmDeposition):
    """ELN schema for spray pyrolysis deposition of thin films."""

    m_def = Section(
        links=['http://purl.obolibrary.org/obo/CHMO_0001516'],
    )

    recipe = SubSection(
        section_def=INLSprayPyrolysisRecipeReference,
        description='Reference to an INL spray pyrolysis recipe.',
    )

    properties = SubSection(section_def=SprayPyrolysisProperties)

    def _apply_recipe(
        self, recipe: 'INLSprayPyrolysisRecipe', archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        super()._apply_recipe(recipe, archive, logger)
        if recipe.properties is not None and self.properties is None:
            self.properties = recipe.properties

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Spray Pyrolysis'
        super().normalize(archive, logger)


class INLDipCoating(INLThinFilmDeposition):
    """ELN schema for dip coating of thin films."""

    m_def = Section(
        links=['http://purl.obolibrary.org/obo/CHMO_0001471'],
    )

    recipe = SubSection(
        section_def=INLDipCoatingRecipeReference,
        description='Reference to an INL dip coating recipe.',
    )

    properties = SubSection(section_def=DipCoatingProperties)

    def _apply_recipe(
        self, recipe: 'INLDipCoatingRecipe', archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        super()._apply_recipe(recipe, archive, logger)
        if recipe.properties is not None and self.properties is None:
            self.properties = recipe.properties

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Dip Coating'
        super().normalize(archive, logger)


class INLChemicalBathDeposition(INLThinFilmDeposition):
    """ELN schema for chemical bath deposition (CBD) of thin films."""

    m_def = Section(
        links=['http://purl.obolibrary.org/obo/CHMO_0001465'],
        a_eln=dict(hide=['annealing', 'quenching']),
    )

    recipe = SubSection(
        section_def=INLChemicalBathDepositionRecipeReference,
        description='Reference to an INL chemical bath deposition recipe.',
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

    color_change_time = Quantity(
        type=float,
        unit='minute',
        description=(
            'Time at which a color change was observed in the solution, if any. '
            'This can be an indication of the reaction progress and film formation.'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='minute',
            label='Color change time',
        ),
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

    def _apply_recipe(
        self, recipe: 'INLChemicalBathDepositionRecipe', archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        super()._apply_recipe(recipe, archive, logger)
        if recipe.bath_temperature is not None and self.bath_temperature is None:
            self.bath_temperature = recipe.bath_temperature
        if recipe.duration is not None and self.duration is None:
            self.duration = recipe.duration
        if recipe.ph is not None and self.ph is None:
            self.ph = recipe.ph
        if recipe.stirring_speed is not None and self.stirring_speed is None:
            self.stirring_speed = recipe.stirring_speed
        if recipe.deposited_material and not self.deposited_material:
            self.deposited_material = recipe.deposited_material

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Chemical Bath Deposition'
        super().normalize(archive, logger)


m_package.__init_metainfo__()
