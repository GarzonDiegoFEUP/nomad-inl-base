from nomad.config.models.plugins import SchemaPackageEntryPoint


class INLAnalysisPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_inl_base.analysis.schema import m_package

        return m_package


analysis_entry_point = INLAnalysisPackageEntryPoint(
    name='INL Analysis',
    description='JupyterAnalysis schemas for INL characterization (EQE, Solar Cell IV, GDOES).',
)
