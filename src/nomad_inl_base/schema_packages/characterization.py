from nomad.datamodel.data import EntryData, EntryDataCategory
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import CompositeSystemReference
from nomad.metainfo import Category, Quantity, SchemaPackage, Section, SubSection
from nomad_material_processing.general import ThinFilmStack
from nomad_measurements.transmission.schema import ELNUVVisNirTransmission
from nomad_measurements.xrd.schema import ELNXRayDiffraction

m_package = SchemaPackage()


class INLCharacterizationCategory(EntryDataCategory):
    m_def = Category(label='INL Characterization', categories=[EntryDataCategory])


class INLSampleReference(CompositeSystemReference):
    m_def = Section(hide=['name', 'lab_id'])
    reference = Quantity(
        type=ThinFilmStack,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Sample',
        ),
    )


class INLXRayDiffraction(ELNXRayDiffraction, EntryData):
    m_def = Section(
        label='INL XRD',
        categories=[INLCharacterizationCategory],
    )
    operator = Quantity(
        type=str,
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    samples = SubSection(section_def=INLSampleReference, repeats=True)


class INLUVVisTransmission(ELNUVVisNirTransmission, EntryData):
    m_def = Section(
        label='INL UV-Vis Transmission',
        categories=[INLCharacterizationCategory],
    )
    operator = Quantity(
        type=str,
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    samples = SubSection(section_def=INLSampleReference, repeats=True)


m_package.__init_metainfo__()
