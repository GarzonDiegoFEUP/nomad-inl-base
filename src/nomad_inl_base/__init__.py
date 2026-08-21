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
    
    This is more reliable than schema-level patching because it handles the
    conversion at the file level, ensuring ALL downstream parsers/schemas
    receive correctly formatted data.
    """
    patch_log = []
    try:
        patch_log.append('Starting patch_transmission_reader...')
        
        import fairmat_readers_transmission
        patch_log.append('Successfully imported fairmat_readers_transmission')
        
        original_read_perkin = fairmat_readers_transmission.read_perkin_elmer_asc
        patch_log.append(f'Original read_perkin_elmer_asc: {original_read_perkin}')
        
        def patched_read_perkin(filename, logger=None):
            """
            Patched read_perkin_elmer_asc that preprocesses European decimal separators.
            
            Uses a two-stage approach:
            1. Try parsing original file
            2. If it fails, convert ALL commas in numeric contexts to periods and retry
            """
            try:
                # First, try to read the original file
                return original_read_perkin(filename, logger)
            except (AssertionError, ValueError, TypeError) as e:
                # If parsing fails, it might be due to European decimals
                # Read the file and do more aggressive comma conversion
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # More aggressive: convert ALL commas to periods, then retry
                # This is safe for European format files where comma is ALWAYS decimal separator
                content_cleaned = content.replace(',', '.')
                
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
        patch_log.append('Successfully patched fairmat_readers_transmission.read_perkin_elmer_asc')
        
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
