"""
nomad-inl-base: INL customizations and extensions for NOMAD.

This module uses the enhanced nomad_measurements fork which includes:
- Reflectance (%R) measurement support
- European decimal separator handling (commas → periods)
- Corrected PerkinElmer metadata indices

No patching needed with the forked version!
"""

import sys


def plugin_load(plugin_config):
    """NOMAD plugin hook called after plugin discovery and full initialization."""
    print(
        '[nomad-inl-base] Using forked nomad-measurements with reflectance support',
        file=sys.stderr
    )
    return None
