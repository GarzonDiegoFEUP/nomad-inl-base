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
    PC04ElectrolyteChamberDeposition,
    PC04SubstrateAnnealing,
    SputteringChamberEnvironment,
    SputteringDCPowerSupply,
    SputteringGasFlow,
    SputteringPressure,
    SputteringRFPowerSupply,
    SputteringSource,
    SputteringVolumetricFlowRate,
)
from nomad_inl_base.schema_packages.characterization import (
    ChronoamperometryMeasurement,
    CurrentTimeSeries,
    INLFourPointProbe,
    INLFourPointProbeResults,
    INLKLATencorProfiler,
    INLKLATencorProfilerResults,
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


class KLATencorProfilerParser(MatchingParser):
    """
    Parser for KLA-Tencor P-series stylus profiler PDF reports (*profile.pdf).

    The PDF is a generated (non-scanned) report with two regions of interest:
      1. Left panel header — scan parameters (Recipe, Length, Speed, Rate, …)
         and cursor results (St Height, TIR, Width, …)
      2. Bottom table — 2D Surface Parameter Summary (Ra, MaxRa, Rq, Rh)
    """

    _ANGSTROM_TO_M = 1e-10
    _UM_TO_M = 1e-6
    _MG_TO_KG = 1e-6

    def parse(self, mainfile: str, archive: EntryArchive, logger) -> None:
        import re

        import pdfplumber

        filetype = 'yaml'
        data_file = (
            mainfile.rsplit('/', maxsplit=1)[-1]
            .rsplit('.', maxsplit=1)[0]
            .replace(' ', '_')
        )

        with pdfplumber.open(mainfile) as pdf:
            text = pdf.pages[0].extract_text() or ''

        # --- Helper: extract first float after a label ---
        def _find(pattern: str, txt: str = text):
            m = re.search(pattern, txt)
            return m.group(1).strip() if m else None

        # --- Scan parameters (left panel) ---
        # Note: the PDF two-column layout interleaves left/right panel text.
        # "Recipe:" is followed by "Level:" (right column) then the recipe value.
        recipe = _find(r'Recipe:\n[^\n]*\n([^\n:]{2,})')
        site_name = _find(r'Site Name:\s*([A-Za-z0-9_\-\.]+)')
        length_um = _find(r'Length:\s*([\d\.]+)\s*µm')
        speed_um = _find(r'Speed:\s*([\d\.]+)\s*µm/s')
        rate_hz = _find(r'Rate:\s*([\d\.]+)\s*Hz')
        direction = _find(r'Direction\s*([-><]+)')
        repeats_s = _find(r'Repeats:\s*(\d+)')
        force_mg = _find(r'Force:\s*([\d\.]+)\s*mg')
        noise_um = _find(r'Noise Filter:\s*([\d\.]+)\s*µm')

        # --- Cursor / feature results ---
        # St Height: -2883.8 Å  (may be negative, no space after colon)
        st_height_a = _find(r'St Height:\s*([-\d\.]+)\s*\u00c5')

        # --- 2D Surface Parameter Summary table ---
        # Lines like: "Ra  2677.3 Å  Roughness  Roughness"
        ra_a = _find(r'\bRa\b\s+([-\d\.]+)\s*\u00c5')
        max_ra_a = _find(r'\bMaxRa\b\s+([-\d\.]+)\s*\u00c5')
        rq_a = _find(r'\bRq\b\s+([-\d\.]+)\s*\u00c5')
        rh_a = _find(r'\bRh\b\s+([-\d\.]+)\s*\u00c5')

        # --- Datetime from footer ---
        # The footer line uses doubled characters (PDF rendering artefact):
        # "KKLLAA--TTeennccoorr ... AApprr 1100,, 22002266 -- 1111::2200"
        # De-duplicate consecutive identical characters before parsing.
        measurement_dt = None
        for line in text.splitlines():
            if 'KLA' in line or 'KKLLAA' in line:
                deduped = re.sub(r'(.)\1', r'\1', line)
                m = re.search(r'([A-Za-z]+ \d+, \d{4} - \d+:\d+)', deduped)
                if m:
                    try:
                        measurement_dt = datetime.strptime(
                            m.group(1), '%b %d, %Y - %H:%M'
                        )
                    except ValueError:
                        pass
                break

        # --- Build entry ---
        entry = INLKLATencorProfiler()

        if measurement_dt:
            entry.datetime = measurement_dt
        if recipe:
            entry.recipe = recipe
        if site_name:
            entry.site_name = site_name
        if length_um:
            entry.scan_length = float(length_um) * self._UM_TO_M
        if speed_um:
            entry.scan_speed = float(speed_um) * self._UM_TO_M
        if rate_hz:
            entry.sample_rate = float(rate_hz)
        if direction:
            entry.scan_direction = direction.strip()
        if repeats_s:
            entry.repeats = int(repeats_s)
        if force_mg:
            entry.stylus_force = float(force_mg) * self._MG_TO_KG
        if noise_um:
            entry.noise_filter = float(noise_um) * self._UM_TO_M
        result = INLKLATencorProfilerResults()
        if st_height_a:
            result.step_height = float(st_height_a) * self._ANGSTROM_TO_M
        if ra_a:
            result.Ra = float(ra_a) * self._ANGSTROM_TO_M
        if max_ra_a:
            result.max_Ra = float(max_ra_a) * self._ANGSTROM_TO_M
        if rq_a:
            result.Rq = float(rq_a) * self._ANGSTROM_TO_M
        if rh_a:
            result.Rh = float(rh_a) * self._ANGSTROM_TO_M
        entry.results.append(result)

        # --- Create archive ---
        prof_filename = f'{data_file}.profiler.archive.{filetype}'
        prof_archive = EntryArchive(
            data=entry,
            metadata=EntryMetadata(upload_id=archive.m_context.upload_id),
        )
        create_archive(
            prof_archive.m_to_dict(),
            archive.m_context,
            prof_filename,
            filetype,
            logger,
        )

        file_reference = get_hash_ref(archive.m_context.upload_id, data_file)
        archive.data = RawFile_(
            name=data_file + '_raw',
            file_=file_reference,
        )
        archive.metadata.entry_name = data_file


class FourPointProbeParser(MatchingParser):
    """
    Parser for 4-point probe sheet resistance Excel files produced by the INL
    4PP measurement system.

    File structure (all in one sheet, no explicit header row until the data table):
      Rows 0–16 : "N. Label :" in col A, value in col C
      Row 17    : "18. Analysis [ ohm/sq ] : 3 Sigma=Max : X  Min : Y"
      Rows 18–20: sub-analysis key-value pairs (European decimal comma)
      Blank row
      Header row: "No  X (mm)  Y (mm)  Sheet R ( ohm/sq )  Resistivity ( ohm.cm )"
      Data rows : one row per measurement point
    """

    # Conversion factors
    _MM_TO_M = 1e-3
    _UM_TO_M = 1e-6
    _OHM_CM_TO_OHM_M = 1e-2
    _KELVIN_OFFSET = 273.15

    @staticmethod
    def _fval(raw) -> float:
        """Convert a raw cell value to float, handling European decimal commas."""
        return float(str(raw).replace(',', '.').strip())

    def parse(self, mainfile: str, archive: EntryArchive, logger) -> None:
        import re

        filetype = 'yaml'
        data_file = (
            mainfile.rsplit('/', maxsplit=1)[-1]
            .rsplit('.', maxsplit=1)[0]
            .replace(' ', '_')
        )

        # --- Read entire sheet as raw cells ---
        raw = pd.read_excel(mainfile, header=None, dtype=str)

        def cell(row: int, col: int):
            """Return stripped cell string or empty string if missing/NaN."""
            try:
                v = raw.iat[row, col]
                return '' if pd.isna(v) else str(v).strip()
            except (IndexError, TypeError):
                return ''

        # --- Rows 0–16: numbered key-value metadata ---
        # Col A: "N. Label :", Col C (index 2): value
        # Indices: 0=Lot ID, 1=Data File, 2=X size, 3=Y size, 4=Exclusion,
        #          5=Thickness, 6=Sample Material, 7=Mat.Resistivity,
        #          8=Correction F, 9=Probe Space, 10=TCoefficient,
        #          11=TMeasure, 12=TReference, 13=MMode, 14=Date, 15=Time, 16=Op ID
        def _meta(row: int) -> str:
            return cell(row, 2)

        lot_id = _meta(0)
        data_file_name = _meta(1)
        x_size_mm = _meta(2)
        y_size_mm = _meta(3)
        exclusion_mm = _meta(4)
        thickness_um = _meta(5)
        sample_material = _meta(6)
        mat_resistivity_raw = _meta(7)
        correction_f = _meta(8)
        probe_space_mm = _meta(9)
        t_coeff = _meta(10)
        t_measure = _meta(11)
        t_reference = _meta(12)
        m_mode = _meta(13)
        date_str = _meta(14)
        time_str = _meta(15)
        op_id = _meta(16)

        # --- Row 17: Analysis line ---
        # "18. Analysis [ ohm/sq ] : 3 Sigma=Max : 0,39489  Min : 0,36679"
        analysis_line = ''
        for ci in range(raw.shape[1]):
            v = cell(17, ci)
            if v:
                analysis_line += ' ' + v
        analysis_line = analysis_line.strip()

        sigma_3_max = sigma_3_min = None
        m = re.search(r'Max\s*:\s*([\d,\.]+)', analysis_line)
        if m:
            sigma_3_max = self._fval(m.group(1))
        m = re.search(r'Min\s*:\s*([\d,\.]+)', analysis_line)
        if m:
            sigma_3_min = self._fval(m.group(1))

        # --- Rows 18–20: sub-analysis pairs ---
        # Row 18: "1) Max : X  2) Min : Y  3) Ave : Z"
        # Row 19: "4) StDev : X  5) Uni(%) : Y  6) Max-Min(Range) : Z"
        # Row 20: "StDev/Ave(%) : X"
        def _row_text(row: int) -> str:
            parts = [cell(row, c) for c in range(raw.shape[1])]
            return ' '.join(p for p in parts if p)

        sub_line1 = _row_text(18)
        sub_line2 = _row_text(19)
        sub_line3 = _row_text(20)

        def _extract(pattern: str, text: str):
            m = re.search(pattern, text)
            return self._fval(m.group(1)) if m else None

        rs_max = _extract(r'Max\s*:\s*([\d,\.]+)', sub_line1)
        rs_min = _extract(r'Min\s*:\s*([\d,\.]+)', sub_line1)
        rs_ave = _extract(r'Ave\s*:\s*([\d,\.]+)', sub_line1)
        rs_std = _extract(r'StDev\s*:\s*([\d,\.]+)', sub_line2)
        uni_pct = _extract(r'Uni\(%\)\s*:\s*([\d,\.]+)', sub_line2)
        rs_range = _extract(r'Max-Min\(Range\)\s*:\s*([\d,\.]+)', sub_line2)
        std_ave_pct = _extract(r'StDev/Ave\(%\)\s*:\s*([\d,\.]+)', sub_line3)

        # --- Find the data table header row ---
        # Look for a row where col A (index 0) contains "No"
        data_header_row = None
        for ri in range(21, min(raw.shape[0], 50)):
            if cell(ri, 0).strip().lower() == 'no':
                data_header_row = ri
                break

        x_pos = y_pos = rs_arr = rho_arr = None
        if data_header_row is not None:
            df_data = pd.read_excel(
                mainfile,
                skiprows=data_header_row,
                dtype=str,
            )
            # Expected columns: No, X (mm), Y (mm), Sheet R ( ohm/sq ), Resistivity ( ohm.cm )
            # Normalise column names for lookup
            col_map = {c.strip(): c for c in df_data.columns}

            def _arr(key_hint: str):
                for k in col_map:
                    if key_hint.lower() in k.lower():
                        raw_col = df_data[col_map[k]]
                        return (
                            raw_col.apply(
                                lambda v: float(str(v).replace(',', '.'))
                                if pd.notna(v)
                                else np.nan
                            )
                            .to_numpy(dtype=np.float64)
                        )
                return None

            x_pos = _arr('x (mm')
            y_pos = _arr('y (mm')
            rs_arr = _arr('sheet r')
            rho_arr = _arr('resistivity')

        # --- Parse datetime ---
        measurement_dt = None
        if date_str and time_str:
            for fmt in ('%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S'):
                try:
                    measurement_dt = datetime.strptime(
                        f'{date_str} {time_str}', fmt
                    )
                    break
                except ValueError:
                    continue

        # --- Build entry ---
        entry = INLFourPointProbe()

        # Hidden metadata
        if lot_id:
            entry.lot_id = lot_id
        if data_file_name:
            entry.data_file_name = data_file_name
        if thickness_um:
            try:
                entry.thickness = self._fval(thickness_um) * self._UM_TO_M
            except ValueError:
                pass
        if sample_material:
            entry.sample_material = sample_material
        if mat_resistivity_raw:
            try:
                entry.material_resistivity = (
                    self._fval(mat_resistivity_raw) * self._OHM_CM_TO_OHM_M
                )
            except ValueError:
                pass

        # Visible metadata
        if op_id:
            entry.operator = op_id
        if measurement_dt:
            entry.datetime = measurement_dt
        if m_mode:
            entry.measurement_mode = m_mode
        for attr, raw_val, factor in [
            ('x_size', x_size_mm, self._MM_TO_M),
            ('y_size', y_size_mm, self._MM_TO_M),
            ('exclusion_size', exclusion_mm, self._MM_TO_M),
            ('probe_spacing', probe_space_mm, self._MM_TO_M),
        ]:
            if raw_val:
                try:
                    setattr(entry, attr, self._fval(raw_val) * factor)
                except ValueError:
                    pass
        for attr, raw_val in [
            ('correction_factor', correction_f),
            ('temperature_coefficient', t_coeff),
        ]:
            if raw_val:
                try:
                    setattr(entry, attr, self._fval(raw_val))
                except ValueError:
                    pass
        for attr, raw_val in [
            ('measurement_temperature', t_measure),
            ('reference_temperature', t_reference),
        ]:
            if raw_val:
                try:
                    setattr(entry, attr, self._fval(raw_val) + self._KELVIN_OFFSET)
                except ValueError:
                    pass

        # Analysis summary + per-point data stored in a results sub-section
        result = INLFourPointProbeResults()
        for attr, val in [
            ('sigma_3_max', sigma_3_max),
            ('sigma_3_min', sigma_3_min),
            ('sheet_resistance_max', rs_max),
            ('sheet_resistance_min', rs_min),
            ('sheet_resistance_ave', rs_ave),
            ('sheet_resistance_std_dev', rs_std),
            ('uniformity_pct', uni_pct),
            ('sheet_resistance_range', rs_range),
            ('std_dev_over_ave_pct', std_ave_pct),
        ]:
            if val is not None:
                setattr(result, attr, val)

        # Per-point arrays (positions: mm → m; resistivity: ohm·cm → ohm·m)
        if x_pos is not None:
            result.x_position = x_pos * self._MM_TO_M
        if y_pos is not None:
            result.y_position = y_pos * self._MM_TO_M
        if rs_arr is not None:
            result.sheet_resistance = rs_arr
        if rho_arr is not None:
            result.resistivity = rho_arr * self._OHM_CM_TO_OHM_M
        entry.results.append(result)

        # --- Create archive ---
        fpp_filename = f'{data_file}.four_point_probe.archive.{filetype}'
        fpp_archive = EntryArchive(
            data=entry,
            metadata=EntryMetadata(upload_id=archive.m_context.upload_id),
        )
        create_archive(
            fpp_archive.m_to_dict(),
            archive.m_context,
            fpp_filename,
            filetype,
            logger,
        )

        file_reference = get_hash_ref(archive.m_context.upload_id, data_file)
        archive.data = RawFile_(
            name=data_file + '_raw',
            file_=file_reference,
        )
        archive.metadata.entry_name = data_file


class _BaseSputteringChamberParser(MatchingParser):
    """
    Shared parser for INL Battery Chamber sputtering system CSV log files (PC03, PC04, …).

    Subclasses set ``_ENTRY_CLASS`` to the concrete ``BatteryChamberSputteringDeposition``
    subclass that should be created for their instrument.

    CSV format (identical across chambers):
      Line 1: meta-column names  (Recording Name, Date Started, User)
      Line 2: meta-values        (All Signals, YYYY-M-D HH-MM-SS, OperatorName)
      Line 3: empty
      Line 4: data column headers (~460 columns)
      Lines 5+: data rows at ~1 Hz
    """

    # Subclasses override this with their specific entry class.
    _ENTRY_CLASS = None

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
            arr = df[name].fillna('').astype(str).to_numpy(dtype=str)
            return arr if not np.all(arr == '') else None

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
        entry = self._ENTRY_CLASS()
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
        env = SputteringChamberEnvironment()

        # Main process pressure: Capman value [Pa] + setpoint [Pa]
        capman_arr = col('PC Capman Pressure')
        capman_sp_arr = col('PC Capman Pressure Setpoint')
        if capman_arr is not None or capman_sp_arr is not None:
            p = SputteringPressure()
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
                p = SputteringPressure()
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
            gf = SputteringGasFlow()
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
                gf.flow_rate = SputteringVolumetricFlowRate()
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
            src = SputteringSource()
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
            ps = SputteringRFPowerSupply()
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
        ps4 = SputteringDCPowerSupply()
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


class PC03CathodeChamberParser(_BaseSputteringChamberParser):
    """Parser for PC03 CathodeChamber CSV log files."""

    _ENTRY_CLASS = PC03CathodeChamberDeposition


class PC04ElectrolyteChamberParser(_BaseSputteringChamberParser):
    """Parser for PC04 ElectrolyteChamber CSV log files (sputtering path only)."""

    _ENTRY_CLASS = PC04ElectrolyteChamberDeposition


class PC04ChamberParser(_BaseSputteringChamberParser):
    """
    Smart dispatcher for PC04 ElectrolyteChamber CSV log files.

    Detects the recording type from the column headers at parse time:
    - If sputtering source columns are present → :class:`PC04ElectrolyteChamberDeposition`
    - Otherwise (heater-only log) → :class:`PC04SubstrateAnnealing`
    """

    _ENTRY_CLASS = PC04ElectrolyteChamberDeposition  # fallback for base class super() call
    _KELVIN_OFFSET = 273.15

    # Column that unambiguously identifies a sputtering log
    _SPUTTERING_MARKER = 'PC Source 1 Active'

    def parse(self, mainfile: str, archive: EntryArchive, logger) -> None:
        # Peek at column headers only (nrows=0 is fast)
        df_head = pd.read_csv(mainfile, skiprows=3, nrows=0, low_memory=False)
        if self._SPUTTERING_MARKER in df_head.columns:
            self._ENTRY_CLASS = PC04ElectrolyteChamberDeposition
            super().parse(mainfile, archive, logger)
        else:
            self._parse_annealing(mainfile, archive, logger)

    def _parse_annealing(
        self, mainfile: str, archive: EntryArchive, logger
    ) -> None:
        """Parse a heater-only PC04 CSV into a :class:`PC04SubstrateAnnealing` entry."""
        from datetime import datetime

        # --- Read preamble (recording metadata) ---
        with open(mainfile, encoding='utf-8', errors='replace') as fh:
            meta_keys = [k.strip() for k in fh.readline().rstrip('\n').split(',')]
            meta_values = [v.strip() for v in fh.readline().rstrip('\n').split(',')]
        meta = dict(zip(meta_keys, meta_values))

        start_datetime = None
        date_str = meta.get('Date Started', '')
        for fmt in ('%Y-%m-%d %H-%M-%S', '%Y-%m-%d %H:%M:%S'):
            try:
                start_datetime = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

        # --- Read time-series data ---
        df = pd.read_csv(mainfile, skiprows=3, low_memory=False)

        def col(name):
            if name not in df.columns:
                return None
            arr = pd.to_numeric(df[name], errors='coerce').to_numpy(dtype=np.float64)
            return arr if not np.all(np.isnan(arr)) else None

        def col_temp(name):
            arr = col(name)
            return arr + self._KELVIN_OFFSET if arr is not None else None

        def col_str(name):
            if name not in df.columns:
                return None
            arr = df[name].fillna('').astype(str).to_numpy(dtype=str)
            return arr if not np.all(arr == '') else None

        # --- Timestamps ---
        ts_fmt = '%b-%d-%Y %I:%M:%S.%f %p'
        try:
            ts = pd.to_datetime(df['Time Stamp'], format=ts_fmt)
            t0 = ts.iloc[0]
            timestamps = (ts - t0).dt.total_seconds().to_numpy(dtype=np.float64)
        except Exception:
            timestamps = np.arange(len(df), dtype=np.float64)

        # --- Build entry ---
        entry = PC04SubstrateAnnealing()
        entry.recording_name = meta.get('Recording Name', '')
        entry.operator = meta.get('User', '')
        if start_datetime:
            entry.start_datetime = start_datetime
        entry.timestamps = timestamps

        ph = col_str('Process Phase')
        if ph is not None:
            entry.process_phase = ph

        # Substrate type (last non-empty value)
        if 'Substrate Type' in df.columns:
            vals = df['Substrate Type'].dropna()
            if len(vals) > 0:
                entry.substrate_type = str(vals.iloc[-1])

        # Pressure
        arr = col('PC Wide Range Gauge')
        if arr is not None:
            entry.wide_range_pressure = arr * _TORR_TO_PA

        # Heater temperatures
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

        # Thermocouples TC1–6
        for i in range(1, 7):
            arr = col_temp(f'TC{i} Temperature')
            if arr is not None:
                setattr(entry, f'tc{i}_temperature', arr)

        archive.data = entry
        data_file = mainfile.rsplit('/', maxsplit=1)[-1].rsplit('.', maxsplit=1)[0]
        archive.metadata.entry_name = data_file


# ---------------------------------------------------------------------------
# EQE Parser
# ---------------------------------------------------------------------------


class EQEParser(MatchingParser):
    def parse(self, mainfile: str, archive: EntryArchive, logger) -> None:
        import re

        filetype = 'yaml'
        data_file = (
            mainfile.rsplit('/', maxsplit=1)[-1]
            .rsplit('.', maxsplit=1)[0]
            .replace(' ', '_')
        )

        # Read the file: data lines are tab-separated, footer starts after a
        # line that doesn't have numeric first column or is blank after data.
        data_lines = []
        footer_lines = []
        in_footer = False
        with open(mainfile, encoding='utf-8', errors='replace') as fh:
            header = fh.readline()  # noqa: F841 — column header line
            for line in fh:
                stripped = line.strip()
                if not stripped:
                    in_footer = True
                    continue
                if not in_footer:
                    parts = stripped.split('\t')
                    try:
                        float(parts[0])
                        data_lines.append(parts)
                    except (ValueError, IndexError):
                        in_footer = True
                        footer_lines.append(stripped)
                else:
                    footer_lines.append(stripped)

        # Parse data columns
        wavelength = np.array([float(row[0]) for row in data_lines], dtype=np.float64)
        qe = np.array([float(row[1]) for row in data_lines], dtype=np.float64)
        # Normalise: if values look like percentages (>1), convert to fraction
        if np.nanmax(qe) > 1.0:
            qe = qe / 100.0

        # Parse footer metadata
        footer_dict = {}
        for fl in footer_lines:
            if '\t' in fl:
                parts = fl.split('\t', maxsplit=1)
                if len(parts) == 2:
                    footer_dict[parts[0].strip()] = parts[1].strip()

        def footer_float(key_pattern):
            for k, v in footer_dict.items():
                if re.search(key_pattern, k, re.IGNORECASE):
                    try:
                        return float(v)
                    except ValueError:
                        return None
            return None

        def footer_str(key_pattern):
            for k, v in footer_dict.items():
                if re.search(key_pattern, k, re.IGNORECASE):
                    return v
            return None

        from nomad_inl_base.schema_packages.characterization import INLEQE

        eqe_entry = INLEQE()
        eqe_entry.wavelength = ureg.Quantity(wavelength, ureg.nanometer)
        eqe_entry.quantum_efficiency = qe

        jsc_val = footer_float(r'Jsc')
        if jsc_val is not None:
            eqe_entry.jsc = ureg.Quantity(jsc_val, ureg('milliampere/centimeter**2'))

        bg_val = footer_float(r'[Bb]andgap')
        if bg_val is not None:
            eqe_entry.bandgap = ureg.Quantity(bg_val, ureg.eV)

        dev_id = footer_str(r'[Dd]evice\s*ID')
        if dev_id is not None:
            eqe_entry.device_id = dev_id

        chop_val = footer_float(r'[Cc]hopping\s*[Ff]requency')
        if chop_val is not None:
            eqe_entry.chopping_frequency = ureg.Quantity(chop_val, ureg.hertz)

        lb_val = footer_float(r'[Ll]ight\s*[Bb]ias\s*[Cc]urrent')
        if lb_val is not None:
            eqe_entry.light_bias_current = ureg.Quantity(lb_val, ureg.milliampere)

        vb_val = footer_float(r'[Vv]oltage\s*[Bb]ias')
        if vb_val is not None:
            eqe_entry.voltage_bias = ureg.Quantity(vb_val, ureg.volt)

        eqe_filename = f'{data_file}.EQE.archive.{filetype}'
        eqe_archive = EntryArchive(
            data=eqe_entry,
            metadata=EntryMetadata(upload_id=archive.m_context.upload_id),
        )
        create_archive(
            eqe_archive.m_to_dict(),
            archive.m_context,
            eqe_filename,
            filetype,
            logger,
        )

        archive.data = RawFile_(
            name=data_file + '_raw',
            file_=get_hash_ref(archive.m_context.upload_id, data_file),
        )
        archive.metadata.entry_name = data_file


# ---------------------------------------------------------------------------
# Solar Cell IV Parser
# ---------------------------------------------------------------------------


class SolarCellIVParser(MatchingParser):
    """
    Matches on 'Results Table' .txt files.  For each matched file, looks up
    all sibling Results Table and IV Graph files sharing the same sample
    prefix and combines them into a single INLSolarCellIV archive entry.
    """

    def parse(self, mainfile: str, archive: EntryArchive, logger) -> None:
        import os
        import re

        filetype = 'yaml'
        basename = mainfile.rsplit('/', maxsplit=1)[-1]
        directory = mainfile.rsplit('/', maxsplit=1)[0] if '/' in mainfile else '.'

        # Extract sample prefix: everything before "Results Table"
        match = re.match(r'^(.+?)\s*Results\s*Table', basename, re.IGNORECASE)
        if not match:
            logger.error(f'Could not extract sample prefix from {basename}')
            return
        sample_prefix = match.group(1).strip()

        # Find all sibling Results Table and IV Graph files for this sample
        results_files = []
        iv_files = []
        for fname in sorted(os.listdir(directory)):
            if not fname.lower().endswith('.txt'):
                continue
            if fname.startswith(sample_prefix):
                if re.search(r'Results\s*Table', fname, re.IGNORECASE):
                    results_files.append(os.path.join(directory, fname))
                elif re.search(r'IV\s*Graph', fname, re.IGNORECASE):
                    iv_files.append(os.path.join(directory, fname))

        from nomad_inl_base.schema_packages.characterization import (
            INLSolarCellIV,
            SolarCellIVCurve,
            SolarCellIVResult,
        )

        entry = INLSolarCellIV()
        all_results = []
        all_curves = []

        # Parse Results Table files
        for rf in results_files:
            try:
                df = pd.read_csv(rf, sep='\t', encoding='utf-8', engine='python')
            except Exception:
                logger.warn(f'Could not read results table: {rf}')
                continue

            for _, row in df.iterrows():
                result = SolarCellIVResult()
                result.measurement_name = str(row.get('Measurement', ''))
                if 'Voc V' in df.columns:
                    result.voc = ureg.Quantity(float(row['Voc V']), ureg.volt)
                if 'Isc A' in df.columns:
                    result.isc = ureg.Quantity(float(row['Isc A']), ureg.ampere)
                if 'Jsc mA/cm2' in df.columns:
                    result.jsc = ureg.Quantity(
                        float(row['Jsc mA/cm2']),
                        ureg('milliampere/centimeter**2'),
                    )
                if 'Vmax V' in df.columns:
                    result.vmax = ureg.Quantity(float(row['Vmax V']), ureg.volt)
                if 'Imax A' in df.columns:
                    result.imax = ureg.Quantity(float(row['Imax A']), ureg.ampere)
                if 'Pmax mW' in df.columns:
                    result.pmax = ureg.Quantity(
                        float(row['Pmax mW']), ureg.milliwatt
                    )
                if 'Fill Factor' in df.columns:
                    result.fill_factor = float(row['Fill Factor'])
                if 'Efficiency' in df.columns:
                    result.efficiency = float(row['Efficiency'])
                if 'RShunt ohms' in df.columns:
                    result.r_shunt = ureg.Quantity(
                        float(row['RShunt ohms']), ureg.ohm
                    )
                if 'R at Voc' in df.columns:
                    result.r_at_voc = float(row['R at Voc'])
                if 'R at Isc' in df.columns:
                    result.r_at_isc = float(row['R at Isc'])
                if 'Exposure' in df.columns:
                    result.exposure = ureg.Quantity(
                        float(row['Exposure']), ureg.second
                    )
                if 'Time' in df.columns and 'Date' in df.columns:
                    result.datetime = f"{row.get('Date', '')} {row.get('Time', '')}"
                all_results.append(result)

        # Parse IV Graph files
        for ivf in iv_files:
            try:
                df = pd.read_csv(ivf, sep='\t', encoding='utf-8', engine='python')
            except Exception:
                logger.warn(f'Could not read IV graph: {ivf}')
                continue

            # File has two header rows: row 0 = measurement names, row 1 = Vmeas/Imeas
            # Re-read with header=[0,1] for multi-level columns
            try:
                df = pd.read_csv(
                    ivf, sep='\t', header=[0, 1], encoding='utf-8', engine='python'
                )
            except Exception:
                logger.warn(f'Could not parse IV graph multi-header: {ivf}')
                continue

            # Iterate over measurement columns in pairs
            cols = list(df.columns)
            i = 0
            while i < len(cols) - 1:
                meas_name = cols[i][0] if isinstance(cols[i], tuple) else str(cols[i])
                col_type = cols[i][1] if isinstance(cols[i], tuple) else ''
                if 'Vmeas' in str(col_type) or 'Vmeas' in str(cols[i]):
                    v_data = pd.to_numeric(df.iloc[:, i], errors='coerce').dropna()
                    i_data = pd.to_numeric(df.iloc[:, i + 1], errors='coerce').dropna()
                    if len(v_data) > 0 and len(i_data) > 0:
                        min_len = min(len(v_data), len(i_data))
                        curve = SolarCellIVCurve()
                        curve.measurement_name = str(meas_name).strip()
                        curve.voltage = ureg.Quantity(
                            v_data.values[:min_len].astype(np.float64), ureg.volt
                        )
                        curve.current = ureg.Quantity(
                            i_data.values[:min_len].astype(np.float64), ureg.ampere
                        )
                        all_curves.append(curve)
                    i += 2
                else:
                    i += 1

        entry.results = all_results
        entry.iv_curves = all_curves

        safe_prefix = sample_prefix.replace(' ', '_')
        sc_filename = f'{safe_prefix}.SolarCellIV.archive.{filetype}'
        sc_archive = EntryArchive(
            data=entry,
            metadata=EntryMetadata(upload_id=archive.m_context.upload_id),
        )
        create_archive(
            sc_archive.m_to_dict(),
            archive.m_context,
            sc_filename,
            filetype,
            logger,
        )

        data_file = basename.rsplit('.', maxsplit=1)[0].replace(' ', '_')
        archive.data = RawFile_(
            name=data_file + '_raw',
            file_=get_hash_ref(archive.m_context.upload_id, data_file),
        )
        archive.metadata.entry_name = data_file


# ---------------------------------------------------------------------------
# GDOES Parser
# ---------------------------------------------------------------------------


class GDOESParser(MatchingParser):
    def parse(self, mainfile: str, archive: EntryArchive, logger) -> None:
        filetype = 'yaml'
        data_file = (
            mainfile.rsplit('/', maxsplit=1)[-1]
            .rsplit('.', maxsplit=1)[0]
            .replace(' ', '_')
        )

        # GDOES files: 2 header lines then tab-separated data
        # First column is depth, remaining columns are element concentrations
        df = pd.read_csv(mainfile, sep='\t', encoding='utf-8', engine='python')

        # Detect depth column (first column, may contain unit info like "µm")
        depth_col = df.columns[0]
        depth_values = pd.to_numeric(df[depth_col], errors='coerce').dropna().values

        from nomad_inl_base.schema_packages.characterization import (
            INLGDOES,
            GDOESElementProfile,
        )

        gdoes_entry = INLGDOES()
        gdoes_entry.depth = ureg.Quantity(
            depth_values.astype(np.float64), ureg.micrometer
        )

        profiles = []
        for col_name in df.columns[1:]:
            values = pd.to_numeric(df[col_name], errors='coerce').dropna().values
            if len(values) == 0:
                continue
            # Align to depth length
            min_len = min(len(depth_values), len(values))
            profile = GDOESElementProfile()
            profile.element_name = str(col_name).strip()
            profile.concentration = values[:min_len].astype(np.float64)
            profiles.append(profile)

        gdoes_entry.element_profiles = profiles

        gdoes_filename = f'{data_file}.GDOES.archive.{filetype}'
        gdoes_archive = EntryArchive(
            data=gdoes_entry,
            metadata=EntryMetadata(upload_id=archive.m_context.upload_id),
        )
        create_archive(
            gdoes_archive.m_to_dict(),
            archive.m_context,
            gdoes_filename,
            filetype,
            logger,
        )

        archive.data = RawFile_(
            name=data_file + '_raw',
            file_=get_hash_ref(archive.m_context.upload_id, data_file),
        )
        archive.metadata.entry_name = data_file
