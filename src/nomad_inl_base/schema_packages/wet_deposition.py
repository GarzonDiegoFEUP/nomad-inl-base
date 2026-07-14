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
from baseclasses.wet_chemical_deposition.blade_coating import BladeCoatingProperties
from baseclasses.wet_chemical_deposition.dip_coating import DipCoatingProperties
from baseclasses.wet_chemical_deposition.inkjet_printing import InkjetPrintingProperties
from baseclasses.wet_chemical_deposition.slot_die_coating import (
    SlotDieCoatingProperties,
)
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
from nomad.datamodel.metainfo.basesections import (
    EntityReference,
    InstrumentReference,
    ProcessStep,
)
from nomad.metainfo import (
    Category,
    MSection,
    Quantity,
    SchemaPackage,
    Section,
    SubSection,
)
from nomad_material_processing.general import SampleDeposition
from nomad_material_processing.solution.general import Solution as NMPSolution
from nomad_material_processing.solution.general import (
    SolutionComponent as NMPSolutionComponent,
)
from nomad_material_processing.solution.general import (
    SolutionComponentReference as NMPSolutionComponentReference,
)

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


# ---------------------------------------------------------------------------
# Process step classes
# ---------------------------------------------------------------------------


class INLWetDepositionStep(ProcessStep):
    """Base step for INL wet deposition. Optionally carries its own solution."""

    m_def = Section(a_eln=dict(hide=['start_time']))

    solution = SubSection(
        section_def=INLPrecursorSolution,
        repeats=True,
        description='Solution(s) for this step. Leave empty to use the entry-level solution.',
    )


class INLSpinCoatingStep(INLWetDepositionStep):
    """A single spin-coating step (speed / time / acceleration)."""

    m_def = Section(label='Spin Coating Step')

    speed = Quantity(
        type=float,
        unit='rpm',
        description='Rotation speed for this step.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='rpm',
        ),
    )
    duration = Quantity(
        type=float,
        unit='s',
        description='Duration of this spin step.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='s',
        ),
    )
    acceleration = Quantity(
        type=float,
        unit='rpm/s',
        description='Ramp rate to reach the target speed.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='rpm/s',
        ),
    )


class INLHotplateAnnealingStep(INLWetDepositionStep):
    """A hotplate annealing step within a wet deposition sequence."""

    m_def = Section(label='Hotplate Annealing Step')

    temperature = Quantity(
        type=float,
        unit='K',
        description='Hotplate set temperature.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='celsius',
        ),
    )
    duration = Quantity(
        type=float,
        unit='s',
        description='Annealing duration.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='minute',
        ),
    )


class INLAntisolventQuenchingStep(INLWetDepositionStep):
    """An antisolvent quenching step within a wet deposition sequence."""

    m_def = Section(label='Antisolvent Quenching Step')

    volume = Quantity(
        type=float,
        unit='ml',
        description='Volume of antisolvent dispensed.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ml',
        ),
    )
    dispensing_speed = Quantity(
        type=float,
        unit='ml/s',
        description='Speed at which the antisolvent is dispensed.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ml/s',
        ),
    )


class INLCBDReagent(MSection):
    """A single reagent used in a CBD solution or added directly to a bath."""

    m_def = Section(
        label='CBD Reagent',
        more=dict(label_quantity='name'),
    )

    name = Quantity(
        type=str,
        description=(
            'Reagent name as it should appear in the chemical database lookup '
            '(e.g. "cadmium acetate", "thiourea", "ammonium hydroxide"). '
            'This name is used to search PubChem for molecular weight and other '
            'properties needed to calculate molar concentration.'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Reagent name (used for PubChem lookup)',
        ),
    )

    mass = Quantity(
        type=float,
        unit='g',
        description='Mass of solid reagent.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='g',
        ),
    )

    volume = Quantity(
        type=float,
        unit='ml',
        description='Volume of liquid reagent.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ml',
        ),
    )


class INLCBDSolutionTemplate(MSection):
    """Inline solution preparation template embedded in a CBD recipe.

    When a deposition entry applies the recipe and create_solutions is set,
    a nomad-material-processing Solution entry is auto-created from this template.
    """

    m_def = Section(label='Solution Template')

    name = Quantity(
        type=str,
        description='Name for the Solution entry that will be created (e.g. "Cd acetate solution").',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Solution name',
        ),
    )

    solvent = Quantity(
        type=str,
        description='Solvent used to prepare this solution (e.g. "deionized water", "ethanol").',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Solvent',
        ),
    )

    total_volume = Quantity(
        type=float,
        unit='ml',
        description='Total volume of the prepared solution.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ml',
        ),
    )

    reagents = SubSection(
        section_def=INLCBDReagent,
        repeats=True,
        description='Reagents dissolved to prepare this solution.',
    )


class INLCBDBathPreparationStep(INLWetDepositionStep):
    """A CBD bath preparation step (e.g., dissolve reagent, add to bath, heat)."""

    m_def = Section(label='CBD Bath Preparation Step')

    reagents = SubSection(
        section_def=INLCBDReagent,
        repeats=True,
        description='Reagents added directly to the bath in this step (Type 1 in-situ prep).',
    )


class INLWetDepositionCategory(EntryDataCategory):
    m_def = Category(label='INL Wet Deposition', categories=[EntryDataCategory])


class INLCBDComponentMixture(MSection):
    """A component in a CBD bath composition (pre-made solution mixed with specific volume)."""

    m_def = Section(
        label='CBD Bath Component',
        more=dict(label_quantity='name'),
    )

    name = Quantity(
        type=str,
        description='Descriptive name for this bath component (e.g., "CdCl2 solution", "Solution A").',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Component name',
        ),
    )

    solution = Quantity(
        type=NMPSolution,
        description='Reference to a pre-made Solution entry.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Solution',
        ),
    )

    volume = Quantity(
        type=float,
        unit='ml',
        description='Volume of this solution component added to the bath.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='ml',
        ),
    )

    order = Quantity(
        type=int,
        description='Order of addition (1, 2, 3, ...) to the bath.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    notes = Quantity(
        type=str,
        description='Optional notes on mixing conditions (e.g., temperature, stirring time).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.RichTextEditQuantity),
    )

    solution_template = SubSection(
        section_def=INLCBDSolutionTemplate,
        description=(
            'Inline solution preparation template (used in recipes only). '
            'When create_solutions is set on the deposition entry, a Solution entry '
            'is auto-created from this template and wired into the solution field.'
        ),
    )


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

    steps = SubSection(
        section_def=INLWetDepositionStep,
        repeats=True,
        description='Ordered process steps for this recipe.',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        if not self.steps:
            return
        existing_refs: set[str] = set()
        if self.solution:
            for sol in self.solution:
                ref = getattr(sol, 'solution', None)
                if ref is not None:
                    existing_refs.add(
                        getattr(ref, 'm_proxy_value', None) or str(ref)
                    )
        for step in self.steps:
            for step_sol in getattr(step, 'solution', None) or []:
                ref = getattr(step_sol, 'solution', None)
                if ref is None:
                    continue
                val = getattr(ref, 'm_proxy_value', None) or str(ref)
                if val not in existing_refs:
                    existing_refs.add(val)
                    if self.solution is None:
                        self.solution = []
                    self.solution.append(
                        INLPrecursorSolution.m_from_dict(step_sol.m_to_dict())
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


class INLSlotDieCoatingRecipe(WetDepositionRecipe):
    """Recipe template for INL slot-die coating."""

    m_def = Section(
        label='INL Slot-Die Coating Recipe', categories=[INLWetDepositionCategory]
    )

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

    m_def = Section(
        label='INL Blade Coating Recipe', categories=[INLWetDepositionCategory]
    )

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

    m_def = Section(
        label='INL Inkjet Printing Recipe', categories=[INLWetDepositionCategory]
    )

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

    m_def = Section(
        label='INL Spray Pyrolysis Recipe',
        categories=[INLWetDepositionCategory],
        a_eln=dict(hide=['steps']),
    )

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

    m_def = Section(
        label='INL Dip Coating Recipe', categories=[INLWetDepositionCategory]
    )

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
    """Recipe template for INL chemical bath deposition.

    Supports two CBD types:
    - Type 1 (in-situ prep): Use 'steps' field with INLCBDBathPreparationStep entries.
    - Type 2 (pre-mixed): Use 'bath_composition' field with pre-made solutions and volumes.
    """

    m_def = Section(
        label='INL Chemical Bath Deposition Recipe',
        categories=[INLWetDepositionCategory],
        a_eln=dict(hide=['lab_id']),
    )

    bath_composition = SubSection(
        section_def=INLCBDComponentMixture,
        repeats=True,
        description=(
            'Bath composition template for Type 2 (pre-mixed) CBD: '
            'pre-made solutions and their standard volumes. '
            'Leave empty for Type 1 (in-situ prep) recipes.'
        ),
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
        a_eln=dict(hide=['instruments', 'lab_id', 'location', 'tags']),
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

    steps = SubSection(
        section_def=INLWetDepositionStep,
        repeats=True,
        description='Ordered process steps (spin coating, annealing, quenching, …).',
    )

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

    def _update_sample(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
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
        self,
        recipe: 'WetDepositionRecipe',
        archive: 'EntryArchive',
        logger: 'BoundLogger',
    ) -> None:
        """Copy shared recipe fields. Override in subclasses to add technique-specific fields."""
        if recipe.instrument is not None and self.instrument is None:
            self.instrument = recipe.instrument
        if recipe.atmosphere is not None and self.atmosphere is None:
            self.atmosphere = recipe.atmosphere
        if recipe.solution is not None and not self.solution:
            self.solution = recipe.solution
        if recipe.steps and not self.steps:
            self.steps = recipe.steps
            for step in self.steps:
                step.start_time = None

    def _collect_step_solutions(self) -> None:
        """Populate the entry-level solution list with any solutions defined on steps (cross-reference)."""
        if not self.steps:
            return
        existing_refs: set[str] = set()
        if self.solution:
            for sol in self.solution:
                ref = getattr(sol, 'solution', None)
                if ref is not None:
                    existing_refs.add(
                        getattr(ref, 'm_proxy_value', None) or str(ref)
                    )
        for step in self.steps:
            for step_sol in getattr(step, 'solution', None) or []:
                ref = getattr(step_sol, 'solution', None)
                if ref is None:
                    continue
                val = getattr(ref, 'm_proxy_value', None) or str(ref)
                if val not in existing_refs:
                    existing_refs.add(val)
                    if self.solution is None:
                        self.solution = []
                    self.solution.append(
                        INLPrecursorSolution.m_from_dict(step_sol.m_to_dict())
                    )

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

        self._collect_step_solutions()

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
        section_def='INLSpinCoatingRecipeReference',
        description='Reference to an INL spin coating recipe.',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Spin Coating'
        super().normalize(archive, logger)


class INLSpinCoatingRecipe(INLSpinCoating, EntryData):
    """Reusable recipe template for spin coating — inherits all INLSpinCoating fields."""

    m_def = Section(
        label='INL Spin Coating Recipe',
        categories=[INLWetDepositionCategory],
        a_eln=dict(
            hide=[
                'lab_id',
                'location',
                'tags',
                'start_time',
                'end_time',
                'datetime',
                'instruments',
                'samples',
                'substrate',
                'sample',
                'creates_new_thin_film',
                'apply_recipe',
                'recipe',
                'operator',
                'method',
            ]
        ),
    )


class INLSpinCoatingRecipeReference(WetDepositionRecipeReference):
    reference = Quantity(
        type=INLSpinCoatingRecipe,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Spin coating recipe',
        ),
    )


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
        self,
        recipe: 'INLSlotDieCoatingRecipe',
        archive: 'EntryArchive',
        logger: 'BoundLogger',
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
        self,
        recipe: 'INLBladeCoatingRecipe',
        archive: 'EntryArchive',
        logger: 'BoundLogger',
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
        self,
        recipe: 'INLInkjetPrintingRecipe',
        archive: 'EntryArchive',
        logger: 'BoundLogger',
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
        self,
        recipe: 'INLSprayPyrolysisRecipe',
        archive: 'EntryArchive',
        logger: 'BoundLogger',
    ) -> None:
        # Spray pyrolysis parameters are covered by SprayPyrolysisProperties;
        # copy common fields manually to avoid propagating spin-coating-oriented steps.
        if recipe.instrument is not None and self.instrument is None:
            self.instrument = recipe.instrument
        if recipe.atmosphere is not None and self.atmosphere is None:
            self.atmosphere = recipe.atmosphere
        if recipe.solution is not None and not self.solution:
            self.solution = recipe.solution
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
        self,
        recipe: 'INLDipCoatingRecipe',
        archive: 'EntryArchive',
        logger: 'BoundLogger',
    ) -> None:
        super()._apply_recipe(recipe, archive, logger)
        if recipe.properties is not None and self.properties is None:
            self.properties = recipe.properties

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Dip Coating'
        super().normalize(archive, logger)


class INLChemicalBathDeposition(INLThinFilmDeposition):
    """ELN schema for chemical bath deposition (CBD) of thin films.

    Supports two CBD types:
    - Type 1 (in-situ prep): Use 'steps' field with INLCBDBathPreparationStep entries to record bath preparation procedure.
    - Type 2 (pre-mixed): Use 'bath_composition' field with pre-made solutions and their volumes.
    """

    m_def = Section(
        links=['http://purl.obolibrary.org/obo/CHMO_0001465'],
    )

    bath_composition = SubSection(
        section_def=INLCBDComponentMixture,
        repeats=True,
        description=(
            'Bath composition for Type 2 (pre-mixed) CBD: '
            'pre-made solutions and their volumes mixed into the bath. '
            'Leave empty for Type 1 (in-situ prep) depositions.'
        ),
    )

    create_solutions = Quantity(
        type=bool,
        default=False,
        description=(
            'If True, auto-create Solution entries from the solution_template '
            'in each bath_composition component and wire in the references. '
            'Only applies to Type 2 (pre-mixed) depositions.'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
            label='Create solutions from templates',
        ),
    )

    ammonium_hydroxide_solution = Quantity(
        type=NMPSolution,
        description=(
            'Reference to the NH\u2084OH (ammonium hydroxide) stock solution used '
            'in this deposition. When set, any template reagent whose name contains '
            '"nh4oh" or "ammonium" will be linked to this solution via a '
            'SolutionComponentReference instead of a plain component name.'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='NH\u2084OH stock solution',
        ),
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
        self,
        recipe: 'INLChemicalBathDepositionRecipe',
        archive: 'EntryArchive',
        logger: 'BoundLogger',
    ) -> None:
        # CBD uses direct parameter fields rather than process steps; copy common
        # fields manually to avoid propagating spin-coating-oriented steps.
        if recipe.instrument is not None and self.instrument is None:
            self.instrument = recipe.instrument
        if recipe.atmosphere is not None and self.atmosphere is None:
            self.atmosphere = recipe.atmosphere
        if recipe.solution is not None and not self.solution:
            self.solution = recipe.solution
        if recipe.steps and not self.steps:
            self.steps = recipe.steps
            for step in self.steps:
                step.start_time = None
        # CBD-specific fields
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
        # Type 2 bath composition template
        if recipe.bath_composition is not None and not self.bath_composition:
            self.bath_composition = recipe.bath_composition

    def _create_solutions_from_templates(
        self, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        """Auto-create Solution entries from bath_composition solution_templates.

        For each bath_composition component that has a solution_template but no
        solution reference, create a nomad-material-processing Solution YAML file
        and set the reference on the component.
        """
        from nomad.units import ureg

        if isinstance(archive.m_context, ClientContext):
            logger.warning(
                'INLChemicalBathDeposition: running in ClientContext — '
                'cannot create Solution entries. Skipping.'
            )
            return

        start_time = getattr(self, 'start_time', None)
        date_str = (
            start_time.strftime('%y%m%d')
            if start_time is not None
            else _date.today().strftime('%y%m%d')
        )
        entry_base = (getattr(self, 'name', None) or 'cbd').replace(' ', '_')

        for i, component in enumerate(self.bath_composition or []):
            tmpl = getattr(component, 'solution_template', None)
            if tmpl is None:
                continue
            if getattr(component, 'solution', None) is not None:
                continue  # already linked

            sol_name = getattr(tmpl, 'name', None) or f'solution_{i + 1}'
            base_filename = f'{date_str}_{entry_base}_{sol_name.replace(" ", "_")}'

            # Build a proper NMPSolution object so NOMAD serialises it correctly
            sol = NMPSolution()
            sol.name = sol_name

            # NOMAD quantity getters may return pint Quantities (not plain floats).
            # Use .magnitude to extract the numeric value in the declared unit before
            # re-attaching ureg units, otherwise we'd get ml² / g² / etc.
            def _mag(val):
                return val.magnitude if hasattr(val, 'magnitude') else float(val)

            total_vol = getattr(tmpl, 'total_volume', None)
            if total_vol is not None:
                sol.measured_volume = _mag(total_vol) * ureg.ml  # declared ml → liter

            # Add reagents as components; Solution.normalize() distributes them.
            # NH4OH is a special case: if a stock solution is referenced on this
            # deposition, use SolutionComponentReference so NOMAD can expand its
            # own solvents/solutes into the created solution (scaled by volume).
            nh4oh_ref = getattr(self, 'ammonium_hydroxide_solution', None)
            for reagent in getattr(tmpl, 'reagents', None) or []:
                reagent_name = getattr(reagent, 'name', None) or 'unknown'
                volume_val = getattr(reagent, 'volume', None)
                reagent_lower = reagent_name.lower()
                is_ammonia = any(
                    k in reagent_lower for k in ('nh4oh', 'ammonium', 'ammonia')
                )
                if is_ammonia and nh4oh_ref is not None:
                    # Link to the existing stock solution, applying the template volume
                    comp = NMPSolutionComponentReference()
                    comp.system = nh4oh_ref
                    comp.name = reagent_name
                    if volume_val is not None:
                        comp.volume = _mag(volume_val) * ureg.ml
                else:
                    comp = NMPSolutionComponent()
                    comp.name = reagent_name
                    comp.substance_name = reagent_name
                    comp.component_role = 'Solute'
                    mass_val = getattr(reagent, 'mass', None)
                    if mass_val is not None:
                        comp.mass = _mag(mass_val) * ureg.g  # declared g → kg
                    if volume_val is not None:
                        comp.volume = _mag(volume_val) * ureg.ml  # declared ml → liter
                sol.m_add_sub_section(NMPSolution.components, comp)

            # Add solvent as a Solvent component; use total_volume as its volume
            solvent_name = getattr(tmpl, 'solvent', None) or 'water'
            if solvent_name:
                solvent_comp = NMPSolutionComponent()
                solvent_comp.name = solvent_name
                solvent_comp.substance_name = solvent_name
                solvent_comp.component_role = 'Solvent'
                if total_vol is not None:
                    solvent_comp.volume = _mag(total_vol) * ureg.ml
                sol.m_add_sub_section(NMPSolution.components, solvent_comp)

            sol_filename, sol_archive = create_filename(
                base_filename, sol, 'Solution', archive, logger
            )
            if not archive.m_context.raw_path_exists(sol_filename):
                sol_ref = create_archive(
                    sol_archive.m_to_dict(),
                    archive.m_context,
                    sol_filename,
                    'yaml',
                    logger,
                )
            else:
                sol_ref = get_hash_ref(archive.m_context.upload_id, sol_filename)

            if sol_ref:
                component.solution = sol_ref
                logger.info(
                    f'INLChemicalBathDeposition: created Solution entry {sol_filename!r}.'
                )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'Chemical Bath Deposition'
        super().normalize(archive, logger)
        if self.create_solutions:
            self._create_solutions_from_templates(archive, logger)
            self.create_solutions = False


m_package.__init_metainfo__()
