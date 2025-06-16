from nomad.config.models.plugins import SchemaPackageEntryPoint
from pydantic import Field


class NewSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    parameter: int = Field(0, description='Custom configuration parameter')

    def load(self):
        from nomad_inl_base.schema_packages.schema_package import m_package

        return m_package


schema_package_entry_point = NewSchemaPackageEntryPoint(
    name='NewSchemaPackage',
    description='New schema package entry point configuration.',
)


class CyclicVoltammetryPackageEntryPoint(SchemaPackageEntryPoint):
    parameter: int = Field(0, description='Custom configuration parameter')

    def load(self):
        from nomad_inl_base.schema_packages.cyclic_voltammetry import m_package

        return m_package


cyclic_voltammetry_entry_point = CyclicVoltammetryPackageEntryPoint(
    name='CyclicVoltammetry',
    description='CyclicVoltammetry entry point configuration.',
)


class StarPackageEntryPoint(SchemaPackageEntryPoint):
    parameter: int = Field(0, description='Custom configuration parameter')

    def load(self):
        from nomad_inl_base.schema_packages.star import m_package

        return m_package


star_entry_point = StarPackageEntryPoint(
    name='STAR processes',
    description='STAR processes entry point configuration.',
)

class CrystaLLMStructureEntryPoint(SchemaPackageEntryPoint):
    parameter: int = Field(0, description='Custom configuration parameter')

    def load(self):
        from nomad_inl_base.schema_packages.crystallm_cif import m_package

        return m_package


crystaLLM_entry_point = CrystaLLMStructureEntryPoint(
    name='CrystaLLM Structure',
    description='CrystaLLM Structure entry point configuration.',
)

