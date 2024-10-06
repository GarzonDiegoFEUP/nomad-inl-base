from typing import (
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import (
        EntryArchive,
    )

import pandas as pd
from nomad.datamodel.data import EntryData
from nomad.datamodel.datamodel import EntryArchive, EntryMetadata
from nomad.parsing.parser import MatchingParser
from nomad.units import ureg

from nomad_inl_base.schema_packages.cyclic_voltammetry import *
from nomad_inl_base.utils import create_archive, fill_quantity, get_hash_ref


class RawFile_(EntryData):
    m_def = Section(a_eln=None, label='Raw File EPIC')
    name = Quantity(
        type=str,
        a_eln=ELNAnnotation(
            component='StringEditQuantity',
        ),
    )
    file_ = Quantity(
        type=str,
        a_eln=ELNAnnotation(
            component='FileEditQuantity',
        ),
        a_browser={'adaptor': 'RawFileAdaptor'},
        description='EPIC log file list',
    )


class EDParser(MatchingParser):
    def parse(self, mainfile: str, archive: EntryArchive, logger) -> None:
        filetype = 'yaml'
        data_file = mainfile.split('/')[-1].split('.xlsx')[0].replace(' ', '_')
        xlsx = pd.ExcelFile(mainfile)

        data = pd.read_excel(xlsx)
        if 'WE(1).Current (A)' in data.columns:
            data.rename(
                columns={'Corrected time (s)': 'Time', 'WE(1).Current (A)': 'Current'},
                inplace=True,
            )
        else:
            data.rename(
                columns={
                    'Column 1': 't',
                    'Column 2': 'Current',
                    'Column 3': 'Time',
                    'Column 4': 'Index',
                    'Column 5': 'Current range',
                },
                inplace=True,
            )

        # Dummy archive for the data file
        file_reference = get_hash_ref(archive.m_context.upload_id, data_file)

        # create a ED archive
        ED_measurement = ChronoamperometryMeasurement()
        ED_measurement.current = CurrentTimeSeries()
        ED_measurement.current.value = fill_quantity(data, 'Current', 'ampere')
        ED_measurement.current.time = fill_quantity(data, 'Time', 'seconds')

        # create a ED archive
        ED_filename = f'{data_file}.ED_measurement.archive.{filetype}'

        if archive.m_context.raw_path_exists(ED_filename):
            logger.warn(f'Process archive already exists: {ED_filename}')
        else:
            ED_archive = EntryArchive(
                data=ED_measurement if ED_filename else ChronoamperometryMeasurement(),
                # m_context=archive.m_context,
                metadata=EntryMetadata(upload_id=archive.m_context.upload_id),
            )

        create_archive(
            ED_archive.m_to_dict(),
            archive.m_context,
            ED_filename,
            filetype,
            logger,
        )

        archive.data = RawFile_(
            name=data_file + '_raw',
            file_=file_reference,
        )
        archive.metadata.entry_name = data_file.replace('.xlsx', '')


class CVParser(MatchingParser):
    def parse(self, mainfile: str, archive: EntryArchive, logger) -> None:
        filetype = 'yaml'
        data_file = mainfile.split('/')[-1].split('.xlsx')[0].replace(' ', '_')
        xlsx = pd.ExcelFile(mainfile)

        data = pd.read_excel(xlsx)
        if 'WE(1).Potential (V)' in data.columns:
            data.rename(
                columns={
                    'WE(1).Potential (V)': 'Potential',
                    'WE(1).Current (A)': 'Current',
                },
                inplace=True,
            )
        else:
            data.rename(
                columns={
                    'Column 1': 'Potential applied (V)',
                    'Column 2': 'Time (s)',
                    'Column 3': 'Current',
                    'Column 4': 'Potential',
                    'Column 5': 'Scan',
                    'Column 6': 'Index',
                    'Column 7': 'Q+',
                    'Column 8': 'Q-',
                },
                inplace=True,
            )

        rate = float(
            mainfile.split('.xlsx')[0]
            .split('-')[-1]
            .replace(' ', '')
            .replace('mVs', '')
        )

        # create a CV archive

        CV_measurement = PotentiostatMeasurement()
        CV_measurement.voltage = VoltageTimeSeries()
        CV_measurement.current = CurrentTimeSeries()
        CV_measurement.scan = ScanTimeSeries()
        CV_measurement.rate = ureg.Quantity(
            rate,
            ureg('millivolt/second'),
        )

        # Dummy archive for the data file
        file_reference = get_hash_ref(archive.m_context.upload_id, data_file)

        # CV_measurement.data_file = file_reference

        CV_measurement.voltage.value = fill_quantity(data, 'Potential', 'volt')
        CV_measurement.current.value = fill_quantity(data, 'Current', 'ampere')
        CV_measurement.scan.value = fill_quantity(data, 'Scan')
        for values in [
            CV_measurement.voltage,
            CV_measurement.current,
            CV_measurement.scan,
        ]:
            values.time = fill_quantity(data, 'Time (s)', 'seconds')

        # create a CV archive
        CV_filename = f'{data_file}.CV_measurement.archive.{filetype}'

        if archive.m_context.raw_path_exists(CV_filename):
            logger.warn(f'Process archive already exists: {CV_filename}')
        else:
            CV_archive = EntryArchive(
                data=CV_measurement if CV_filename else PotentiostatMeasurement(),
                # m_context=archive.m_context,
                metadata=EntryMetadata(upload_id=archive.m_context.upload_id),
            )

        create_archive(
            CV_archive.m_to_dict(),
            archive.m_context,
            CV_filename,
            filetype,
            logger,
        )

        archive.data = RawFile_(
            name=data_file + '_raw',
            file_=file_reference,
        )
        archive.metadata.entry_name = data_file.replace('.xlsx', '')
