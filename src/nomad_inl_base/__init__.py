"""
nomad-inl-base: INL customizations and extensions for NOMAD.

This module patches nomad_measurements schemas to handle European decimal separators
(commas) transparently, ensuring compatibility with localized instrument output files.
"""


def _patch_transmission_schema():
    """
    Monkey-patch nomad_measurements.transmission.schema.ELNUVVisNirTransmission
    to handle European decimal separators (commas).
    
    This ensures that regardless of which parser processes the file, the schema
    will correctly convert comma-separated decimals (e.g., "79,803") to floats.
    """
    try:
        from nomad_measurements.transmission.schema import ELNUVVisNirTransmission
        
        # Import the coercion helper from our characterization module
        from nomad_inl_base.schema_packages.characterization import _coerce_string_floats
        
        # Store the original method
        original_update = ELNUVVisNirTransmission.m_update_from_dict
        
        def patched_update(self, dct, **kwargs):
            """
            Patched m_update_from_dict that preprocesses comma decimals.
            """
            # Preprocess the dictionary to convert comma decimals to periods
            dct_cleaned = _coerce_string_floats(dct, handle_comma_decimals=True)
            # Call the original update with cleaned data
            return original_update(self, dct_cleaned, **kwargs)
        
        # Replace the method
        ELNUVVisNirTransmission.m_update_from_dict = patched_update
    except ImportError:
        # nomad_measurements might not be available in all contexts
        pass
    except Exception as e:
        # Silently fail patching; original functionality still works
        pass


# Apply the patch when the module is imported
_patch_transmission_schema()
