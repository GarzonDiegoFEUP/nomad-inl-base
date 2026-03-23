from datetime import date as _date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

import numpy as np
import plotly.graph_objects as go
from nomad.datamodel.data import ArchiveSection, EntryData
from nomad.datamodel.metainfo.annotations import ELNAnnotation
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.metainfo import Datetime, MEnum, Quantity, SchemaPackage, Section, SubSection
from nomad_material_processing.vapor_deposition.general import (
    ChamberEnvironment,
    GasFlow,
    Pressure,
    VolumetricFlowRate,
)
from plotly.subplots import make_subplots

from nomad_inl_base.schema_packages.entities import (
    INLSubstrateReference,
    INLThinFilm,
    INLThinFilmReference,
    INLThinFilmStack,
)
from nomad_inl_base.utils import create_archive, create_filename, get_hash_ref

m_package = SchemaPackage()

# Unit conversion constants
_TORR_TO_PA = 133.322368  # 1 torr = 133.322368 Pa
_SCCM_TO_M3S = 1.66667e-8  # 1 sccm = 1 cm³(STP)/min = 1e-6 m³ / 60 s


class PC03VolumetricFlowRate(VolumetricFlowRate):
    """
    MFC flow rate inheriting VolumetricFlowRate.
    value [m³/s array] → measured flow; set_value [m³/s array] → setpoint.
    """

    m_def = Section(a_eln={'hide': ['measurement_type']})

    measurement_type = Quantity(
        type=MEnum('Mass Flow Controller', 'Flow Meter', 'Other'),
        default='Mass Flow Controller',
    )


class PC03GasFlow(GasFlow):
    """
    Gas flow channel inheriting from GasFlow.
    gas.name holds the species string; flow_rate stores the time-series arrays.
    """

    m_def = Section(label='Gas Flow')

    name = Quantity(
        type=str,
        description='Human-readable gas channel label (e.g. Ar, O2, N2).',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )
    mfc_index = Quantity(
        type=int,
        description='MFC channel index (1, 2, or 3).',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    flow_rate = SubSection(section_def=PC03VolumetricFlowRate)


class PC03Pressure(Pressure):
    """
    Pressure sensor time series inheriting Pressure.
    value [Pa array] → measured; set_value [Pa array] → setpoint (where applicable).
    """

    m_def = Section(a_eln={'hide': ['time', 'set_time']})


class PC03ChamberEnvironment(ChamberEnvironment):
    """
    Chamber environment for a continuous PC03 deposition log.
    Holds the main process pressure (Capman), additional gauges, and MFC gas flows.
    """

    m_def = Section(label='Chamber Environment')

    # Override base gas_flow to use PC03GasFlow
    gas_flow = SubSection(section_def=PC03GasFlow, repeats=True)

    # Override base pressure to use PC03Pressure (Capman = main process pressure).
    # pressure.value = measured [Pa]; pressure.set_value = setpoint [Pa].
    pressure = SubSection(section_def=PC03Pressure)

    # Additional pressure sensors
    ion_gauge_pressure = SubSection(
        section_def=PC03Pressure,
        description='Ion gauge (high vacuum) pressure time series.',
    )
    wide_range_gauge_pressure = SubSection(
        section_def=PC03Pressure,
        description='Wide-range gauge pressure time series.',
    )
    roughing_pressure = SubSection(
        section_def=PC03Pressure,
        description='Roughing pump backing pressure time series.',
    )


class PC03Source(ArchiveSection):
    """Sputtering source (target + magnetron) data from the PC03 CathodeChamber."""

    m_def = Section(label='Sputtering Source')

    source_index = Quantity(
        type=int,
        description='Source position index (1–4).',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )
    material = Quantity(
        type=str,
        description='Target material name as reported by the instrument.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )
    loaded_target = Quantity(
        type=str,
        description='Target identifier loaded on this source (e.g. "LFP#001").',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )
    final_thickness_setpoint = Quantity(
        type=np.float64,
        unit='nm',
        description='QCM thickness setpoint for this source (run target).',
        a_eln=ELNAnnotation(component='NumberEditQuantity', defaultDisplayUnit='nm'),
    )
    power_supply_type = Quantity(
        type=str,
        description='Power supply type connected to this source (RF or DC-pulsed), '
        'determined from the Switch columns in the CSV log.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )
    active = Quantity(
        type=np.dtype(np.bool_),
        shape=['*'],
        description='Whether this source is active (energised) at each time step.',
    )
    shutter_open = Quantity(
        type=np.dtype(np.bool_),
        shape=['*'],
        description='Whether the source shutter is open at each time step.',
    )
    deposition_rate = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='nm/s',
        description='Instantaneous QCM deposition rate as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='nm/s'),
    )
    thickness = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='nm',
        description='QCM-measured film thickness deposited in this run as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='nm'),
    )
    accumulated_thickness = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='nm',
        description='Total accumulated thickness deposited by this source over its lifetime.',
        a_eln=ELNAnnotation(defaultDisplayUnit='nm'),
    )


class PC03RFPowerSupply(ArchiveSection):
    """RF power supply (PS1, PS3, or PS5) time-series data."""

    m_def = Section(label='RF Power Supply')

    supply_index = Quantity(
        type=int,
        description='Power supply index (1, 3, or 5).',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )
    forward_power = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='W',
        description='Forward (incident) RF power as a time series.',
    )
    reflected_power = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='W',
        description='Reflected RF power as a time series.',
    )
    dc_bias = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='V',
        description='DC self-bias voltage on the target as a time series.',
    )
    output_setpoint = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='W',
        description='Requested RF power output setpoint as a time series.',
    )
    load_cap_position = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        description='Load capacitor position (matching network) as a time series.',
    )
    tune_cap_position = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        description='Tune capacitor position (matching network) as a time series.',
    )


class PC03DCPowerSupply(ArchiveSection):
    """DC pulsed power supply (PS4) time-series data."""

    m_def = Section(label='DC Pulsed Power Supply')

    current = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='A',
        description='Output current as a time series.',
    )
    voltage = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='V',
        description='Output voltage as a time series.',
    )
    power = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='W',
        description='Output power as a time series.',
    )
    output_setpoint = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='W',
        description='Requested power output setpoint as a time series.',
    )
    current_setpoint = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='A',
        description='Requested current setpoint as a time series.',
    )
    voltage_setpoint = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='V',
        description='Requested voltage setpoint as a time series.',
    )
    pulse_frequency = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='Hz',
        description='Pulsed DC repetition frequency as a time series.',
    )
    arc_count = Quantity(
        type=np.dtype(np.int64),
        shape=['*'],
        description='Cumulative arc (DC count) events as a time series.',
    )
    spark_count = Quantity(
        type=np.dtype(np.int64),
        shape=['*'],
        description='Cumulative spark events as a time series.',
    )


class PC03CathodeChamberDeposition(PlotSection, EntryData):
    """
    Parsed log entry from the PC03 CathodeChamber sputtering system.

    Populated automatically by uploading a CSV file whose filename starts with 'PC03'.
    All time-series columns are stored as NumPy arrays sampled at ~1 Hz.
    """

    m_def = Section(label='PC03 Cathode Chamber Deposition')

    # --- Metadata (scalar, auto-populated from file header) ---
    recording_name = Quantity(
        type=str,
        description='Recording name as stored in the CSV header.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )
    operator = Quantity(
        type=str,
        description='Operator name as stored in the CSV header.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )
    start_datetime = Quantity(
        type=Datetime,
        description='Date and time when the recording was started.',
        a_eln=ELNAnnotation(component='DateTimeEditQuantity'),
    )
    base_pressure = Quantity(
        type=np.float64,
        unit='pascal',
        description='Minimum ion gauge pressure recorded during this log (used as base pressure estimate).',
        a_eln=ELNAnnotation(component='NumberEditQuantity', defaultDisplayUnit='mbar'),
    )
    deposition_time = Quantity(
        type=np.float64,
        unit='s',
        description='Total elapsed time with substrate shutter open (computed from log data).',
        a_eln=ELNAnnotation(component='NumberEditQuantity', defaultDisplayUnit='s'),
    )
    substrate_type = Quantity(
        type=str,
        description='Substrate type as identified by the system (e.g. "Bare Wafer").',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )

    # --- User-set reference field ---
    substrate = SubSection(
        section_def=INLSubstrateReference,
        description=(
            'Reference to the substrate used in this deposition. '
            'Set this field to auto-create an INLThinFilm (and stack) on re-processing.'
        ),
    )

    # --- Time axis ---
    timestamps = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='s',
        description='Elapsed time from the first recorded row (seconds).',
    )

    # --- Process tracking ---
    process_phase = Quantity(
        type=str,
        shape=['*'],
        description='Process phase name (string label) at each time step.',
    )
    process_time = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='s',
        description='Process phase elapsed time as a time series.',
    )

    # --- Substrate shutter ---
    substrate_shutter_open = Quantity(
        type=np.dtype(np.bool_),
        shape=['*'],
        description='Whether the substrate shutter is open at each time step.',
    )

    # --- Substrate heater ---
    substrate_temperature = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='kelvin',
        description='Primary substrate heater thermocouple temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )
    substrate_temperature_2 = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='kelvin',
        description='Secondary substrate heater thermocouple temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )
    substrate_temperature_setpoint = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='kelvin',
        description='Substrate heater temperature setpoint as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )
    substrate_heater_current = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='A',
        description='Substrate heater current as a time series.',
    )

    # --- Substrate rotation ---
    substrate_rotation_speed = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='1/minute',
        description='Substrate rotation speed (rpm) as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='1/minute'),
    )

    # --- Substrate bias (Rigel) ---
    substrate_bias_active = Quantity(
        type=np.dtype(np.bool_),
        shape=['*'],
        description='Whether substrate bias is active at each time step.',
    )
    substrate_bias_voltage = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='V',
        description='Substrate bias voltage (Rigel DC) as a time series.',
    )
    substrate_bias_current = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='A',
        description='Substrate bias current (Rigel DC) as a time series.',
    )
    substrate_bias_power = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='W',
        description='Substrate bias power (Rigel DC) as a time series.',
    )

    # --- Thermocouples TC1–TC6 ---
    tc1_temperature = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='kelvin',
        description='TC1 temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )
    tc2_temperature = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='kelvin',
        description='TC2 temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )
    tc3_temperature = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='kelvin',
        description='TC3 temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )
    tc4_temperature = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='kelvin',
        description='TC4 temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )
    tc5_temperature = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='kelvin',
        description='TC5 temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )
    tc6_temperature = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='kelvin',
        description='TC6 temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )

    # --- Subsections ---
    chamber_environment = SubSection(
        section_def=PC03ChamberEnvironment,
        description='Chamber gas flows and pressure readings for this deposition.',
    )
    sources = SubSection(
        section_def=PC03Source,
        repeats=True,
        description='Sputtering sources 1–4.',
    )
    rf_power_supplies = SubSection(
        section_def=PC03RFPowerSupply,
        repeats=True,
        description='RF power supplies (PS1, PS3, PS5).',
    )
    dc_power_supply = SubSection(
        section_def=PC03DCPowerSupply,
        description='DC pulsed power supply (PS4).',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        self._trim_inactive()
        self._compute_scalars()
        self._build_figures()
        self._create_thin_film(archive, logger)

    def _trim_inactive(self) -> None:
        """Remove time steps where all sources are inactive (silently, no logging)."""
        if not self.sources:
            return

        # Build mask: True at each timestep where at least one source is active
        n = len(self.timestamps) if self.timestamps is not None else 0
        if n == 0:
            return

        mask = np.zeros(n, dtype=bool)
        for src in self.sources:
            if src.active is not None and len(src.active) == n:
                mask |= src.active.astype(bool)

        # If nothing is active at all, skip trimming
        if not np.any(mask):
            return

        def trim(arr):
            if arr is None:
                return None
            if isinstance(arr, np.ndarray) and len(arr) == n:
                return arr[mask]
            return arr

        # --- Top-level arrays ---
        self.timestamps = trim(self.timestamps)
        self.process_time = trim(self.process_time)
        self.substrate_shutter_open = trim(self.substrate_shutter_open)
        self.substrate_temperature = trim(self.substrate_temperature)
        self.substrate_temperature_2 = trim(self.substrate_temperature_2)
        self.substrate_temperature_setpoint = trim(self.substrate_temperature_setpoint)
        self.substrate_heater_current = trim(self.substrate_heater_current)
        self.substrate_rotation_speed = trim(self.substrate_rotation_speed)
        self.substrate_bias_active = trim(self.substrate_bias_active)
        self.substrate_bias_voltage = trim(self.substrate_bias_voltage)
        self.substrate_bias_current = trim(self.substrate_bias_current)
        self.substrate_bias_power = trim(self.substrate_bias_power)
        for i in range(1, 7):
            attr = f'tc{i}_temperature'
            setattr(self, attr, trim(getattr(self, attr)))
        # process_phase is a string array — trim manually
        if self.process_phase is not None and len(self.process_phase) == n:
            self.process_phase = self.process_phase[mask]

        # --- Chamber environment ---
        env = self.chamber_environment
        if env is not None:
            for p_attr in ('pressure', 'ion_gauge_pressure', 'wide_range_gauge_pressure', 'roughing_pressure'):
                p = getattr(env, p_attr, None)
                if p is not None:
                    p.value = trim(p.value)
                    p.set_value = trim(p.set_value)
            for gf in (env.gas_flow or []):
                if gf.flow_rate is not None:
                    gf.flow_rate.value = trim(gf.flow_rate.value)
                    gf.flow_rate.set_value = trim(gf.flow_rate.set_value)

        # --- Sources ---
        for src in (self.sources or []):
            src.active = trim(src.active)
            src.shutter_open = trim(src.shutter_open)
            src.deposition_rate = trim(src.deposition_rate)
            src.thickness = trim(src.thickness)
            src.accumulated_thickness = trim(src.accumulated_thickness)

        # --- RF power supplies ---
        for ps in (self.rf_power_supplies or []):
            ps.forward_power = trim(ps.forward_power)
            ps.reflected_power = trim(ps.reflected_power)
            ps.dc_bias = trim(ps.dc_bias)
            ps.output_setpoint = trim(ps.output_setpoint)
            ps.load_cap_position = trim(ps.load_cap_position)
            ps.tune_cap_position = trim(ps.tune_cap_position)

        # --- DC power supply ---
        ps4 = self.dc_power_supply
        if ps4 is not None:
            ps4.current = trim(ps4.current)
            ps4.voltage = trim(ps4.voltage)
            ps4.power = trim(ps4.power)
            ps4.output_setpoint = trim(ps4.output_setpoint)
            ps4.current_setpoint = trim(ps4.current_setpoint)
            ps4.voltage_setpoint = trim(ps4.voltage_setpoint)
            ps4.pulse_frequency = trim(ps4.pulse_frequency)
            ps4.arc_count = trim(ps4.arc_count)
            ps4.spark_count = trim(ps4.spark_count)

    def _compute_scalars(self) -> None:
        """Recompute base_pressure from trimmed ion gauge data and compute deposition_time."""
        env = self.chamber_environment
        if env is not None and env.ion_gauge_pressure is not None:
            arr = env.ion_gauge_pressure.value
            if arr is not None and len(arr) > 0:
                raw = arr.magnitude if hasattr(arr, 'magnitude') else np.asarray(arr)
                valid = raw[~np.isnan(raw)]
                if len(valid) > 0:
                    self.base_pressure = float(np.min(valid))

        ts = self.timestamps
        shutter = self.substrate_shutter_open
        if ts is not None and shutter is not None and len(ts) > 1 and len(shutter) == len(ts):
            ts_raw = ts.magnitude if hasattr(ts, 'magnitude') else np.asarray(ts)
            dt = np.diff(ts_raw)
            self.deposition_time = float(np.sum(dt[shutter[:-1].astype(bool)]))

    def _build_figures(self) -> None:
        """Build Plotly figures: Pressure, RF Power, DC Power, Temperatures."""
        self.figures = []
        ts = self.timestamps
        if ts is None or len(ts) == 0:
            return

        _KELVIN_TO_C = 273.15
        _PA_TO_MBAR = 1e-2  # 1 Pa = 0.01 mbar

        def mag(arr):
            """Return plain numpy array, stripping pint units if present."""
            if arr is None:
                return None
            return arr.magnitude if hasattr(arr, 'magnitude') else np.asarray(arr)

        ts_raw = mag(ts)
        env = self.chamber_environment

        # ── Figure 1: Pressure ─────────────────────────────────────────────
        capman = mag(env.pressure.value if (env and env.pressure) else None)
        ion = mag(env.ion_gauge_pressure.value if (env and env.ion_gauge_pressure) else None)
        if capman is not None or ion is not None:
            rows = sum(x is not None for x in [capman, ion])
            fig = make_subplots(
                rows=rows, cols=1, shared_xaxes=True,
                subplot_titles=[t for t, x in [('Capman (mbar)', capman), ('Ion Gauge (mbar)', ion)] if x is not None],
            )
            row = 1
            if capman is not None:
                fig.add_trace(go.Scatter(x=ts_raw, y=capman * _PA_TO_MBAR, name='Capman', line=dict(color='steelblue')), row=row, col=1)
                row += 1
            if ion is not None:
                fig.add_trace(go.Scatter(x=ts_raw, y=ion * _PA_TO_MBAR, name='Ion Gauge', line=dict(color='darkorange')), row=row, col=1)
                fig.update_yaxes(type='log', row=row, col=1)
            fig.update_layout(template='plotly_white', height=400, xaxis_title='Time (s)', showlegend=True)
            self.figures.append(PlotlyFigure(label='Pressure', figure=fig.to_plotly_json()))

        # ── Figure 2: RF Power ─────────────────────────────────────────────
        rf_traces = []
        colours = ['#1f77b4', '#ff7f0e', '#2ca02c']
        for idx, ps in enumerate(self.rf_power_supplies or []):
            c = colours[idx % len(colours)]
            fwd = mag(ps.forward_power)
            rfl = mag(ps.reflected_power)
            if fwd is not None and len(fwd) == len(ts_raw):
                rf_traces.append(go.Scatter(x=ts_raw, y=fwd, name=f'PS{ps.supply_index} Fwd', line=dict(color=c)))
            if rfl is not None and len(rfl) == len(ts_raw):
                rf_traces.append(go.Scatter(x=ts_raw, y=rfl, name=f'PS{ps.supply_index} Rfl', line=dict(color=c, dash='dash')))
        if rf_traces:
            fig = go.Figure(data=rf_traces)
            fig.update_layout(template='plotly_white', height=350, xaxis_title='Time (s)', yaxis_title='Power (W)', showlegend=True)
            self.figures.append(PlotlyFigure(label='RF Power', figure=fig.to_plotly_json()))

        # ── Figure 3: DC Power Supply ──────────────────────────────────────
        ps4 = self.dc_power_supply
        if ps4 is not None:
            dc_rows = [
                (mag(ps4.power), 'Power (W)'),
                (mag(ps4.voltage), 'Voltage (V)'),
                (mag(ps4.current), 'Current (A)'),
            ]
            dc_rows = [(arr, lbl) for arr, lbl in dc_rows if arr is not None and len(arr) == len(ts_raw)]
            if dc_rows:
                fig = make_subplots(rows=len(dc_rows), cols=1, shared_xaxes=True,
                                    subplot_titles=[lbl for _, lbl in dc_rows])
                for row_i, (arr, lbl) in enumerate(dc_rows, start=1):
                    fig.add_trace(go.Scatter(x=ts_raw, y=arr, name=lbl, showlegend=False), row=row_i, col=1)
                fig.update_layout(template='plotly_white', height=500, xaxis_title='Time (s)')
                self.figures.append(PlotlyFigure(label='DC Power Supply', figure=fig.to_plotly_json()))

        # ── Figure 4: Temperatures ─────────────────────────────────────────
        temp_traces = []
        temp_series = [
            (self.substrate_temperature, 'Substrate T', True),
            (self.substrate_temperature_2, 'Substrate T2', 'legendonly'),
            (self.substrate_temperature_setpoint, 'Substrate T setpoint', 'legendonly'),
        ] + [
            (getattr(self, f'tc{i}_temperature'), f'TC{i}', 'legendonly') for i in range(1, 7)
        ]
        for arr, label, visible in temp_series:
            raw = mag(arr)
            if raw is not None and len(raw) == len(ts_raw):
                temp_traces.append(go.Scatter(
                    x=ts_raw, y=raw - _KELVIN_TO_C, name=label, visible=visible,
                ))
        if temp_traces:
            fig = go.Figure(data=temp_traces)
            fig.update_layout(
                template='plotly_white', height=350,
                xaxis_title='Time (s)', yaxis_title='Temperature (°C)',
                showlegend=True,
            )
            self.figures.append(PlotlyFigure(label='Temperatures', figure=fig.to_plotly_json()))

    def _create_thin_film(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        if not self.sources:
            return

        # Collect materials from sources whose shutter was open at any point
        active_materials = []
        for source in self.sources:
            if (
                source.shutter_open is not None
                and len(source.shutter_open) > 0
                and bool(np.any(source.shutter_open))
                and source.material
            ):
                mat = source.material.strip()
                if mat and mat not in active_materials:
                    active_materials.append(mat)

        # Fallback: use all sources that have a material name
        if not active_materials:
            for source in self.sources:
                if source.material and source.material.strip():
                    mat = source.material.strip()
                    if mat not in active_materials:
                        active_materials.append(mat)

        if not active_materials:
            logger.warning(
                'PC03CathodeChamberDeposition: no source materials found, '
                'skipping thin film creation.'
            )
            return

        filetype = 'yaml'
        data_file = (
            archive.metadata.mainfile.rsplit('/', maxsplit=1)[-1]
            .rsplit('.', maxsplit=1)[0]
        )

        if self.start_datetime:
            date_str = self.start_datetime.strftime('%y%m%d')
        else:
            date_str = _date.today().strftime('%y%m%d')

        material_formula = '_'.join(active_materials)
        film_label = f'{date_str}_{material_formula}'

        new_thinFilm = INLThinFilm()
        new_thinFilm.name = film_label
        new_thinFilm.material = active_materials[0]

        thinFilm_filename, thinFilm_archive = create_filename(
            f'{film_label}_{data_file}',
            new_thinFilm,
            'thinFilm',
            archive,
            logger,
        )

        if not archive.m_context.raw_path_exists(thinFilm_filename):
            thinFilmRef = create_archive(
                thinFilm_archive.m_to_dict(),
                archive.m_context,
                thinFilm_filename,
                filetype,
                logger,
            )
        else:
            thinFilmRef = get_hash_ref(archive.m_context.upload_id, thinFilm_filename)

        if self.substrate is None:
            logger.info(
                'PC03CathodeChamberDeposition: thin film created without a stack '
                '(no substrate set). Set the substrate field to auto-create a stack.'
            )
            return

        new_thinFilmReference = INLThinFilmReference(reference=thinFilmRef)

        new_Stack = INLThinFilmStack()
        new_Stack.substrate = self.substrate
        new_Stack.layers.append(new_thinFilmReference)

        stack_filename, stack_archive = create_filename(
            data_file + '_sample',
            new_Stack,
            'ThinFilmStack',
            archive,
            logger,
        )

        if not archive.m_context.raw_path_exists(stack_filename):
            create_archive(
                stack_archive.m_to_dict(),
                archive.m_context,
                stack_filename,
                filetype,
                logger,
            )


m_package.__init_metainfo__()
