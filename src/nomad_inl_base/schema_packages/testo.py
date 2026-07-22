from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

import numpy as np
import plotly.graph_objects as go
from nomad.datamodel.context import ClientContext
from nomad.datamodel.data import ArchiveSection
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.metainfo import Datetime, Quantity, SchemaPackage, Section, SubSection

from nomad_inl_base.schema_packages.entities import (
    INLEntityCategory,
    INLInstrument,
    INLInstrumentReference,
)

m_package = SchemaPackage()

_KELVIN_TO_C = 273.15


class INLTestoMeasurementRecord(ArchiveSection):
    """A single temperature/humidity reading from a Testo environmental data logger."""

    m_def = Section(label='Measurement Record')

    timestamp = Quantity(
        type=Datetime,
        description=(
            'Timestamp of this measurement, reconstructed from the logger '
            'ticker. Kept timezone-naive, as recorded by the logger.'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.DateTimeEditQuantity, label='Timestamp'
        ),
    )

    temperature = Quantity(
        type=np.float64,
        unit='kelvin',
        description='Measured air temperature.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            defaultDisplayUnit='celsius',
            label='Temperature',
        ),
    )

    humidity = Quantity(
        type=np.float64,
        description='Measured relative humidity (%RH).',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.NumberEditQuantity,
            label='Relative Humidity (%)',
        ),
    )


class INLTestoLogger(INLInstrument, PlotSection):
    """
    Testo 175H1 (or compatible) environmental data logger deployed at a fixed
    lab location.

    Each uploaded ``.vi2`` file creates one entry of this type, holding the
    records read from that particular file (``measurement_records``). The
    physical device/location is identified via ``lab_id`` (e.g.
    ``B.P0.Lg.06`` or ``C.P0.Tl.01``).

    On processing, this entry also looks up every other ``INLTestoLogger``
    entry that shares the same ``lab_id`` to build a deduplicated,
    chronologically sorted temperature/humidity trend covering the full
    measurement history recorded for that device, and shows it as two plots
    (temperature and humidity vs. time) on this entry.

    Deduplication: records are merged by exact timestamp. When two entries
    report the same timestamp with different values, the record belonging to
    the entry whose upload was created first is kept (earliest upload wins).
    """

    m_def = Section(label='INL Testo Logger', categories=[INLEntityCategory])

    serial_number = Quantity(
        type=str,
        description='Serial number of the Testo logger device.',
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity, label='Serial Number'
        ),
    )

    source_lab_name = Quantity(
        type=str,
        description=(
            'Raw lab-name string extracted from the uploaded .vi2 file, '
            'before mapping to a lab_id/device location.'
        ),
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.StringEditQuantity, label='Source Lab Name'
        ),
    )

    measurement_records = SubSection(
        section_def=INLTestoMeasurementRecord,
        repeats=True,
        description='Temperature/humidity records parsed from this uploaded .vi2 file.',
    )

    def _collect_history(self, archive: 'EntryArchive', logger: 'BoundLogger') -> dict:
        """Merge measurement records from this entry and every other
        ``INLTestoLogger`` entry sharing the same ``lab_id``.

        Returns a dict mapping timestamp -> (temperature, humidity), deduplicated
        with "earliest upload wins" semantics on timestamp collisions.
        """
        own_records = [
            (r.timestamp, r.temperature, r.humidity)
            for r in self.measurement_records or []
            if r.timestamp is not None
        ]

        # (upload_create_time, records) candidates, earliest upload first.
        candidates = [(archive.metadata.upload_create_time, own_records)]

        if self.lab_id and not isinstance(archive.m_context, ClientContext):
            from nomad.search import MetadataPagination, search

            try:
                search_result = search(
                    owner='all',
                    query={
                        'results.eln.lab_ids': self.lab_id,
                        'entry_type': 'INLTestoLogger',
                    },
                    pagination=MetadataPagination(page_size=1000),
                    user_id=archive.metadata.main_author.user_id,
                )
            except Exception as exc:
                logger.warning(
                    'INLTestoLogger: search for related entries failed.',
                    exc_info=exc,
                )
                search_result = None

            if search_result is not None:
                for hit in search_result.data:
                    if hit['entry_id'] == archive.metadata.entry_id:
                        continue
                    try:
                        other_archive = archive.m_context.load_archive(
                            hit['entry_id'], hit['upload_id'], None
                        )
                        other = other_archive.data
                        other_records = [
                            (r.timestamp, r.temperature, r.humidity)
                            for r in getattr(other, 'measurement_records', None) or []
                            if r.timestamp is not None
                        ]
                        candidates.append(
                            (hit.get('upload_create_time'), other_records)
                        )
                    except Exception as exc:
                        logger.warning(
                            'INLTestoLogger: failed to load related entry '
                            f'{hit.get("entry_id")!r} for trend merge.',
                            exc_info=exc,
                        )

        candidates.sort(key=lambda c: (c[0] is None, c[0]))

        merged: dict = {}
        for _, records in candidates:
            for ts, temp, hum in records:
                if ts not in merged:
                    merged[ts] = (temp, hum)
        return merged

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        self.figures = []

        merged = self._collect_history(archive, logger)
        if not merged:
            return

        sorted_ts = sorted(merged.keys())
        temps_c = []
        hums = []
        for ts in sorted_ts:
            temp, hum = merged[ts]
            temp_val = temp.magnitude if hasattr(temp, 'magnitude') else temp
            temps_c.append(None if temp_val is None else float(temp_val) - _KELVIN_TO_C)
            hum_val = hum.magnitude if hasattr(hum, 'magnitude') else hum
            hums.append(None if hum_val is None else float(hum_val))

        title_suffix = f' ({self.lab_id})' if self.lab_id else ''

        temp_fig = go.Figure(
            data=[go.Scatter(x=sorted_ts, y=temps_c, mode='lines+markers')]
        )
        temp_fig.update_layout(
            template='plotly_white',
            height=350,
            xaxis_title='Time',
            yaxis_title='Temperature (°C)',
            title_text=f'Temperature Trend{title_suffix}',
        )
        self.figures.append(
            PlotlyFigure(label='Temperature Trend', figure=temp_fig.to_plotly_json())
        )

        hum_fig = go.Figure(
            data=[go.Scatter(x=sorted_ts, y=hums, mode='lines+markers')]
        )
        hum_fig.update_layout(
            template='plotly_white',
            height=350,
            xaxis_title='Time',
            yaxis_title='Relative Humidity (%)',
            title_text=f'Humidity Trend{title_suffix}',
        )
        self.figures.append(
            PlotlyFigure(label='Humidity Trend', figure=hum_fig.to_plotly_json())
        )


class INLTestoLoggerReference(INLInstrumentReference):
    """Reference to an INLTestoLogger entry."""

    reference = Quantity(
        type=INLTestoLogger,
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.ReferenceEditQuantity,
            label='Testo Logger',
        ),
    )


m_package.__init_metainfo__()
