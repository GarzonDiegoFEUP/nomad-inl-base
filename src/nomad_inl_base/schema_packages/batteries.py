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
from nomad_material_processing.general import Annealing
from nomad_material_processing.vapor_deposition.general import (
    ChamberEnvironment,
    GasFlow,
    Pressure,
    VolumetricFlowRate,
)
from plotly.subplots import make_subplots

from nomad_inl_base.schema_packages.entities import (
    INLSampleReference,
    INLSubstrateReference,
    INLThinFilm,
    INLThinFilmReference,
    INLThinFilmStack,
    INLThinFilmStackReference,
)
from nomad_inl_base.utils import create_archive, create_filename, get_hash_ref

m_package = SchemaPackage()

# Unit conversion constants
_TORR_TO_PA = 133.322368  # 1 torr = 133.322368 Pa
_SCCM_TO_M3S = 1.66667e-8  # 1 sccm = 1 cm³(STP)/min = 1e-6 m³ / 60 s


class SputteringVolumetricFlowRate(VolumetricFlowRate):
    """
    MFC flow rate inheriting VolumetricFlowRate.
    value [m³/s array] → measured flow; set_value [m³/s array] → setpoint.
    """

    m_def = Section(a_eln={'hide': ['measurement_type']})

    measurement_type = Quantity(
        type=MEnum('Mass Flow Controller', 'Flow Meter', 'Other'),
        default='Mass Flow Controller',
    )


class SputteringGasFlow(GasFlow):
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

    flow_rate = SubSection(section_def=SputteringVolumetricFlowRate)


class SputteringPressure(Pressure):
    """
    Pressure sensor time series inheriting Pressure.
    value [Pa array] → measured; set_value [Pa array] → setpoint (where applicable).
    """

    m_def = Section(a_eln={'hide': ['time', 'set_time']})


class SputteringChamberEnvironment(ChamberEnvironment):
    """
    Chamber environment for a continuous sputtering deposition log.
    Holds the main process pressure (Capman), additional gauges, and MFC gas flows.
    """

    m_def = Section(label='Chamber Environment')

    gas_flow = SubSection(section_def=SputteringGasFlow, repeats=True)

    # Capman = main process pressure. value [Pa] = measured; set_value [Pa] = setpoint.
    pressure = SubSection(section_def=SputteringPressure)

    # Additional pressure sensors
    ion_gauge_pressure = SubSection(
        section_def=SputteringPressure,
        description='Ion gauge (high vacuum) pressure time series.',
    )
    wide_range_gauge_pressure = SubSection(
        section_def=SputteringPressure,
        description='Wide-range gauge pressure time series.',
    )
    roughing_pressure = SubSection(
        section_def=SputteringPressure,
        description='Roughing pump backing pressure time series.',
    )


class SputteringSource(ArchiveSection):
    """Sputtering source (target + magnetron) time-series data."""

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


class SputteringRFPowerSupply(ArchiveSection):
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


class SputteringDCPowerSupply(ArchiveSection):
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


class PlotConfig(ArchiveSection):
    """User-configurable settings for which figures to generate during normalization.

    Set ``plot_mode`` to ``'Deposition'`` (default) or ``'Thermal Treatment'`` for
    preset figure selections, or ``'Custom'`` to control each toggle individually.
    """

    m_def = Section(label='Plot Configuration')

    plot_mode = Quantity(
        type=MEnum('Deposition', 'Thermal Treatment', 'Custom'),
        default='Deposition',
        description=(
            'Preset plot mode. "Deposition" shows all figures; '
            '"Thermal Treatment" shows only temperatures and pressure; '
            '"Custom" uses the individual show_* toggles.'
        ),
        a_eln=ELNAnnotation(component='EnumEditQuantity'),
    )
    show_pressure = Quantity(
        type=bool,
        default=True,
        description='Include the Pressure (+ MFC flows) figure.',
        a_eln=ELNAnnotation(component='BoolEditQuantity'),
    )
    show_sources = Quantity(
        type=bool,
        default=True,
        description='Include one power-supply figure per active sputtering source.',
        a_eln=ELNAnnotation(component='BoolEditQuantity'),
    )
    show_temperatures = Quantity(
        type=bool,
        default=True,
        description='Include the Temperatures figure.',
        a_eln=ELNAnnotation(component='BoolEditQuantity'),
    )
    show_substrate_bias = Quantity(
        type=bool,
        default=True,
        description='Include the Substrate Bias figure (only rendered if bias was active).',
        a_eln=ELNAnnotation(component='BoolEditQuantity'),
    )
    show_mfc_flows = Quantity(
        type=bool,
        default=True,
        description='Add MFC gas-flow rows to the Pressure figure.',
        a_eln=ELNAnnotation(component='BoolEditQuantity'),
    )


class BatteryChamberSputteringDeposition(PlotSection, EntryData):
    """
    Base class for parsed log entries from INL Battery Chamber sputtering systems
    (PC03 CathodeChamber, PC04 ElectrolyteChamber, …).

    Subclasses override only ``m_def`` to supply the correct label; all quantities,
    subsections, and normalisation logic are inherited from here.
    All time-series columns are stored as NumPy arrays sampled at ~1 Hz.
    """

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
        description='Minimum ion gauge pressure recorded during this log (used as base pressure estimate). Auto-computed during file import.',
        a_eln=ELNAnnotation(component='NumberEditQuantity', defaultDisplayUnit='mbar'),
    )
    deposition_time = Quantity(
        type=np.float64,
        unit='s',
        description='Total elapsed time with substrate shutter open (computed from log data). Auto-computed during file import.',
        a_eln=ELNAnnotation(component='NumberEditQuantity', defaultDisplayUnit='s'),
    )
    substrate_type = Quantity(
        type=str,
        description='Substrate type as identified by the system (e.g. "Bare Wafer").',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )

    # --- User-set reference fields ---
    substrate = SubSection(
        section_def=INLSubstrateReference,
        description=(
            'Single substrate reference (fallback). '
            'Prefer using ``substrates`` to list all individual pieces loaded in the run.'
        ),
    )

    substrates = SubSection(
        section_def=INLSubstrateReference,
        repeats=True,
        description=(
            'Individual substrate entries loaded in this deposition run '
            '(e.g. LCO-17-S01, LCO-17-S02, …). '
            'One INLThinFilmStack is created per entry on normalisation. '
            'Falls back to the single ``substrate`` field if empty.'
        ),
    )

    samples = SubSection(
        section_def=INLSampleReference,
        repeats=True,
        description='References to INL samples (substrate, thin film, or stack) associated with this deposition.',
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
        section_def=SputteringChamberEnvironment,
        description='Chamber gas flows and pressure readings for this deposition.',
    )
    sources = SubSection(
        section_def=SputteringSource,
        repeats=True,
        description='Sputtering sources 1–4.',
    )
    rf_power_supplies = SubSection(
        section_def=SputteringRFPowerSupply,
        repeats=True,
        description='RF power supplies (PS1, PS3, PS5).',
    )
    dc_power_supply = SubSection(
        section_def=SputteringDCPowerSupply,
        description='DC pulsed power supply (PS4).',
    )

    plot_config = SubSection(
        section_def=PlotConfig,
        description='Controls which figures are generated during normalization.',
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

        # Re-zero timestamps so x-axis always starts at 0 after trimming
        if self.timestamps is not None and len(self.timestamps) > 0:
            t0 = self.timestamps[0]
            self.timestamps = self.timestamps - t0

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
        """Build Plotly figures controlled by plot_config settings."""
        self.figures = []
        ts = self.timestamps
        if ts is None or len(ts) == 0:
            return

        # Resolve config - use stored config or create a default one
        cfg = self.plot_config if self.plot_config is not None else PlotConfig()

        # Apply mode presets
        show_pressure = cfg.show_pressure
        show_sources = cfg.show_sources
        show_temperatures = cfg.show_temperatures
        show_substrate_bias = cfg.show_substrate_bias
        show_mfc_flows = cfg.show_mfc_flows
        if cfg.plot_mode == 'Thermal Treatment':
            show_sources = False
            show_substrate_bias = False

        _KELVIN_TO_C = 273.15
        _PA_TO_MBAR = 1e-2
        _M3S_TO_SCCM = 1.0 / _SCCM_TO_M3S

        def mag(arr):
            """Return plain numpy array, stripping pint units if present."""
            if arr is None:
                return None
            return arr.magnitude if hasattr(arr, 'magnitude') else np.asarray(arr)

        ts_raw = mag(ts)
        env = self.chamber_environment

        # ── Figure: Pressure [+ MFC flows] ────────────────────────────────────────────
        if show_pressure:
            capman = mag(env.pressure.value if (env and env.pressure) else None)
            ion = mag(env.ion_gauge_pressure.value if (env and env.ion_gauge_pressure) else None)

            mfc_rows = []
            if show_mfc_flows and env:
                for gf in (env.gas_flow or []):
                    if gf.flow_rate is not None:
                        fv = mag(gf.flow_rate.value)
                        if fv is not None and len(fv) == len(ts_raw):
                            lbl = gf.name or f'MFC {gf.mfc_index}'
                            mfc_rows.append((fv * _M3S_TO_SCCM, lbl))

            pressure_rows = []
            if capman is not None:
                pressure_rows.append((capman * _PA_TO_MBAR, 'Capman (mbar)', False))
            if ion is not None:
                pressure_rows.append((ion * _PA_TO_MBAR, 'Ion Gauge (mbar)', True))
            for fv, lbl in mfc_rows:
                pressure_rows.append((fv, f'{lbl} (sccm)', False))

            if pressure_rows:
                n_rows = len(pressure_rows)
                colours = ['steelblue', 'darkorange', '#2ca02c', '#9467bd', '#8c564b']
                fig = make_subplots(rows=n_rows, cols=1, shared_xaxes=True)
                for r_i, (arr, lbl, log_scale) in enumerate(pressure_rows, start=1):
                    fig.add_trace(
                        go.Scatter(x=ts_raw, y=arr, name=lbl, showlegend=False,
                                   line=dict(color=colours[(r_i - 1) % len(colours)])),
                        row=r_i, col=1,
                    )
                    fig.update_yaxes(title_text=lbl, row=r_i, col=1)
                    if log_scale:
                        fig.update_yaxes(type='log', row=r_i, col=1)
                fig.update_xaxes(title_text='Time (s)', row=n_rows, col=1)
                fig.update_layout(
                    template='plotly_white', height=max(300, 200 * n_rows), showlegend=False,
                )
                self.figures.append(PlotlyFigure(label='Pressure', figure=fig.to_plotly_json()))

        # ── Figures: one per active sputtering source ──────────────────────────────────
        if show_sources:
            rf_by_index = {
                ps.supply_index: ps
                for ps in (self.rf_power_supplies or [])
                if ps.supply_index is not None
            }
            ps4 = self.dc_power_supply

            for src in (self.sources or []):
                if src.active is None or not np.any(src.active.astype(bool)):
                    continue

                src_label = f'Source {src.source_index}'
                if src.material:
                    src_label += f' \u2013 {src.material}'

                supply_rows = []  # (array, y_label, use_log)
                ps_type = (src.power_supply_type or '').upper()

                if 'DC' in ps_type or 'PULSED' in ps_type:
                    if ps4 is not None:
                        for arr, lbl in [
                            (mag(ps4.power), 'Power (W)'),
                            (mag(ps4.voltage), 'Voltage (V)'),
                            (mag(ps4.current), 'Current (A)'),
                            (mag(ps4.pulse_frequency), 'Pulse Freq (Hz)'),
                        ]:
                            if arr is not None and len(arr) == len(ts_raw):
                                supply_rows.append((arr, lbl, False))
                        for arr, lbl in [
                            (mag(ps4.arc_count), 'Arc Count'),
                            (mag(ps4.spark_count), 'Spark Count'),
                        ]:
                            if arr is not None and len(arr) == len(ts_raw):
                                supply_rows.append((arr.astype(float), lbl, False))
                else:
                    # RF supply: sources 1-2 → PS1, sources 3-4 → PS3
                    _SOURCES_ON_PS1 = 2
                    si = src.source_index or 0
                    rf_idx = 1 if si <= _SOURCES_ON_PS1 else 3
                    ps = rf_by_index.get(rf_idx)
                    if ps is not None:
                        for arr, lbl in [
                            (mag(ps.forward_power), 'Fwd Power (W)'),
                            (mag(ps.reflected_power), 'Rfl Power (W)'),
                            (mag(ps.dc_bias), 'RF DC Self-Bias (V)'),
                            (mag(ps.load_cap_position), 'Load Cap Position'),
                            (mag(ps.tune_cap_position), 'Tune Cap Position'),
                        ]:
                            if arr is not None and len(arr) == len(ts_raw):
                                supply_rows.append((arr, lbl, False))

                if not supply_rows:
                    continue

                n_rows = len(supply_rows)
                fig = make_subplots(rows=n_rows, cols=1, shared_xaxes=True)
                for r_i, (arr, lbl, log_scale) in enumerate(supply_rows, start=1):
                    fig.add_trace(
                        go.Scatter(x=ts_raw, y=arr, name=lbl, showlegend=False),
                        row=r_i, col=1,
                    )
                    fig.update_yaxes(title_text=lbl, row=r_i, col=1)
                    if log_scale:
                        fig.update_yaxes(type='log', row=r_i, col=1)
                fig.update_xaxes(title_text='Time (s)', row=n_rows, col=1)
                fig.update_layout(
                    template='plotly_white', height=max(300, 200 * n_rows), showlegend=False,
                )
                self.figures.append(PlotlyFigure(label=src_label, figure=fig.to_plotly_json()))

        # ── Figure: Substrate Bias (only if bias was active) ──────────────────────────
        if show_substrate_bias:
            b_active = mag(self.substrate_bias_active)
            if b_active is not None and np.any(b_active.astype(bool)):
                bias_rows = []
                for arr, lbl in [
                    (mag(self.substrate_bias_voltage), 'Voltage (V)'),
                    (mag(self.substrate_bias_current), 'Current (A)'),
                    (mag(self.substrate_bias_power), 'Power (W)'),
                ]:
                    if arr is not None and len(arr) == len(ts_raw):
                        bias_rows.append((arr, lbl))
                if bias_rows:
                    n_rows = len(bias_rows)
                    fig = make_subplots(rows=n_rows, cols=1, shared_xaxes=True)
                    for r_i, (arr, lbl) in enumerate(bias_rows, start=1):
                        fig.add_trace(
                            go.Scatter(x=ts_raw, y=arr, name=lbl, showlegend=False),
                            row=r_i, col=1,
                        )
                        fig.update_yaxes(title_text=lbl, row=r_i, col=1)
                    fig.update_xaxes(title_text='Time (s)', row=n_rows, col=1)
                    fig.update_layout(
                        template='plotly_white', height=max(300, 200 * n_rows), showlegend=False,
                    )
                    self.figures.append(PlotlyFigure(label='Substrate Bias', figure=fig.to_plotly_json()))

        # ── Figure: Temperatures ──────────────────────────────────────────────────────
        if show_temperatures:
            temp_traces = []
            temp_series = [
                (self.substrate_temperature, 'Substrate T', True),
                (self.substrate_temperature_2, 'Substrate T2', 'legendonly'),
                (self.substrate_temperature_setpoint, 'Substrate T setpoint', 'legendonly'),
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
                'BatteryChamberSputteringDeposition: no source materials found, '
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

        # Determine which substrates to create stacks for.
        # substrates list takes precedence; falls back to single substrate.
        substrates_to_stack = []
        if self.substrates:
            for sub_ref in self.substrates:
                if sub_ref.reference is not None:
                    # Use the substrate's own name as the stack filename suffix
                    sub_name = (
                        getattr(sub_ref.reference, 'name', None)
                        or getattr(sub_ref, 'name', None)
                        or ''
                    )
                    substrates_to_stack.append((sub_name, sub_ref))
        elif self.substrate is not None:
            substrates_to_stack.append(('', self.substrate))

        if not substrates_to_stack:
            logger.info(
                'BatteryChamberSputteringDeposition: thin film created without a stack '
                '(no substrates set). '
                'Add entries to the ``substrates`` field to auto-create stacks.'
            )
            return

        for sub_name, substrate_ref in substrates_to_stack:
            new_thinFilmReference = INLThinFilmReference(reference=thinFilmRef)

            new_Stack = INLThinFilmStack()
            new_Stack.substrate = substrate_ref
            new_Stack.layers.append(new_thinFilmReference)

            suffix = f'_{sub_name}' if sub_name else ''
            stack_filename, stack_archive = create_filename(
                f'{data_file}{suffix}_sample',
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


class PC03CathodeChamberDeposition(BatteryChamberSputteringDeposition):
    """
    Parsed log entry from the PC03 CathodeChamber sputtering system.

    Populated automatically by uploading a CSV file whose filename starts with 'PC03'.
    """

    m_def = Section(label='PC03 Cathode Chamber Deposition')


class PC04ElectrolyteChamberDeposition(BatteryChamberSputteringDeposition):
    """
    Parsed log entry from the PC04 ElectrolyteChamber sputtering system.

    Populated automatically by uploading a CSV file whose filename starts with 'PC04'.
    """

    m_def = Section(label='PC04 Electrolyte Chamber Deposition')


class PC04SubstrateAnnealing(PlotSection, Annealing):
    """
    Parsed log entry for a PC04 ElectrolyteChamber substrate annealing/heating run.

    Populated automatically when a PC04 CSV log contains only heater channels
    and no sputtering source columns.

    Inherits ``duration``, ``steps``, and ``samples`` from
    :class:`nomad_material_processing.general.Annealing`.

    No sample is created automatically. Use ``thin_film`` or ``thin_film_stack``
    to link the run to an existing :class:`~nomad_inl_base.schema_packages.entities.INLThinFilm`
    or :class:`~nomad_inl_base.schema_packages.entities.INLThinFilmStack`.
    """

    m_def = Section(label='PC04 Substrate Annealing')

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
    substrate_type = Quantity(
        type=str,
        description='Substrate type as identified by the system (e.g. "Bare Wafer").',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )
    peak_temperature = Quantity(
        type=np.float64,
        unit='kelvin',
        description='Maximum substrate heater temperature reached during the run. Auto-computed during file import.',
        a_eln=ELNAnnotation(component='NumberEditQuantity', defaultDisplayUnit='celsius'),
    )

    # --- Sample references (user-set) ---
    thin_film = SubSection(
        section_def=INLThinFilmReference,
        description=(
            'Reference to an INLThinFilm sample that was annealed in this run.'
        ),
    )
    thin_film_stack = SubSection(
        section_def=INLThinFilmStackReference,
        description=(
            'Reference to an INLThinFilmStack sample that was annealed in this run.'
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

    # --- Pressure ---
    wide_range_pressure = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='pascal',
        description='Wide-range gauge pressure time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='mbar'),
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

    # --- Thermocouples TC1–6 ---
    tc1_temperature = Quantity(
        type=np.dtype(np.float64), shape=['*'], unit='kelvin',
        description='TC1 temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )
    tc2_temperature = Quantity(
        type=np.dtype(np.float64), shape=['*'], unit='kelvin',
        description='TC2 temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )
    tc3_temperature = Quantity(
        type=np.dtype(np.float64), shape=['*'], unit='kelvin',
        description='TC3 temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )
    tc4_temperature = Quantity(
        type=np.dtype(np.float64), shape=['*'], unit='kelvin',
        description='TC4 temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )
    tc5_temperature = Quantity(
        type=np.dtype(np.float64), shape=['*'], unit='kelvin',
        description='TC5 temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )
    tc6_temperature = Quantity(
        type=np.dtype(np.float64), shape=['*'], unit='kelvin',
        description='TC6 temperature as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='celsius'),
    )

    plot_config = SubSection(
        section_def=PlotConfig,
        description='Controls which figures are generated during normalization.',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        # Default plot_config to Thermal Treatment for annealing runs
        if self.plot_config is None:
            self.plot_config = PlotConfig(plot_mode='Thermal Treatment')
        super().normalize(archive, logger)
        self._compute_scalars()
        self._build_figures()

    def _compute_scalars(self) -> None:
        """Derive peak_temperature and fill the inherited duration quantity."""
        ts = self.timestamps
        if ts is not None and len(ts) > 1:
            ts_raw = ts.magnitude if hasattr(ts, 'magnitude') else np.asarray(ts)
            self.duration = float(ts_raw[-1] - ts_raw[0])

        temp = self.substrate_temperature
        if temp is not None and len(temp) > 0:
            raw = temp.magnitude if hasattr(temp, 'magnitude') else np.asarray(temp)
            valid = raw[~np.isnan(raw)]
            if len(valid) > 0:
                self.peak_temperature = float(np.max(valid))

    def _build_figures(self) -> None:
        """Build Plotly figures: Temperatures, Pressure, Heater Current."""
        self.figures = []
        ts = self.timestamps
        if ts is None or len(ts) == 0:
            return

        cfg = self.plot_config if self.plot_config is not None else PlotConfig(plot_mode='Thermal Treatment')

        _KELVIN_TO_C = 273.15
        _PA_TO_MBAR = 1e-2

        def mag(arr):
            if arr is None:
                return None
            return arr.magnitude if hasattr(arr, 'magnitude') else np.asarray(arr)

        ts_raw = mag(ts)

        # ── Figure: Temperatures ──────────────────────────────────────────────────────
        if cfg.show_temperatures:
            temp_traces = []
            temp_series = [
                (self.substrate_temperature, 'Substrate T', True),
                (self.substrate_temperature_2, 'Substrate T2', 'legendonly'),
                (self.substrate_temperature_setpoint, 'Substrate T setpoint', 'legendonly'),
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
                    template='plotly_white', height=400,
                    xaxis_title='Time (s)', yaxis_title='Temperature (°C)',
                    showlegend=True,
                )
                self.figures.append(PlotlyFigure(label='Temperatures', figure=fig.to_plotly_json()))

        # ── Figure: Pressure ─────────────────────────────────────────────────────────
        if cfg.show_pressure:
            p_raw = mag(self.wide_range_pressure)
            if p_raw is not None and len(p_raw) == len(ts_raw):
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=ts_raw, y=p_raw * _PA_TO_MBAR, name='Wide Range Gauge',
                    line=dict(color='darkorange'),
                ))
                fig.update_yaxes(type='log', title_text='Pressure (mbar)')
                fig.update_layout(
                    template='plotly_white', height=300,
                    xaxis_title='Time (s)',
                    showlegend=False,
                )
                self.figures.append(PlotlyFigure(label='Pressure', figure=fig.to_plotly_json()))

        # ── Figure: Heater Current ────────────────────────────────────────────────────
        i_raw = mag(self.substrate_heater_current)
        if i_raw is not None and len(i_raw) == len(ts_raw):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ts_raw, y=i_raw, name='Heater Current',
                line=dict(color='crimson'),
            ))
            fig.update_yaxes(title_text='Current (A)')
            fig.update_layout(
                template='plotly_white', height=280,
                xaxis_title='Time (s)',
                showlegend=False,
            )
            self.figures.append(PlotlyFigure(label='Heater Current', figure=fig.to_plotly_json()))


m_package.__init_metainfo__()
