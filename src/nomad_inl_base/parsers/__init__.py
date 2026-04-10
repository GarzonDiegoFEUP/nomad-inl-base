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


class PC04ParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_inl_base.parsers.parser import PC04ChamberParser

        return PC04ChamberParser(**self.dict())


pc04_parser_entry_point = PC04ParserEntryPoint(
    name='PC04ElectrolyteChamberParser',
    description='Parser for PC04 ElectrolyteChamber sputtering system CSV log files.',
    mainfile_name_re=r'.*PC04.*\.[cC][sS][vV]$',
    mainfile_mime_re=r'(text/csv|text/plain|application/csv|application/octet-stream)',
)


class FourPointProbeParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_inl_base.parsers.parser import FourPointProbeParser

        return FourPointProbeParser(**self.dict())


four_point_probe_parser_entry_point = FourPointProbeParserEntryPoint(
    name='FourPointProbeParser',
    description='Parser for 4-point probe sheet resistance Excel files (*4pp.xls / *4pp.xlsx).',
    mainfile_name_re=r'.*4[pP][pP]\.[xX][lL][sS][xX]?$',
    mainfile_mime_re=r'(application/vnd\.ms-excel|application/vnd\.openxmlformats-officedocument\.spreadsheetml\.sheet|application/octet-stream)',
)


class KLATencorProfilerParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_inl_base.parsers.parser import KLATencorProfilerParser

        return KLATencorProfilerParser(**self.dict())


kla_tencor_profiler_parser_entry_point = KLATencorProfilerParserEntryPoint(
    name='KLATencorProfilerParser',
    description='Parser for KLA-Tencor stylus profiler PDF reports (*profile.pdf).',
    mainfile_name_re=r'.*[Pp]rofile\.pdf$',
    mainfile_mime_re=r'application/pdf',
)
