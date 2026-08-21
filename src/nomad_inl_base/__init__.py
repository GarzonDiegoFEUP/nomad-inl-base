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
    Patch fairmat_readers_transmission.readers.read_file() to preprocess
    European decimal separators BEFORE parsing.
    
    This is more reliable than schema-level patching because it handles the
    conversion at the file level, ensuring ALL downstream parsers/schemas
    receive correctly formatted data.
    """
    patch_log = []
    try:
        patch_log.append('Starting patch_transmission_reader...')
        
        from fairmat_readers_transmission import readers
        patch_log.append('Successfully imported fairmat_readers_transmission.readers')
        
        original_read_file = readers.read_file
        patch_log.append(f'Original read_file: {original_read_file}')
        
        def patched_read_file(filename, logger=None):
            """
            Patched read_file that preprocesses European decimal separators.
            """
            # Read the file
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Preprocess: replace comma decimal separators with periods
            # Pattern: digit, digit (e.g., "123,456" -> "123.456")
            content_cleaned = re.sub(r'(\d),(\d)', r'\1.\2', content)
            
            # If content changed, write to temp and parse temp file
            if content_cleaned != content:
                import tempfile
                with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.asc', delete=False, encoding='utf-8'
                ) as tmp:
                    tmp.write(content_cleaned)
                    tmp_name = tmp.name
                
                try:
                    result = original_read_file(tmp_name, logger)
                    return result
                finally:
                    try:
                        import os
                        os.unlink(tmp_name)
                    except Exception:
                        pass
            else:
                # No commas found, use original file
                return original_read_file(filename, logger)
        
        readers.read_file = patched_read_file
        patch_log.append('Successfully patched fairmat_readers_transmission.readers.read_file')
        
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
