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
    Patch fairmat_readers_transmission.read_perkin_elmer_asc() to preprocess
    European decimal separators BEFORE parsing.
    
    This ALWAYS converts commas to periods for European format files.
    Safe because European .asc files ONLY use comma for decimal separation.
    """
    patch_log = []
    try:
        patch_log.append('Starting patch_transmission_reader...')
        
        import fairmat_readers_transmission
        patch_log.append('Successfully imported fairmat_readers_transmission')
        
        original_read_perkin = fairmat_readers_transmission.read_perkin_elmer_asc
        patch_log.append(f'Original read_perkin_elmer_asc found')
        
        def patched_read_perkin(filename, logger=None):
            """
            Patched read_perkin_elmer_asc that ALWAYS converts comma decimals.
            
            For European format .asc files, commas are ONLY used as decimal separators.
            This converts all commas to periods BEFORE parsing, ensuring the parser
            always sees standard decimal point notation.
            """
            # Read the original file
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ALWAYS convert ALL commas to periods for European format handling
            # This is safe because commas in European .asc files are ONLY decimal separators
            content_cleaned = content.replace(',', '.')
            
            # Only write temp file if content actually changed
            if content_cleaned == content:
                # No commas found, use original file
                return original_read_perkin(filename, logger)
            
            # Commas were found and converted - parse the cleaned version
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
                    logger.info(
                        f'Successfully parsed {filename} after converting commas to periods'
                    )
                return result
            finally:
                try:
                    os.unlink(tmp_name)
                except Exception:
                    pass
        
        fairmat_readers_transmission.read_perkin_elmer_asc = patched_read_perkin
        patch_log.append('Successfully patched read_perkin_elmer_asc')
        
        print(
            f'[nomad-inl-base] Transmission reader patch applied: {" | ".join(patch_log)}',
            file=sys.stderr
        )
        
    except ImportError as e:
        print(
            f'[nomad-inl-base] Skipping reader patch (fairmat_readers_transmission not available): {e}',
            file=sys.stderr
        )
    except Exception as e:
        print(
            f'[nomad-inl-base] ERROR applying reader patch: {e}',
            file=sys.stderr
        )


# Apply patches when the module is imported
_patch_transmission_reader()
