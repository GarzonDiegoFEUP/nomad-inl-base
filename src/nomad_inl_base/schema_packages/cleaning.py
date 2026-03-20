from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

from nomad.datamodel.data import EntryDataCategory
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.metainfo import Category, Quantity, SchemaPackage, Section, SubSection
from nomad_material_processing.general import Cleaning, CleaningRecipe, CleaningStep

from nomad_inl_base.schema_packages.entities import INLSubstrate, INLSubstrateReference
from nomad_inl_base.utils import create_archive, create_filename, get_hash_ref

m_package = SchemaPackage()


class INLCleaningCategory(EntryDataCategory):
    m_def = Category(label='INL Cleaning', categories=[EntryDataCategory])


class INLCleaningStep(CleaningStep):
    """A single cleaning step with an optional descriptive name."""

    name = Quantity(
        type=str,
        description='Name or description of this step (e.g. "Acetone", "IPA rinse").',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Step name',
        ),
    )


class INLCleaningRecipe(CleaningRecipe):
    """
    Reusable cleaning recipe template.  Stores the step sequence and a default
    substrate material.  Substrate creation is handled on the experiment entry.
    """

    m_def = Section(
        label='INL Cleaning Recipe',
        categories=[INLCleaningCategory],
        a_eln={
            'hide': [
                'datetime',
                'samples',
                'starting_time',
                'ending_time',
                'location',
                'recipe',
            ]
        },
    )

    material = Quantity(
        type=str,
        description='Default substrate material for this recipe (e.g. "SLG").',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Substrate material',
        ),
    )

    steps = SubSection(section_def=INLCleaningStep, repeats=True)


class INLCleaning(Cleaning):
    """
    ELN schema for substrate cleaning at INL.

    Extends the upstream Cleaning process with:
    - Per-step naming via INLCleaningStep
    - Automatic total duration summed from individual step durations
    - Recipe application (copies steps + substrate material from INLCleaningRecipe)
    - Auto-creation of N INLSubstrate entries named {entry_name}-S01, -S02, ...
      (existing entries are reused; duplicate references are never added)
    """

    m_def = Section(
        label='INL Cleaning',
        categories=[INLCleaningCategory],
        a_eln={'hide': ['samples']},
    )

    recipe = Quantity(
        type=INLCleaningRecipe,
        description='Recipe template to apply to this cleaning experiment.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Recipe',
        ),
    )

    apply_recipe = Quantity(
        type=bool,
        default=False,
        description='If True, copy steps and substrate material from the recipe (once).',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
            label='Apply recipe',
        ),
    )

    substrate_material = Quantity(
        type=str,
        description=(
            'Material of the substrates being cleaned (e.g. "SLG"). '
            'Used when auto-creating substrate entries.'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Substrate material',
        ),
    )

    number_of_substrates = Quantity(
        type=int,
        description='Number of substrates to create when "Create substrates" is enabled.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            label='Number of substrates',
        ),
    )

    create_substrates = Quantity(
        type=bool,
        default=False,
        description=(
            'If True, create one INLSubstrate entry per substrate. '
            'Files that already exist in the upload are reused, not overwritten. '
            'References already present in "substrates" are not duplicated.'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
            label='Create substrates',
        ),
    )

    steps = SubSection(section_def=INLCleaningStep, repeats=True)

    substrates = SubSection(
        section_def=INLSubstrateReference,
        repeats=True,
        description='References to the INLSubstrate entries associated with this cleaning run.',
    )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_recipe(self) -> None:
        """Copy steps and substrate material from the linked recipe (non-destructive)."""
        if not (self.apply_recipe and self.recipe is not None):
            return
        recipe = self.recipe
        if recipe.steps:
            self.steps = recipe.steps
        if recipe.material is not None and self.substrate_material is None:
            self.substrate_material = recipe.material
        self.apply_recipe = False

    def _sum_step_durations(self) -> None:
        """Overwrite self.duration with the sum of all non-None step durations (seconds)."""
        if not self.steps:
            return
        total = sum(
            step.duration for step in self.steps if step.duration is not None
        )
        if total > 0:
            self.duration = total

    def _create_substrates(
        self, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        """
        Create up to `number_of_substrates` INLSubstrate YAML entries named
        ``{base}-S{N:02d}``.

        - If the archive file already exists the existing file is kept as-is.
        - If a reference to that file is already in self.substrates it is skipped.
        - The toggle is reset to False when the run completes.
        """
        if not self.create_substrates:
            return

        n = self.number_of_substrates
        if not n or n < 1:
            logger.warning(
                'create_substrates is True but number_of_substrates is not set or is zero.'
            )
            self.create_substrates = False
            return

        base = (self.name or 'cleaning').replace(' ', '_')
        upload_id = archive.m_context.upload_id

        # Build a set of ref strings already recorded so we never add duplicates
        existing_refs: set[str] = set()
        if self.substrates:
            for sub_ref in self.substrates:
                if sub_ref.reference is not None:
                    proxy = sub_ref.reference
                    val = getattr(proxy, 'm_proxy_value', None) or str(proxy)
                    existing_refs.add(val)

        for i in range(1, n + 1):
            substrate_name = f'{base}-S{i:02d}'

            # Determine the filename that create_filename would use
            sub_filename, sub_archive = create_filename(
                substrate_name, INLSubstrate(), 'Substrate', archive, logger
            )
            # sub_filename == '{substrate_name}.Substrate.archive.yaml'

            expected_ref = get_hash_ref(upload_id, sub_filename)

            # Skip if this ref is already in self.substrates
            if expected_ref in existing_refs:
                continue

            if archive.m_context.raw_path_exists(sub_filename):
                # File exists — just add the reference without touching the file
                ref = expected_ref
            else:
                # Build a fresh substrate and write it
                substrate = INLSubstrate()
                substrate.name = substrate_name
                if self.substrate_material is not None:
                    substrate.material = self.substrate_material

                _sub_filename, sub_archive = create_filename(
                    substrate_name, substrate, 'Substrate', archive, logger
                )

                ref = create_archive(
                    sub_archive.m_to_dict(),
                    archive.m_context,
                    sub_filename,
                    'yaml',
                    logger,
                )

            if ref is None:
                continue

            if self.substrates is None:
                self.substrates = []
            self.substrates.append(INLSubstrateReference(reference=ref))
            existing_refs.add(ref)

        self.create_substrates = False

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self._apply_recipe()
        super().normalize(archive, logger)
        self._sum_step_durations()
        self._create_substrates(archive, logger)


m_package.__init_metainfo__()
