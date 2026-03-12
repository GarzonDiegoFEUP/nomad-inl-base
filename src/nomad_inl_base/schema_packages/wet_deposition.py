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
from nomad.datamodel.metainfo.basesections import InstrumentReference
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
    ThinFilmStackReference,
)

m_package = SchemaPackage()


class INLWetDepositionCategory(EntryDataCategory):
    m_def = Category(label='INL Wet Deposition', categories=[EntryDataCategory])


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

    thin_film_stack = SubSection(section_def=ThinFilmStackReference)

    solution = SubSection(
        section_def=PrecursorSolution,
        repeats=True,
    )

    annealing = SubSection(section_def=Annealing)

    quenching = SubSection(section_def=Quenching)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        if not self.method:
            self.method = 'Wet Deposition'
        super().normalize(archive, logger)


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
