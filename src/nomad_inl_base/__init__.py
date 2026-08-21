"""
nomad-inl-base: INL customizations and extensions for NOMAD.

This module patches nomad_measurements schemas to handle European decimal separators
(commas) transparently, ensuring compatibility with localized instrument output files.
"""

import sys


def _coerce_comma_decimals_inline(dct):
    """Inline coercion function to avoid circular imports.
    
    Converts comma decimal separators to periods recursively throughout a dict.
    """
    def _convert_value(val):
        if isinstance(val, str):
            try:
                val_normalized = val.strip()
                if ',' in val_normalized:
                    val_normalized = val_normalized.replace(',', '.')
                return float(val_normalized)
            except (ValueError, TypeError):
                return val
        elif isinstance(val, dict):
            return _coerce_comma_decimals_inline(val)
        else:
            return val

    out = {}
    for key, val in dct.items():
        if isinstance(val, list):
            out[key] = [_convert_value(item) for item in val]
        elif isinstance(val, dict):
            out[key] = _coerce_comma_decimals_inline(val)
        else:
            out[key] = _convert_value(val)
    return out


def _patch_transmission_schema():
    """
    Monkey-patch nomad_measurements.transmission.schema.ELNUVVisNirTransmission
    to handle European decimal separators (commas).
    
    This ensures that regardless of which parser processes the file, the schema
    will correctly convert comma-separated decimals (e.g., "79,803") to floats.
    """
    patch_log = []
    try:
        patch_log.append('Starting patch_transmission_schema...')
        
        from nomad_measurements.transmission.schema import ELNUVVisNirTransmission
        patch_log.append('Successfully imported ELNUVVisNirTransmission')
        
        # Store the original method
        original_update = ELNUVVisNirTransmission.m_update_from_dict
        patch_log.append(f'Original m_update_from_dict: {original_update}')
        
        def patched_update(self, dct, **kwargs):
            """
            Patched m_update_from_dict that preprocesses comma decimals.
            """
            # Preprocess the dictionary to convert comma decimals to periods
            dct_cleaned = _coerce_comma_decimals_inline(dct)
            # Call the original update with cleaned data
            return original_update(self, dct_cleaned, **kwargs)
        
        # Replace the method
        ELNUVVisNirTransmission.m_update_from_dict = patched_update
        patch_log.append('Successfully patched ELNUVVisNirTransmission.m_update_from_dict')
        
        # Print patch log to stderr so we can see it in logs
        print(
            f'[nomad-inl-base] Transmission schema patch applied: {" | ".join(patch_log)}',
            file=sys.stderr
        )
        
    except ImportError as e:
        print(
            f'[nomad-inl-base] Skipping transmission patch (nomad_measurements not available): {e}',
            file=sys.stderr
        )
    except Exception as e:
        print(
            f'[nomad-inl-base] ERROR applying transmission patch: {e}',
            file=sys.stderr
        )


# Apply the patch when the module is imported
_patch_transmission_schema()
