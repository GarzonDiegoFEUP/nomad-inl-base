from datetime import date as _date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

import numpy as np
from nomad.datamodel.data import ArchiveSection, EntryData
from nomad.datamodel.metainfo.annotations import ELNAnnotation
from nomad.metainfo import Datetime, Quantity, SchemaPackage, Section, SubSection

from nomad_inl_base.schema_packages.entities import (
    INLSubstrateReference,
    INLThinFilm,
    INLThinFilmReference,
    INLThinFilmStack,
)
from nomad_inl_base.utils import create_archive, create_filename, get_hash_ref

m_package = SchemaPackage()


class PC03GasFlow(ArchiveSection):
    """Gas flow channel (MFC) time-series data from the PC03 CathodeChamber."""

    m_def = Section(label='Gas Flow')

    gas_name = Quantity(
        type=str,
        description='Gas species flowing through this MFC channel.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )
    mfc_index = Quantity(
        type=int,
        description='MFC channel index (1, 2, or 3).',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )
    flow = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='cm**3/minute',
        description='Measured gas flow rate (sccm) as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='cm**3/minute'),
    )
    flow_setpoint = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='cm**3/minute',
        description='Requested gas flow setpoint (sccm) as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='cm**3/minute'),
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


class PC03CathodeChamberDeposition(EntryData):
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
        unit='torr',
        description='Minimum ion gauge pressure recorded during this log (used as base pressure estimate).',
        a_eln=ELNAnnotation(component='NumberEditQuantity', defaultDisplayUnit='torr'),
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

    # --- Pressures ---
    ion_gauge_pressure = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='torr',
        description='Ion gauge pressure (high vacuum) as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='torr'),
    )
    capman_pressure = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='torr',
        description='Capacitance manometer (Capman) pressure as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='torr'),
    )
    capman_pressure_setpoint = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='torr',
        description='Capacitance manometer pressure setpoint as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='torr'),
    )
    wide_range_gauge_pressure = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='torr',
        description='Wide-range gauge pressure as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='torr'),
    )
    roughing_pressure = Quantity(
        type=np.dtype(np.float64),
        shape=['*'],
        unit='torr',
        description='Roughing pump backing pressure as a time series.',
        a_eln=ELNAnnotation(defaultDisplayUnit='torr'),
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
    gas_flows = SubSection(
        section_def=PC03GasFlow,
        repeats=True,
        description='MFC gas flow channels (3 channels: Ar, O2, N2).',
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
        self._create_thin_film(archive, logger)

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
