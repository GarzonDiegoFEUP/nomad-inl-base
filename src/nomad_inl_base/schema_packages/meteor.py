from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

import numpy as np
from nomad.datamodel.data import ArchiveSection, EntryData, EntryDataCategory
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import Process, PureSubstanceSection
from nomad.metainfo import (
    Category,
    Datetime,
    Quantity,
    SchemaPackage,
    Section,
    SubSection,
)

from nomad_inl_base.schema_packages.entities import (
    INLSampleReference,
    INLSubstrateReference,
    INLThinFilm,
    INLThinFilmReference,
    INLThinFilmStack,
)
from nomad_inl_base.utils import create_archive, create_filename, get_hash_ref

m_package = SchemaPackage()

_ANGSTROM_TO_M = 1e-10


class METEORCategory(EntryDataCategory):
    m_def = Category(label='METEOR', categories=[EntryDataCategory])


class METEORPocket(ArchiveSection):
    """One of the four e-beam evaporation pockets in the METEOR system."""

    m_def = Section(label='E-Beam Pocket')

    name = Quantity(
        type=str,
        description='Pocket label (e.g. "Pocket 1").',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Name',
        ),
    )

    pocket_index = Quantity(
        type=int,
        description='Pocket number (1–4).',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            label='Pocket index',
        ),
    )

    material = SubSection(
        section_def=PureSubstanceSection,
        description='Material loaded in this pocket. Type the element/compound name for PubChem lookup.',
    )

    filament_current = Quantity(
        type=np.float64,
        shape=['*'],
        unit='A',
        description='E-beam filament current time series (Fil N(A) column).',
    )

    set_power = Quantity(
        type=np.float64,
        shape=['*'],
        unit='W',
        description='Set (target) power for this pocket (first Power N(W) column).',
    )

    measured_power = Quantity(
        type=np.float64,
        shape=['*'],
        unit='W',
        description='Measured (actual) power for this pocket (second Power N(W) column).',
    )

    flux = Quantity(
        type=np.float64,
        shape=['*'],
        unit='nA',
        description='Ion flux reading for this pocket.',
    )

    enabled = Quantity(
        type=bool,
        shape=['*'],
        description='Whether this pocket shutter was open at each time point.',
    )


class METEORQCMMonitor(ArchiveSection):
    """Quartz crystal microbalance (QCM) thickness monitor data."""

    m_def = Section(label='QCM Monitor')

    frequency = Quantity(
        type=np.float64,
        shape=['*'],
        unit='Hz',
        description='QCM oscillation frequency time series.',
    )

    deposition_rate = Quantity(
        type=np.float64,
        shape=['*'],
        unit='m/s',
        description='Instantaneous deposition rate time series (Å/s → m/s).',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='angstrom/s',
            label='Deposition rate',
        ),
    )

    thickness = Quantity(
        type=np.float64,
        unit='m',
        description='Final deposited thickness from QCM (auto-filled by parser from last log entry).',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='angstrom',
            label='QCM thickness',
        ),
    )

    thickness_override = Quantity(
        type=np.float64,
        unit='m',
        description=(
            'User-supplied thickness override. '
            'When set, this supersedes the QCM-parsed thickness for thin film creation.'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='angstrom',
            label='Thickness override',
        ),
    )

    density = Quantity(
        type=np.float64,
        unit='kg/m**3',
        description='Material density configured in the QCM controller.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='g/cm**3',
            label='Density',
        ),
    )

    tooling_factor = Quantity(
        type=np.float64,
        description='QCM tooling factor (%).',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            label='Tooling factor (%)',
        ),
    )


class METEORDeposition(Process, EntryData):
    """
    E-beam evaporation in the METEOR (Korvus Technology) system.

    Time-series data is auto-populated by the .nbl log parser. Per-pocket
    materials must be set manually in the ELN. Set creates_new_thin_film=True
    and re-process to auto-create an INLThinFilm entry from the first pocket
    that has a material configured.
    """

    m_def = Section(
        label='METEOR E-Beam Evaporation',
        categories=[METEORCategory],
        a_eln=dict(hide=['instruments', 'lab_id', 'location']),
    )

    log_datetime = Quantity(
        type=Datetime,
        description='Timestamp extracted from the .nbl log file header.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.DateTimeEditQuantity,
            label='Log datetime',
        ),
    )

    mask = Quantity(
        type=str,
        description='Description of the shadow mask used for contact deposition (e.g. "shadow mask A, 2 mm circular contacts").',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity,
            label='Mask',
        ),
    )

    samples = SubSection(
        section_def=INLSampleReference,
        repeats=True,
        description='Sample(s) coated in this deposition run.',
    )

    substrate = SubSection(
        section_def=INLSubstrateReference,
        description=(
            'Substrate to use when no samples are pre-set. '
            'A new thin film stack will be created from it when creates_new_thin_film is enabled.'
        ),
    )

    creates_new_thin_film = Quantity(
        type=bool,
        description=(
            'If True, create an INLThinFilm entry from the first pocket with a material set. '
            'Set this after configuring pocket materials, then re-process.'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.BoolEditQuantity,
            label='Creates new thin film',
        ),
    )

    # ── Time-series quantities (filled by parser) ─────────────────────────────

    elapsed_time = Quantity(
        type=np.float64,
        shape=['*'],
        unit='s',
        description='Elapsed time from the first log entry (Time column minus first value).',
    )

    chamber_pressure = Quantity(
        type=np.float64,
        shape=['*'],
        unit='Pa',
        description='Chamber pressure time series (converted from mbar).',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='mbar',
            label='Chamber pressure',
        ),
    )

    substrate_temperature = Quantity(
        type=np.float64,
        shape=['*'],
        unit='K',
        description='Substrate temperature time series (converted from °C).',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='°C',
            label='Substrate temperature',
        ),
    )

    ebeam_power = Quantity(
        type=np.float64,
        shape=['*'],
        unit='W',
        description='Global e-beam filament power time series.',
    )

    ebeam_current_percentage = Quantity(
        type=np.float64,
        shape=['*'],
        description='E-beam emission current as a percentage of the maximum.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            label='E-beam current (%)',
        ),
    )

    rotation_speed = Quantity(
        type=np.float64,
        shape=['*'],
        unit='rpm',
        description='Substrate holder rotation speed time series.',
    )

    # ── Sub-sections ──────────────────────────────────────────────────────────

    pockets = SubSection(
        section_def=METEORPocket,
        repeats=True,
        description='Four e-beam pockets. Set the material for each pocket in use.',
    )

    qcm = SubSection(
        section_def=METEORQCMMonitor,
        description='QCM thickness monitor data parsed from the log.',
    )

    # ── Normalization ─────────────────────────────────────────────────────────

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        self.method = 'E-Beam Evaporation'
        super().normalize(archive, logger)

        if not self.creates_new_thin_film:
            return

        # Find the first pocket that has a material configured
        active_pocket = None
        for pocket in self.pockets or []:
            if pocket.material is not None and pocket.material.name:
                active_pocket = pocket
                break

        if active_pocket is None:
            logger.warning(
                'METEORDeposition.normalize: creates_new_thin_film=True '
                'but no pocket has a material name set — skipping thin film creation.'
            )
            return

        from nomad.datamodel.context import ClientContext

        if isinstance(archive.m_context, ClientContext):
            return

        from datetime import date as _date

        material_name = active_pocket.material.name
        date_str = (
            self.log_datetime.strftime('%y%m%d')
            if self.log_datetime is not None
            else _date.today().strftime('%y%m%d')
        )
        filetype = 'yaml'
        data_file = (self.name or 'METEOR').replace(' ', '_')

        # Determine thickness: override takes precedence over QCM-parsed value
        film_thickness = None
        if self.qcm is not None:
            if self.qcm.thickness_override is not None:
                film_thickness = self.qcm.thickness_override
            elif self.qcm.thickness is not None:
                film_thickness = self.qcm.thickness

        # ── Create INLThinFilm entry ──────────────────────────────────────────
        new_film = INLThinFilm()
        film_label = f'{date_str}_{material_name}'
        new_film.name = film_label
        new_film.material = material_name
        if film_thickness is not None:
            new_film.thickness = film_thickness

        film_filename, film_archive = create_filename(
            f'{film_label}_{data_file}',
            new_film,
            'thinFilm',
            archive,
            logger,
        )

        if not archive.m_context.raw_path_exists(film_filename):
            film_ref = create_archive(
                film_archive.m_to_dict(),
                archive.m_context,
                film_filename,
                filetype,
                logger,
            )
        else:
            film_ref = get_hash_ref(archive.m_context.upload_id, film_filename)

        new_film_ref = INLThinFilmReference(reference=film_ref)

        # ── Attach film to existing samples, or create a new stack ───────────
        if self.samples:
            for sample in self.samples:
                if sample.reference is not None:
                    sample.reference.layers.append(new_film_ref)
        elif self.substrate is not None:
            new_stack = INLThinFilmStack()
            new_stack.substrate = self.substrate
            new_stack.layers.append(new_film_ref)

            stack_filename, stack_archive = create_filename(
                f'{data_file}_sample',
                new_stack,
                'ThinFilmStack',
                archive,
                logger,
            )
            stack_ref = create_archive(
                stack_archive.m_to_dict(),
                archive.m_context,
                stack_filename,
                filetype,
                logger,
            )
            self.samples.append(INLSampleReference(reference=stack_ref))
        else:
            logger.warning(
                'METEORDeposition.normalize: creates_new_thin_film=True but no '
                'substrate set and no existing samples — skipping stack creation.'
            )


m_package.__init_metainfo__()
