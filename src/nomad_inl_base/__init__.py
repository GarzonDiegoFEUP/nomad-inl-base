"""
nomad-inl-base: INL customizations and extensions for NOMAD.

This module patches nomad_measurements and related parsers to handle European
decimal separators (commas) transparently, ensuring compatibility with localized
instrument output files.
"""

import sys
import re


def _patch_transmission_reader():
    """
    Patch fairmat_readers_transmission functions to handle European decimal separators
    and problematic metadata fields.
    
    Two-level patching strategy:
    1. Patch file reader to convert commas to periods
    2. Patch read_detector_module function to return standard value
    """
    patch_log = []
    try:
        patch_log.append('Starting patch_transmission_reader...')
        
        import fairmat_readers_transmission
        patch_log.append('Imported fairmat_readers_transmission')
        
        # Import and patch the perkin_elmers_asc module functions
        import fairmat_readers_transmission.perkin_elmers_asc as perkin_module
        patch_log.append('Imported perkin_elmers_asc')
        
        # Patch read_detector_module to return standard value
        original_read_detector = perkin_module.read_detector_module
        
        def patched_read_detector_module(metadata, logger=None):
            """Patched version that returns standard Integrated Sphere value."""
            try:
                # Try original function first
                return original_read_detector(metadata, logger)
            except Exception as e:
                # If it fails (due to commas or parsing issues), return standard value
                if logger:
                    logger.warning(
                        f'read_detector_module failed ({e}), using default "Integrated Sphere"'
                    )
                return 'Integrated Sphere'
        
        perkin_module.read_detector_module = patched_read_detector_module
        patch_log.append('Patched read_detector_module to handle parsing errors')
        
        # Also patch the main read_perkin_elmer_asc function
        original_read_perkin = fairmat_readers_transmission.read_perkin_elmer_asc
        
        def patched_read_perkin(filename, logger=None):
            """
            Patched read_perkin_elmer_asc that converts comma decimals to periods.
            
            European .asc files use commas as decimal separators.
            This converts them to periods BEFORE parsing.
            """
            # Read the original file
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convert ALL commas to periods (safe for European format)
            content_cleaned = content.replace(',', '.')
            
            # Only write temp file if content actually changed
            if content_cleaned == content:
                return original_read_perkin(filename, logger)
            
            # Parse the cleaned version
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.asc', delete=False, encoding='utf-8'
            ) as tmp:
                tmp.write(content_cleaned)
                tmp_name = tmp.name
            
            try:
                result = original_read_perkin(tmp_name, logger)
                if logger:
                    logger.info(f'Parsed {filename} after converting commas to periods')
                return result
            finally:
                try:
                    os.unlink(tmp_name)
                except Exception:
                    pass
        
        fairmat_readers_transmission.read_perkin_elmer_asc = patched_read_perkin
        patch_log.append('Patched read_perkin_elmer_asc for comma conversion')
        
        print(
            f'[nomad-inl-base] Transmission patches applied: {" | ".join(patch_log)}',
            file=sys.stderr
        )
        
    except ImportError as e:
        print(
            f'[nomad-inl-base] Skipping patches (fairmat_readers_transmission not available): {e}',
            file=sys.stderr
        )
    except Exception as e:
        print(
            f'[nomad-inl-base] ERROR applying patches: {e}',
            file=sys.stderr
        )


# Apply patches when the module is imported
_patch_transmission_reader()
