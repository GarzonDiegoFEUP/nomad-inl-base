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

from nomad.config import config
from nomad.datamodel.data import Schema
from nomad.metainfo import Quantity, SchemaPackage

configuration = config.get_plugin_entry_point(
    'nomad_inl_base.schema_packages:schema_package_entry_point'
)

m_package = SchemaPackage()


class PotentiostatMeasurement(Schema):
    m_def = Section(
        links=['https://w3id.org/nfdi4cat/voc4cat_0007206'],
    )

    data_file = Quantity(
        type=str,
        a_eln=dict(component='FileEditQuantity'),
        a_browser=dict(adaptor='RawFileAdaptor'),
    )

    station = Quantity(type=str, a_eln=dict(component='StringEditQuantity'))

    function = Quantity(type=str, a_eln=dict(component='StringEditQuantity'))

    environment = Quantity(
        links=['https://w3id.org/nfdi4cat/voc4cat_0007223'],
        type=Reference(Environment.m_def),
        a_eln=dict(component='ReferenceEditQuantity'),
    )

    setup = Quantity(
        links=['https://w3id.org/nfdi4cat/voc4cat_0007230'],
        type=Reference(ElectroChemicalSetup.m_def),
        a_eln=dict(component='ReferenceEditQuantity'),
    )

    connected_experiments = Quantity(
        type=Reference(SectionProxy('PotentiostatMeasurement')),
        shape=['*'],
        a_eln=dict(component='ReferenceEditQuantity'),
    )

    pretreatment = SubSection(section_def=VoltammetryCycle)

    setup_parameters = SubSection(section_def=PotentiostatSetup)

    properties = SubSection(section_def=PotentiostatProperties)

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        logger.info('NewSchema.normalize', parameter=configuration.parameter)
        self.message = f'Hello {self.name}!'


m_package.__init_metainfo__()
