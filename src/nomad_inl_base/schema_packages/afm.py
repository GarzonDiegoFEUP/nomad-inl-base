# AFM classes (INLAFMChannel, INLAFMSession) now live in characterization.py
# and are exposed through the existing characterization_entry_point.
# This module is kept for backward-compatibility imports only.
from nomad_inl_base.schema_packages.characterization import (  # noqa: F401
    INLAFMChannel,
    INLAFMSession,
)

# Legacy aliases
AFMChannel = INLAFMChannel
BrukerAFMMeasurement = INLAFMSession
