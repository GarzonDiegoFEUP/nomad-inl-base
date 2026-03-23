from datetime import datetime
from typing import (
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import (
        EntryArchive,
    )

import numpy as np
import pandas as pd
from nomad.datamodel.data import EntryData
from nomad.datamodel.datamodel import EntryArchive, EntryMetadata
from nomad.datamodel.metainfo.annotations import ELNAnnotation
from nomad.datamodel.metainfo.basesections import PureSubstanceSection
from nomad.metainfo import Quantity, Section
from nomad.parsing.parser import MatchingParser
from nomad.units import ureg

from nomad_inl_base.schema_packages.batteries import (
    _SCCM_TO_M3S,
    _TORR_TO_PA,
    PC03CathodeChamberDeposition,
    PC03ChamberEnvironment,
    PC03DCPowerSupply,
    PC03GasFlow,
    PC03Pressure,
    PC03RFPowerSupply,
    PC03Source,
    PC03VolumetricFlowRate,
)
from nomad_inl_base.schema_packages.characterization import (
    ChronoamperometryMeasurement,
    CurrentTimeSeries,
    PotentiostatMeasurement,
    ScanTimeSeries,
    VoltageTimeSeries,
)
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
        data_file = mainfile.rsplit('/', maxsplit=1)[-1].split('.xlsx', maxsplit=1)[0].replace(' ', '_')
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
        data_file = mainfile.rsplit('/', maxsplit=1)[-1].split('.xlsx', maxsplit=1)[0].replace(' ', '_')
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
            mainfile.split('.xlsx', maxsplit=1)[0]
            .rsplit('-', maxsplit=1)[-1]
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


class PC03CathodeChamberParser(MatchingParser):
    """
    Parser for PC03 CathodeChamber sputtering system CSV log files.

    CSV format:
      Line 1: meta-column names  (Recording Name, Date Started, User)
      Line 2: meta-values        (All Signals, YYYY-M-D HH-MM-SS, OperatorName)
      Line 3: empty
      Line 4: data column headers (~460 columns)
      Lines 5+: data rows at ~1 Hz

    Files are matched by filename starting with 'PC03'.
    """

    # Offset used to convert Celsius (from CSV) to Kelvin (stored in schema)
    _KELVIN_OFFSET = 273.15
    # Angstrom-to-nm conversion factor (QCM reads in Å)
    _ANG_TO_NM = 0.1

    def parse(self, mainfile: str, archive: EntryArchive, logger) -> None:
        # --- Read 2-line header (metadata) ---
        with open(mainfile, encoding='utf-8', errors='replace') as fh:
            meta_keys = [k.strip() for k in fh.readline().rstrip('\n').split(',')]
            meta_values = [v.strip() for v in fh.readline().rstrip('\n').split(',')]

        meta = dict(zip(meta_keys, meta_values))
        recording_name = meta.get('Recording Name', '')
        operator = meta.get('User', '')
        date_started_str = meta.get('Date Started', '')

        # Parse start datetime: '2026-3-18 14-15-53'
        start_datetime = None
        for fmt in ('%Y-%m-%d %H-%M-%S', '%Y-%m-%d %H:%M:%S'):
            try:
                start_datetime = datetime.strptime(date_started_str, fmt)
                break
            except ValueError:
                continue

        # --- Read time-series data (skip 3-line preamble) ---
        df = pd.read_csv(mainfile, skiprows=3, low_memory=False)

        # --- Helpers ---
        def col(name):
            """Return float64 array for column, or None if absent/all-NaN."""
            if name not in df.columns:
                return None
            arr = pd.to_numeric(df[name], errors='coerce').to_numpy(dtype=np.float64)
            return arr if not np.all(np.isnan(arr)) else None

        def col_bool(name):
            """Return bool array, treating 1/0 as True/False."""
            if name not in df.columns:
                return None
            return pd.to_numeric(df[name], errors='coerce').fillna(0).astype(bool).to_numpy()

        def col_str(name):
            if name not in df.columns:
                return None
            return df[name].astype(str).to_numpy()

        def col_temp(name):
            """Return Kelvin array from a Celsius column."""
            arr = col(name)
            return arr + self._KELVIN_OFFSET if arr is not None else None

        def col_int(name):
            if name not in df.columns:
                return None
            return pd.to_numeric(df[name], errors='coerce').fillna(0).astype(np.int64).to_numpy()

        # --- Timestamps ---
        ts_fmt = '%b-%d-%Y %I:%M:%S.%f %p'
        try:
            ts = pd.to_datetime(df['Time Stamp'], format=ts_fmt)
            t0 = ts.iloc[0]
            timestamps = (ts - t0).dt.total_seconds().to_numpy(dtype=np.float64)
        except Exception:
            timestamps = np.arange(len(df), dtype=np.float64)

        # --- Build entry ---
        entry = PC03CathodeChamberDeposition()
        entry.recording_name = recording_name
        entry.operator = operator
        if start_datetime:
            entry.start_datetime = start_datetime

        entry.timestamps = timestamps

        # Process tracking
        ph = col_str('Process Phase')
        if ph is not None:
            entry.process_phase = ph
        arr = col('Process Time')
        if arr is not None:
            entry.process_time = arr

        # --- Chamber environment (gas flows + pressures) ---
        env = PC03ChamberEnvironment()

        # Main process pressure: Capman value [Pa] + setpoint [Pa]
        capman_arr = col('PC Capman Pressure')
        capman_sp_arr = col('PC Capman Pressure Setpoint')
        if capman_arr is not None or capman_sp_arr is not None:
            p = PC03Pressure()
            if capman_arr is not None:
                p.value = capman_arr * _TORR_TO_PA
            if capman_sp_arr is not None:
                p.set_value = capman_sp_arr * _TORR_TO_PA
            env.pressure = p

        # Additional pressure gauges [Pa]
        for attr, csv_col in [
            ('ion_gauge_pressure', 'PC Ion Gauge Pressure'),
            ('wide_range_gauge_pressure', 'PC Wide Range Gauge'),
            ('roughing_pressure', 'PC Roughing Pressure'),
        ]:
            arr = col(csv_col)
            if arr is not None:
                p = PC03Pressure()
                p.value = arr * _TORR_TO_PA
                setattr(env, attr, p)

        # Base pressure (minimum ion gauge reading, stored in Pa)
        arr = col('PC Ion Gauge Pressure')
        if arr is not None:
            valid = arr[~np.isnan(arr)]
            if len(valid) > 0:
                entry.base_pressure = float(np.min(valid)) * _TORR_TO_PA

        # Substrate shutter
        arr = col_bool('PC Substrate Shutter Open')
        if arr is not None:
            entry.substrate_shutter_open = arr

        # Substrate heater
        for attr, csv_col in [
            ('substrate_temperature', 'Substrate Heater Temperature'),
            ('substrate_temperature_2', 'Substrate Heater Temperature 2'),
            ('substrate_temperature_setpoint', 'Substrate Heater Temperature Setpoint'),
        ]:
            arr = col_temp(csv_col)
            if arr is not None:
                setattr(entry, attr, arr)
        arr = col('Substrate Heater Current')
        if arr is not None:
            entry.substrate_heater_current = arr

        # Substrate rotation
        arr = col('Substrate Rotation_Speed')
        if arr is not None:
            entry.substrate_rotation_speed = arr

        # Substrate bias (Rigel)
        arr = col_bool('Substrate Bias Active')
        if arr is not None:
            entry.substrate_bias_active = arr
        for attr, csv_col in [
            ('substrate_bias_voltage', 'Rigel DC Voltage'),
            ('substrate_bias_current', 'Rigel DC Current'),
            ('substrate_bias_power', 'Rigel DC Power'),
        ]:
            arr = col(csv_col)
            if arr is not None:
                setattr(entry, attr, arr)

        # Thermocouples TC1–TC6
        for i in range(1, 7):
            arr = col_temp(f'TC{i} Temperature')
            if arr is not None:
                setattr(entry, f'tc{i}_temperature', arr)

        # Substrate type (last non-empty value)
        if 'Substrate Type' in df.columns:
            vals = df['Substrate Type'].dropna()
            if len(vals) > 0:
                entry.substrate_type = str(vals.iloc[-1])

        # Gas flows: MFC 1–3 [m³/s]
        for mfc_idx in [1, 2, 3]:
            gf = PC03GasFlow()
            gf.mfc_index = mfc_idx

            gas_col = f'PC MFC {mfc_idx} Gas'
            if gas_col in df.columns:
                names = df[gas_col].dropna()
                if len(names) > 0:
                    gas_name = str(names.iloc[0])
                    gf.name = gas_name
                    gf.gas = PureSubstanceSection(name=gas_name)

            arr = col(f'PC MFC {mfc_idx} Flow')
            arr_sp = col(f'PC MFC {mfc_idx} Setpoint')
            if arr is not None or arr_sp is not None:
                gf.flow_rate = PC03VolumetricFlowRate()
                if arr is not None:
                    gf.flow_rate.value = arr * _SCCM_TO_M3S
                if arr_sp is not None:
                    gf.flow_rate.set_value = arr_sp * _SCCM_TO_M3S

            env.gas_flow.append(gf)

        entry.chamber_environment = env

        # --- Sources 1–4 ---
        # Columns that reveal which power supply type is wired to each source
        _ps_switch_cols = {
            1: ('PC Source 1 Switch-RF-PWS1', 'PC Source 1 Switch-PDC-PWS4'),
            2: (None, None),
            3: ('PC Source 3 Switch-RF-PWS3', 'PC Source 3 Switch-PDC-PWS4'),
            4: ('PC Source 4 Switch-RF-PWS3', 'PC Source 4 Switch-PDC-PWS4'),
        }

        for src_idx in [1, 2, 3, 4]:
            src = PC03Source()
            src.source_index = src_idx

            # Scalar identity fields (read first non-empty value)
            for attr, csv_col in [
                ('material', f'PC Source {src_idx} Material'),
                ('loaded_target', f'PC Source {src_idx} Loaded Target'),
            ]:
                if csv_col in df.columns:
                    vals = df[csv_col].dropna()
                    if len(vals) > 0:
                        setattr(src, attr, str(vals.iloc[0]).strip())

            # Final thickness setpoint (scalar, Å → nm, last recorded value)
            arr = col(f'PC Source {src_idx} Final Thickness Setpoint')
            if arr is not None:
                valid = arr[~np.isnan(arr)]
                if len(valid) > 0:
                    src.final_thickness_setpoint = float(valid[-1]) * self._ANG_TO_NM

            # Time-series arrays
            arr = col_bool(f'PC Source {src_idx} Active')
            if arr is not None:
                src.active = arr

            arr = col_bool(f'PC Source {src_idx} Shutter Open')
            if arr is not None:
                src.shutter_open = arr

            arr = col(f'PC Source {src_idx} Rate')
            if arr is not None:
                src.deposition_rate = arr * self._ANG_TO_NM  # Å/s → nm/s

            arr = col(f'PC Source {src_idx} Thickness')
            if arr is not None:
                src.thickness = arr * self._ANG_TO_NM  # Å → nm

            arr = col(f'PC Source {src_idx} Accumulate Thickness')
            if arr is not None:
                src.accumulated_thickness = arr * self._ANG_TO_NM  # Å → nm

            # Determine power supply type from Switch columns
            rf_col, dc_col = _ps_switch_cols.get(src_idx, (None, None))
            ps_type = 'unknown'
            if rf_col and rf_col in df.columns:
                if pd.to_numeric(df[rf_col], errors='coerce').fillna(0).astype(bool).any():
                    ps_type = 'RF'
            if dc_col and dc_col in df.columns:
                if pd.to_numeric(df[dc_col], errors='coerce').fillna(0).astype(bool).any():
                    ps_type = 'DC-pulsed'
            src.power_supply_type = ps_type

            entry.sources.append(src)

        # --- RF Power Supplies PS1, PS3, PS5 ---
        for ps_idx in [1, 3, 5]:
            ps = PC03RFPowerSupply()
            ps.supply_index = ps_idx
            for attr, csv_col in [
                ('forward_power', f'Power Supply {ps_idx} Fwd Power'),
                ('reflected_power', f'Power Supply {ps_idx} Rfl Power'),
                ('dc_bias', f'Power Supply {ps_idx} DC Bias'),
                ('output_setpoint', f'Power Supply {ps_idx} Output Setpoint'),
                ('load_cap_position', f'Power Supply {ps_idx} Load Cap Position'),
                ('tune_cap_position', f'Power Supply {ps_idx} Tune Cap Position'),
            ]:
                arr = col(csv_col)
                if arr is not None:
                    setattr(ps, attr, arr)
            entry.rf_power_supplies.append(ps)

        # --- DC Pulsed Power Supply PS4 ---
        ps4 = PC03DCPowerSupply()
        for attr, csv_col in [
            ('current', 'Power Supply 4 Current'),
            ('voltage', 'Power Supply 4 Voltage'),
            ('power', 'Power Supply 4 Power'),
            ('output_setpoint', 'Power Supply 4 Output Setpoint'),
            ('current_setpoint', 'Power Supply 4 Current Setpoint'),
            ('voltage_setpoint', 'Power Supply 4 Voltage Setpoint'),
            ('pulse_frequency', 'Power Supply 4 Pulse Frequency'),
        ]:
            arr = col(csv_col)
            if arr is not None:
                setattr(ps4, attr, arr)
        for attr, csv_col in [
            ('arc_count', 'Power Supply 4 DC Count'),
            ('spark_count', 'Power Supply 4 Spark Count'),
        ]:
            arr = col_int(csv_col)
            if arr is not None:
                setattr(ps4, attr, arr)
        entry.dc_power_supply = ps4

        archive.data = entry
        data_file = mainfile.rsplit('/', maxsplit=1)[-1].rsplit('.', maxsplit=1)[0]
        archive.metadata.entry_name = data_file
