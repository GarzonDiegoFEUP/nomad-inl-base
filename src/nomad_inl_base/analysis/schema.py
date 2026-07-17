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


def _disable_notebook_url_fetch(archive, notebook_path, logger) -> None:
    """
    Comments out the `url=NOMAD_ANALYSIS_BASE_URL` argument in the generated
    notebook's `get_entry_data` header cell.

    The explicit URL is not needed (and can prevent the API call from working,
    e.g. inside a JupyterHub container) since `get_entry_data` already defaults
    to the local NOMAD client URL. `nomad_analysis`'s `write_header_cells`
    hardcodes this argument and is not overridable via subclassing, so this
    patch is applied to the generated notebook file directly. It only needs to
    run once, right after a notebook is (re)generated, since header cells are
    not rewritten afterwards.
    """
    if not notebook_path:
        return
    try:
        with archive.m_context.raw_file(notebook_path, 'r') as nb_file:
            notebook = nbf.read(nb_file, as_version=4)

        changed = False
        for cell in notebook.cells:
            tags = cell.get('metadata', {}).get('tags', [])
            if 'nomad-analysis-header' not in tags or 'get_entry_data' not in cell.source:
                continue
            new_lines = []
            for line in cell.source.splitlines(keepends=True):
                if 'url=NOMAD_ANALYSIS_BASE_URL' in line and not line.lstrip().startswith(
                    '#'
                ):
                    stripped = line.lstrip()
                    prefix = line[: len(line) - len(stripped)]
                    new_lines.append(f'{prefix}# {stripped}')
                    changed = True
                else:
                    new_lines.append(line)
            cell.source = ''.join(new_lines)

        if not changed:
            return

        with archive.m_context.raw_file(notebook_path, 'w') as nb_file:
            nbf.write(notebook, nb_file)
        archive.m_context.process_updated_raw_file(notebook_path, allow_modify=True)
    except Exception as e:
        logger.warning(
            f'Could not disable the NOMAD_ANALYSIS_BASE_URL fetch in notebook '
            f'"{notebook_path}": {e!r}',
            exc_info=True,
        )


class EQEJupyterAnalysis(JupyterAnalysis, EntryData):
    """Extends JupyterAnalysis with EQE-specific analysis functions."""

    m_def = Section(
        label='EQE Jupyter Analysis',
        description='Jupyter notebook analysis for External Quantum Efficiency data.',
        a_display=SectionDisplayAnnotation(
            order=[
                'name',
                'datetime',
                'lab_id',
                'location',
                'description',
                'method',
                'template',
                'notebook',
                'trigger_generate_notebook',
                'query_for_inputs',
                'trigger_reset_inputs',
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

        source = 'eqe_analysis(analysis.inputs)\n'
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        return cells

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        self.method = 'EQE'
        had_notebook = bool(self.notebook)
        super().normalize(archive, logger)
        if not had_notebook and self.notebook:
            _disable_notebook_url_fetch(archive, self.notebook, logger)


class SolarCellJupyterAnalysis(JupyterAnalysis, EntryData):
    """Extends JupyterAnalysis with Solar Cell IV-specific analysis functions."""

    m_def = Section(
        label='Solar Cell IV Jupyter Analysis',
        description='Jupyter notebook analysis for Solar Cell IV data.',
        a_display=SectionDisplayAnnotation(
            order=[
                'name',
                'datetime',
                'lab_id',
                'location',
                'description',
                'method',
                'template',
                'notebook',
                'trigger_generate_notebook',
                'query_for_inputs',
                'trigger_reset_inputs',
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

        source = 'solar_cell_iv_analysis(analysis.inputs)\n'
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        return cells

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        self.method = 'SolarCellIV'
        had_notebook = bool(self.notebook)
        super().normalize(archive, logger)
        if not had_notebook and self.notebook:
            _disable_notebook_url_fetch(archive, self.notebook, logger)


class GDOESJupyterAnalysis(JupyterAnalysis, EntryData):
    """Extends JupyterAnalysis with GDOES-specific analysis functions."""

    m_def = Section(
        label='GDOES Jupyter Analysis',
        description='Jupyter notebook analysis for GDOES depth profile data.',
        a_display=SectionDisplayAnnotation(
            order=[
                'name',
                'datetime',
                'lab_id',
                'location',
                'description',
                'method',
                'template',
                'notebook',
                'trigger_generate_notebook',
                'query_for_inputs',
                'trigger_reset_inputs',
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

        source = 'gdoes_analysis(analysis.inputs)\n'
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        return cells

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        self.method = 'GDOES'
        had_notebook = bool(self.notebook)
        super().normalize(archive, logger)
        if not had_notebook and self.notebook:
            _disable_notebook_url_fetch(archive, self.notebook, logger)


class INLXRDJupyterAnalysis(JupyterAnalysis, EntryData):
    """Extends JupyterAnalysis with XRD-specific analysis functions."""

    m_def = Section(
        label='INL XRD Jupyter Analysis',
        description='Jupyter notebook analysis for X-Ray Diffraction data.',
        a_display=SectionDisplayAnnotation(
            order=[
                'name',
                'datetime',
                'lab_id',
                'location',
                'description',
                'method',
                'template',
                'notebook',
                'trigger_generate_notebook',
                'query_for_inputs',
                'trigger_reset_inputs',
            ],
        ),
    )

    def write_predefined_cells(self, archive, logger):
        cells = []

        comment = '# XRD analysis functions\n\n'
        funcs = get_function_source(category_name='XRD', module=_analysis_source)
        source = comment + list_to_string(funcs)
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        source = 'xrd_voila_analysis(analysis.inputs)\n'
        cells.append(
            nbf.v4.new_code_cell(
                source=source,
                metadata={'tags': ['nomad-analysis-predefined']},
            )
        )

        return cells

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        self.method = 'XRD'
        had_notebook = bool(self.notebook)
        super().normalize(archive, logger)
        if not had_notebook and self.notebook:
            _disable_notebook_url_fetch(archive, self.notebook, logger)


m_package.__init_metainfo__()
