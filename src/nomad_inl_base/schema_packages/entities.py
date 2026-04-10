from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

import numpy as np
from nomad.datamodel.data import ArchiveSection, EntryData, EntryDataCategory
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import (
    CompositeSystem,
    CompositeSystemReference,
    Instrument,
    InstrumentReference,
    SystemComponent,
)
from nomad.metainfo import (
    Category,
    Datetime,
    MEnum,
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

m_package = SchemaPackage()


class INLEntityCategory(EntryDataCategory):
    m_def = Category(label='INL Entities', categories=[EntryDataCategory])


class INLSample(CompositeSystem):
    """Marker base class for all INL sample entities (substrate, thin film, stack)."""

    m_def = Section(label='INL Sample')

    location = Quantity(
        type=str,
        description='Physical location of the sample (e.g. fridge, glovebox, characterization lab).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity, label='Location'),
    )
    status = Quantity(
        type=MEnum('active', 'in use', 'consumed', 'broken', 'archived'),
        description='Current status of the sample.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.EnumEditQuantity, label='Status'),
    )


class INLSampleReference(CompositeSystemReference):
    """Reference to any INL sample entity (substrate, thin film, or stack)."""

    m_def = Section(hide=['name', 'lab_id'])

    reference = Quantity(
        type=INLSample,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Sample',
        ),
    )


class INLSubstrate(Substrate, INLSample, EntryData):
    m_def = Section(label='INL Substrate', categories=[INLEntityCategory])

    material = Quantity(
        type=str,
        description='The material of the substrate.',
        a_eln=ELNAnnotation(component='StringEditQuantity', label='Material'),
        default='SLG',
    )

    geometry = SubSection(section_def=Geometry)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.geometry is None:
            substrate_geo = RectangleCuboid()
            substrate_geo.height = 1 * ureg('mm')
            substrate_geo.width = 2.5 * ureg('cm')
            substrate_geo.length = 2.5 * ureg('cm')
            self.geometry = substrate_geo


class INLSubstrateReference(SubstrateReference):
    reference = Quantity(
        type=INLSubstrate,
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


class INLThinFilm(ThinFilm, INLSample, EntryData):
    """Shared thin film entity for all INL deposition methods."""

    m_def = Section(label='INL Thin Film', categories=[INLEntityCategory])

    material = Quantity(
        type=str,
        description='The material of the thin film.',
        a_eln=ELNAnnotation(component='StringEditQuantity', label='Material'),
    )

    thickness = Quantity(
        type=np.float64,
        description='The thickness of the thin film.',
        a_eln=ELNAnnotation(
            component='NumberEditQuantity',
            label='Thickness',
            defaultDisplayUnit='nm',
        ),
        unit='meter',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.geometry is None:
            self.geometry = RectangleCuboid()

        if self.thickness is not None:
            self.geometry.height = self.thickness

        if self.material is None and self.components and self.components[0] is not None:
            self.material = self.components[0].name


class INLThinFilmReference(ThinFilmReference):
    """Reference to an INLThinFilm entry."""

    reference = Quantity(
        type=INLThinFilm,
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


class INLThinFilmStack(ThinFilmStack, INLSample, EntryData):
    """Shared thin film stack entity for all INL deposition methods."""

    m_def = Section(label='INL Thin Film Stack', categories=[INLEntityCategory])

    layers = SubSection(section_def=INLThinFilmReference, repeats=True)

    substrate = SubSection(section_def=INLSubstrateReference)

    raw_path = Quantity(
        type=str,
        description='Raw file path of this entry (set automatically during normalization).',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        if archive.metadata and getattr(archive.metadata, 'mainfile', None):
            self.raw_path = archive.metadata.mainfile

        self.components = []
        if self.layers:
            self.components = [
                SystemComponent(system=layer.reference)
                for layer in self.layers
                if layer.reference
            ]

        if self.substrate is not None and self.substrate.reference is not None:
            self.components.append(SystemComponent(system=self.substrate.reference))
            for layer in self.layers:
                if layer.reference and layer.reference.geometry is not None:
                    if self.substrate.reference.geometry is not None:
                        layer.reference.geometry.width = (
                            self.substrate.reference.geometry.width
                        )
                        layer.reference.geometry.length = (
                            self.substrate.reference.geometry.length
                        )

        super().normalize(archive, logger)


class INLThinFilmStackReference(ThinFilmStackReference):
    """Reference to an INLThinFilmStack entry."""

    reference = Quantity(
        type=INLThinFilmStack,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Thin Film Stack',
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.reference is not None:
            if self.reference.name is not None:
                self.name = self.reference.name
            if self.reference.lab_id is not None:
                self.lab_id = self.reference.lab_id


class INLMaintenanceLog(ArchiveSection):
    """A single maintenance event for an instrument."""

    m_def = Section(label='Maintenance Log Entry')

    date = Quantity(
        type=Datetime,
        description='Date and time of the maintenance event.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.DateTimeEditQuantity,
            label='Date',
        ),
    )

    performed_by = Quantity(
        type=str,
        description='Name of the person who performed the maintenance.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Performed by',
        ),
    )

    description = Quantity(
        type=str,
        description='Description of the maintenance performed.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.RichTextEditQuantity,
            label='Description',
        ),
    )


class INLInstrument(Instrument, EntryData):
    """INL instrument entity with supplier information."""

    m_def = Section(label='INL Instrument', categories=[INLEntityCategory])

    supplier = Quantity(
        type=str,
        description='Manufacturer or supplier of the instrument.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity, label='Supplier'),
    )

    lab_id = Quantity(
        type=str,
        description='Lab identifier where the instrument is located.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity, label='Lab ID'),
    )

    maintenance_log = SubSection(
        section_def=INLMaintenanceLog,
        repeats=True,
        description='Chronological log of maintenance events for this instrument.',
    )


class INLInstrumentReference(InstrumentReference):
    """Reference to an INLInstrument entry."""

    reference = Quantity(
        type=INLInstrument,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Instrument',
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.reference is not None:
            if self.reference.name is not None:
                self.name = self.reference.name
            if self.reference.lab_id is not None:
                self.lab_id = self.reference.lab_id


class INLSampleFragment(INLSample, EntryData):
    """A fragment cut or broken from a parent sample at any stage of preparation."""

    m_def = Section(label='INL Sample Fragment', categories=[INLEntityCategory])

    parent_sample = Quantity(
        type=INLSample,
        description='The parent sample (substrate, thin film, or stack) this fragment was cut from.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Parent Sample',
        ),
    )
    fraction = Quantity(
        type=str,
        description='Fraction label describing the piece size (e.g. "1/2", "1/4", "triangle").',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity, label='Fraction'),
    )
    cut_date = Quantity(
        type=Datetime,
        description='Date when this fragment was cut or separated from the parent.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.DateTimeEditQuantity,
            label='Cut Date',
        ),
    )


class INLSampleFragmentReference(INLSampleReference):
    """Reference to an INLSampleFragment entry."""

    reference = Quantity(
        type=INLSampleFragment,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Sample Fragment',
        ),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        if self.reference is not None:
            if self.reference.name is not None:
                self.name = self.reference.name
            if self.reference.lab_id is not None:
                self.lab_id = self.reference.lab_id


class INLGraphiteBox(INLInstrument):
    """A graphite box used in tube furnace annealing processes."""

    m_def = Section(label='INL Graphite Box', categories=[INLEntityCategory])

    geometry = SubSection(
        section_def=RectangleCuboid,
        description='Dimensions of the graphite box (length × width × height).',
    )


class INLGraphiteBoxReference(INLInstrumentReference):
    """Reference to an INLGraphiteBox entry."""

    reference = Quantity(
        type=INLGraphiteBox,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Graphite Box',
        ),
    )


m_package.__init_metainfo__()
