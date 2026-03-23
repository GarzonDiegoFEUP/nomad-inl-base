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
        from nomad_inl_base.schema_packages.crystaLLM import m_package

        return m_package


crystaLLM_entry_point = CrystaLLMStructureEntryPoint(
    name='CrystaLLM Structure',
    description='CrystaLLM Structure entry point configuration.',
)

class WetDepositionPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_inl_base.schema_packages.wet_deposition import m_package

        return m_package


wet_deposition_entry_point = WetDepositionPackageEntryPoint(
    name='INL Wet Deposition',
    description='ELN schemas for wet deposition methods (spin, slot-die, blade, inkjet, spray pyrolysis, dip coating).',
)


class INLCharacterizationPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_inl_base.schema_packages.characterization import m_package

        return m_package


characterization_entry_point = INLCharacterizationPackageEntryPoint(
    name='INL Characterization',
    description='INL characterization measurement schemas (XRD, UV-Vis).',
)


class INLEntitiesPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_inl_base.schema_packages.entities import m_package

        return m_package


entities_entry_point = INLEntitiesPackageEntryPoint(
    name='INL Entities',
    description='Shared INL entity schemas (INLSubstrate, etc.) usable across all INL processes.',
)


class INLCleaningPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_inl_base.schema_packages.cleaning import m_package

        return m_package


cleaning_entry_point = INLCleaningPackageEntryPoint(
    name='INL Cleaning',
    description='ELN schemas for substrate cleaning (INLCleaning, INLCleaningRecipe).',
)


class BatteriesPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_inl_base.schema_packages.batteries import m_package

        return m_package


batteries_entry_point = BatteriesPackageEntryPoint(
    name='INL Batteries',
    description='ELN schemas and CSV parser for the PC03 CathodeChamber sputtering system (battery materials).',
)
