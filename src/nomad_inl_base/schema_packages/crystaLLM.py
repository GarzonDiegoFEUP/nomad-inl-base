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


import numpy as np
from nomad.config import config
from nomad.datamodel.data import (
    EntryData,
    EntryDataCategory,
)
from nomad.datamodel.metainfo.annotations import ELNAnnotation
from nomad.metainfo import (
    Category,
    Quantity,
    SchemaPackage,
    Section,
)

from nomad_inl_base.utils import *

configuration = config.get_plugin_entry_point(
    'nomad_inl_base.schema_packages:crystaLLM_entry_point'
)

m_package = SchemaPackage()

class CrystaLLMCategory(EntryDataCategory):
    m_def = Category(label='CrystaLLM', categories=[EntryDataCategory])

class crystal_material(EntryData):
    m_def = Section(
        label='Structure from crystaLLM',
        category=[CrystaLLMCategory],
    )

    input_formula = Quantity(
        type=str,
        description="""The input formula for the CrystaLLM algorithm.""",
        a_eln=ELNAnnotation(component='StringEditQuantity', label='Formula'),
    )

    space_group = Quantity(
        type=MEnum(
            'P6/mmm',
            'Imma',
            'P4_32_12',
            'P4_2/mnm',
            'Fd-3m',
            'P3m1',
            'P-3',
            'P4mm',
            'P4_332',
            'P4/nnc',
            'P2_12_12',
            'Pnn2',
            'Pbcn',
            'P4_2/n',
            'Cm',
            'R3m',
            'Cmce',
            'Aea2',
            'P-42_1m',
            'P-42m',
            'P2_13',
            'R-3',
            'Fm-3',
            'Cmm2',
            'Pn-3n',
            'P6/mcc',
            'P-6m2',
            'P3_2',
            'P-3m1',
            'P3_212',
            'I23',
            'P-62m',
            'P4_2nm',
            'Pma2',
            'Pmma',
            'I-42m',
            'P-31c',
            'Pa-3',
            'Pmmn',
            'Pmmm',
            'P4_2/ncm',
            'I4/mcm',
            'I-4m2',
            'P3_1',
            'Pcc2',
            'Cmcm',
            'I222',
            'Fddd',
            'P312',
            'Cccm',
            'P6_1',
            'F-43c',
            'P6_322',
            'Pm-3',
            'P3_121',
            'P6_4',
            'Ia-3d',
            'Pm-3m',
            'P2_1/c',
            'C222_1',
            'Pc',
            'P4/n',
            'Pba2',
            'Ama2',
            'Pbcm',
            'P31m',
            'Pcca',
            'P222',
            'P-43n',
            'Pccm',
            'P6_422',
            'F23',
            'P42_12',
            'C222',
            'Pnnn',
            'P6_3cm',
            'P4_12_12',
            'P6/m',
            'Fmm2',
            'I4_1/a',
            'P4/mbm',
            'Pmn2_1',
            'P4_2bc',
            'P4_22_12',
            'I-43d',
            'I4/m',
            'P4bm',
            'Fdd2',
            'P3',
            'P6_122',
            'Pnc2',
            'P4_2/mcm',
            'P4_122',
            'Cmc2_1',
            'P-6c2',
            'R32',
            'P4_1',
            'P4_232',
            'Pnna',
            'P422',
            'Pban',
            'Cc',
            'I4_122',
            'P6_3/m',
            'P6_3mc',
            'I4_1/amd',
            'P4_2',
            'P4/nmm',
            'Pmna',
            'P4/m',
            'Fm-3m',
            'P4/mmm',
            'Imm2',
            'P4/ncc',
            'P-62c',
            'Ima2',
            'P6_5',
            'P2/c',
            'P4/nbm',
            'Ibam',
            'P6_522',
            'P6_3/mmc',
            'I4/mmm',
            'Fmmm',
            'P2/m',
            'P-4b2',
            'I-4',
            'C2/m',
            'P4_2/mmc',
            'P4',
            'Fd-3c',
            'P4_3',
            'P2_1/m',
            'I-43m',
            'P-42c',
            'F4_132',
            'Pm',
            'Pccn',
            'P-4n2',
            'P4_132',
            'P23',
            'I4cm',
            'R3c',
            'Amm2',
            'Immm',
            'Iba2',
            'I4',
            'Fd-3',
            'P1',
            'Pbam',
            'P4_2/nbc',
            'Im-3',
            'P4_2/nnm',
            'Pmc2_1',
            'P-31m',
            'R-3m',
            'Ia-3',
            'P622',
            'F222',
            'P2',
            'P-1',
            'Pmm2',
            'P-4',
            'Aem2',
            'P6_222',
            'P-3c1',
            'P4_322',
            'I422',
            'Pnma',
            'P6_3',
            'P3c1',
            'Pn-3',
            'P4nc',
            'P-6',
            'P4/mcc',
            'I2_12_12_1',
            'P4_2/mbc',
            'P31c',
            'Ccc2',
            'P4_2/nmc',
            'P6_3/mcm',
            'C2',
            'Pbca',
            'P-4c2',
            'I4_1cd',
            'P2_1',
            'P3_112',
            'P4_2mc',
            'Pn-3m',
            'C2/c',
            'R3',
            'P-43m',
            'I432',
            'P222_1',
            'I-42d',
            'I-4c2',
            'P6cc',
            'P6_2',
            'P3_221',
            'P321',
            'Pca2_1',
            'I4_1/acd',
            'I4_132',
            'F432',
            'Pna2_1',
            'Ccce',
            'Ibca',
            'P4/mnc',
            'I4_1md',
            'P2_12_12_1',
            'R-3c',
            'I2_13',
            'P-4m2',
            'Pm-3n',
            'I4mm',
            'F-43m',
            'Pnnm',
            'P-42_1c',
            'Cmmm',
            'P6mm',
            'P4_2cm',
            'P4_2/m',
            'Im-3m',
            'Fm-3c',
            'I4_1',
            'P4cc',
            'Cmme',
        ),
        description="""The space group of the crystal material.""",
        a_eln=ELNAnnotation(component='StringEditQuantity', label='Space Group'),
    )

    raw_cif_file = Quantity(
        type=str,
        description="""The raw CIF file generated by the CrystaLLM algorithm.""",
        a_eln=ELNAnnotation(component='StringEditQuantity', label='CIF File'),
    )

    processed_cif_file = Quantity(
        type=str,
        description="""The processed CIF file.""",
        a_eln=ELNAnnotation(component='StringEditQuantity', label='Processed CIF File'),
    )

    model_used = Quantity(
        type=str,
        description="""The model used for the CrystaLLM algorithm.""",
        a_eln=ELNAnnotation(component='StringEditQuantity', label='Model Used'),
    )

    no_cell_units = Quantity(
        type=np.int64,
        description="""The number of cell units in the crystal material.""",
        a_eln=ELNAnnotation(
            component='NumberEditQuantity', label='Number of Cell Units'
        ),
    )

    run_inference = Quantity(
        type=bool,
        default=False,
        description="""Whether to run the CrystaLLM inference algorithm.""",
        a_eln=ELNAnnotation(component='BooleanEditQuantity', label='Run Inference'),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        logger.info('NewSchema.normalize', parameter=configuration.parameter)
        # self.message = f'Hello {self.name}!'

m_package.__init_metainfo__()
