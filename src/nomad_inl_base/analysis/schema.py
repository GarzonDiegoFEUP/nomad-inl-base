"""
JupyterAnalysis subclasses for INL characterization measurements.

Each class generates a Jupyter notebook pre-populated with analysis functions
specific to its measurement type (EQE, Solar Cell IV, GDOES).
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

import nbformat as nbf
from nomad.datamodel.data import EntryData
from nomad.datamodel.metainfo.annotations import SectionDisplayAnnotation
from nomad.metainfo import SchemaPackage, Section
from nomad_analysis.jupyter.schema import JupyterAnalysis
from nomad_analysis.utils import get_function_source, list_to_string

import nomad_inl_base.analysis.analysis_source as _analysis_source

m_package = SchemaPackage()


class EQEJupyterAnalysis(JupyterAnalysis, EntryData):
    """Extends JupyterAnalysis with EQE-specific analysis functions."""

    m_def = Section(
        label='EQE Jupyter Analysis',
        description='Jupyter notebook analysis for External Quantum Efficiency data.',
        a_display=SectionDisplayAnnotation(
            order=[
                'name', 'datetime', 'lab_id', 'location', 'description',
                'method', 'template', 'notebook', 'trigger_generate_notebook',
                'query_for_inputs', 'trigger_reset_inputs',
            ],
        ),
    )

    def write_predefined_cells(self, archive, logger):
        cells = []

        comment = '# EQE analysis functions\n\n'
        funcs = get_function_source(category_name='EQE', module=_analysis_source)
        source = comment + list_to_string(funcs)
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        source = 'eqe_analysis(analysis.data.inputs)\n'
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        return cells

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        self.method = 'EQE'
        super().normalize(archive, logger)


class SolarCellJupyterAnalysis(JupyterAnalysis, EntryData):
    """Extends JupyterAnalysis with Solar Cell IV-specific analysis functions."""

    m_def = Section(
        label='Solar Cell IV Jupyter Analysis',
        description='Jupyter notebook analysis for Solar Cell IV data.',
        a_display=SectionDisplayAnnotation(
            order=[
                'name', 'datetime', 'lab_id', 'location', 'description',
                'method', 'template', 'notebook', 'trigger_generate_notebook',
                'query_for_inputs', 'trigger_reset_inputs',
            ],
        ),
    )

    def write_predefined_cells(self, archive, logger):
        cells = []

        comment = '# Solar Cell IV analysis functions\n\n'
        funcs = get_function_source(category_name='SolarCell', module=_analysis_source)
        source = comment + list_to_string(funcs)
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        source = 'solar_cell_iv_analysis(analysis.data.inputs)\n'
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        return cells

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        self.method = 'SolarCellIV'
        super().normalize(archive, logger)


class GDOESJupyterAnalysis(JupyterAnalysis, EntryData):
    """Extends JupyterAnalysis with GDOES-specific analysis functions."""

    m_def = Section(
        label='GDOES Jupyter Analysis',
        description='Jupyter notebook analysis for GDOES depth profile data.',
        a_display=SectionDisplayAnnotation(
            order=[
                'name', 'datetime', 'lab_id', 'location', 'description',
                'method', 'template', 'notebook', 'trigger_generate_notebook',
                'query_for_inputs', 'trigger_reset_inputs',
            ],
        ),
    )

    def write_predefined_cells(self, archive, logger):
        cells = []

        comment = '# GDOES depth-profile analysis functions\n\n'
        funcs = get_function_source(category_name='GDOES', module=_analysis_source)
        source = comment + list_to_string(funcs)
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        source = 'gdoes_analysis(analysis.data.inputs)\n'
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        return cells

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        self.method = 'GDOES'
        super().normalize(archive, logger)


m_package.__init_metainfo__()
