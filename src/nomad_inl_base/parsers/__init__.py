from nomad.config.models.plugins import ParserEntryPoint

# from pydantic import Field


class CVConfigurationParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_inl_base.parsers.parser import CVParser

        return CVParser(**self.dict())


CV_parser_entry_point = CVConfigurationParserEntryPoint(
    name='CVParser',
    description='New parser for getting the data from a CV.',
    mainfile_name_re=r'.*mVs\.xlsx',
    mainfile_mime_re='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
)


class EDConfigurationParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_inl_base.parsers.parser import EDParser

        return EDParser(**self.dict())


ED_parser_entry_point = EDConfigurationParserEntryPoint(
    name='EDParser',
    description='New parser for getting the data from a ED.',
    mainfile_name_re=r'.*ED\.xlsx',
    mainfile_mime_re='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
)


class PC03ParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_inl_base.parsers.parser import PC03CathodeChamberParser

        return PC03CathodeChamberParser(**self.dict())


pc03_parser_entry_point = PC03ParserEntryPoint(
    name='PC03CathodeChamberParser',
    description='Parser for PC03 CathodeChamber sputtering system CSV log files.',
    mainfile_name_re=r'.*PC03.*\.[cC][sS][vV]$',
    mainfile_mime_re=r'(text/csv|text/plain|application/csv|application/octet-stream)',
)
