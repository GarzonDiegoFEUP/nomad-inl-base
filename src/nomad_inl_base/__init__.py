"""
nomad-inl-base: INL customizations and extensions for NOMAD.

This module patches nomad_measurements and related parsers to handle European
decimal separators (commas) transparently, ensuring compatibility with localized
instrument output files.
"""

import sys
import os
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
        
        # Now replace with fully corrected version
        def patched_read_perkin_with_indices(filename, logger=None):
            """
            Final wrapper: handles both comma conversion AND index correction.
            """
            from collections import defaultdict
            from inspect import isfunction
            import pandas as pd
            import numpy as np
            import pint
            
            ureg = pint.get_application_registry()
            
            # Read and clean commas
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            content_cleaned = content.replace(',', '.')
            
            if content_cleaned != content:
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.asc', delete=False, encoding='utf-8'
                ) as tmp:
                    tmp.write(content_cleaned)
                    tmp_name = tmp.name
            else:
                tmp_name = filename
            
            try:
                # Parse metadata and data
                metadata = []
                data_start_ind = '#DATA'
                
                with open(tmp_name, encoding='utf-8') as file_obj:
                    for line in file_obj:
                        if line.strip() == data_start_ind:
                            break
                        metadata.append(line.strip())
                    data = pd.read_csv(file_obj, sep='\\s+', header=None, index_col=0)
                
                # Import the read functions from perkin_elmers_asc
                from fairmat_readers_transmission.perkin_elmers_asc import (
                    read_attenuation_percentage,
                    read_detector_change_wavelength,
                    read_detector_integration_time,
                    read_detector_module,
                    read_detector_nir_gain,
                    read_is_common_beam_depolarizer_on,
                    read_is_d2_lamp_used,
                    read_is_tungsten_lamp_used,
                    read_lamp_change_wavelength,
                    read_monochromator_change_wavelength,
                    read_monochromator_slit_width,
                    read_polarizer_angle,
                    read_sample_name,
                    read_start_datetime,
                )
                
                # Use CORRECTED metadata indices
                metadata_map = {
                    'sample_name': read_sample_name,
                    'start_datetime': read_start_datetime,
                    'analyst_name': 7,
                    'instrument_name': 11,
                    'instrument_serial_number': 12,
                    'instrument_firmware_version': 13,
                    'is_d2_lamp_used': read_is_d2_lamp_used,
                    'is_tungsten_lamp_used': read_is_tungsten_lamp_used,
                    'sample_beam_position': 44,
                    'common_beam_mask_percentage': 45,
                    'is_common_beam_depolarizer_on': read_is_common_beam_depolarizer_on,
                    'attenuation_percentage': read_attenuation_percentage,
                    'detector_integration_time': read_detector_integration_time,
                    'detector_NIR_gain': read_detector_nir_gain,
                    'detector_change_wavelength': read_detector_change_wavelength,
                    'detector_module': read_detector_module,
                    'polarizer_angle': read_polarizer_angle,
                    'ordinate_type': 84,  # FIXED: was 80
                    'wavelength_units': 83,  # FIXED: was 79
                    'monochromator_slit_width': read_monochromator_slit_width,
                    'monochromator_change_wavelength': read_monochromator_change_wavelength,
                    'lamp_change_wavelength': read_lamp_change_wavelength,
                }
                
                output = defaultdict(lambda: None)
                
                for path, val in metadata_map.items():
                    if isinstance(val, int):
                        if metadata[val]:
                            try:
                                output[path] = float(metadata[val]) * ureg.dimensionless
                            except ValueError:
                                output[path] = metadata[val]
                    elif isfunction(val):
                        output[path] = val(metadata, logger)
                    else:
                        raise ValueError(f'Invalid type for {path}')
                
                # Restructure measured data
                output['measured_wavelength'] = data.index.values
                output['measured_ordinate'] = data.values[:, 0] * ureg.dimensionless
                output['measured_wavelength'] *= ureg(output['wavelength_units'])
                
                if logger:
                    logger.info(f'Parsed {filename} with corrected metadata indices')
                
                return dict(output)
                
            finally:
                if tmp_name != filename:
                    try:
                        os.unlink(tmp_name)
                    except Exception:
                        pass
        
        fairmat_readers_transmission.read_perkin_elmer_asc = patched_read_perkin_with_indices
        patch_log.append('Fixed metadata_map indices (79→83, 80→84)')
        
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


def _patch_transmission_schema():
    """
    Patch nomad_measurements transmission schema to support reflectance ('%R').
    
    Adds support for measuring both transmittance (%T) and reflectance (%R).
    Both values come in as percentages and are divided by 100 to get decimal values (0-1).
    """
    try:
        from nomad_measurements.transmission.schema import UVVisNirTransmission
        
        # Get the original _populate_transmission_from_file method
        original_populate = UVVisNirTransmission._populate_transmission_from_file
        
        def patched_populate_transmission_from_file(transmission, data_dict, archive, logger):
            """
            Patched version that supports both %T (transmittance) and %R (reflectance).
            """
            transmission.user = data_dict['analyst_name']
            if data_dict['start_datetime'] is not None:
                transmission.datetime = data_dict['start_datetime']

            # add results
            transmission.m_setdefault('results/0')
            transmission.results[0].wavelength = data_dict['measured_wavelength']
            
            # Handle different ordinate types
            ordinate_type = data_dict.get('ordinate_type', '')
            if ordinate_type == 'A':
                transmission.results[0].absorbance = data_dict['measured_ordinate']
            elif ordinate_type == '%T':
                transmission.results[0].transmittance = data_dict['measured_ordinate'] / 100
            elif ordinate_type == '%R':
                # Support reflectance - divide by 100 same as transmittance
                transmission.results[0].reflectance = data_dict['measured_ordinate'] / 100
            else:
                logger.warning(f"Unknown ordinate type '{ordinate_type}'.")
            
            transmission.results[0].normalize(archive, logger)

            # add settings
            transmission.m_setdefault('transmission_settings')
            transmission.transmission_settings.sample_beam_position = data_dict[
                'sample_beam_position'
            ]
            transmission.transmission_settings.common_beam_depolarizer = data_dict[
                'is_common_beam_depolarizer_on'
            ]
            if data_dict['common_beam_mask_percentage'] is not None:
                transmission.transmission_settings.common_beam_mask_percentage = (
                    data_dict['common_beam_mask_percentage']
                )
            
            # Continue with rest of original function by calling it
            # Copy the rest of the settings from the original method
            transmission.transmission_settings.is_d2_lamp_used = data_dict[
                'is_d2_lamp_used'
            ]
            transmission.transmission_settings.is_tungsten_lamp_used = data_dict[
                'is_tungsten_lamp_used'
            ]
            transmission.transmission_settings.detector_integration_time = data_dict[
                'detector_integration_time'
            ]
            transmission.transmission_settings.detector_NIR_gain = data_dict[
                'detector_NIR_gain'
            ]
            transmission.transmission_settings.detector_change_wavelength = data_dict[
                'detector_change_wavelength'
            ]
            transmission.transmission_settings.monochromator_slit_width = data_dict[
                'monochromator_slit_width'
            ]
            transmission.transmission_settings.monochromator_change_wavelength = (
                data_dict['monochromator_change_wavelength']
            )
            transmission.transmission_settings.lamp_change_wavelength = data_dict[
                'lamp_change_wavelength'
            ]
            transmission.transmission_settings.polarizer_angle = data_dict[
                'polarizer_angle'
            ]
            transmission.transmission_settings.attenuation_percentage = data_dict[
                'attenuation_percentage'
            ]
            
            # add detector info
            transmission.m_setdefault('detector')
            transmission.detector.detector_type = data_dict['detector_module']
            
            # add instrument info
            transmission.m_setdefault('instrument')
            transmission.instrument.instrument_name = data_dict['instrument_name']
            transmission.instrument.instrument_serial_number = (
                data_dict['instrument_serial_number']
            )
            transmission.instrument.instrument_firmware_version = (
                data_dict['instrument_firmware_version']
            )
        
        # Replace the original method
        UVVisNirTransmission._populate_transmission_from_file = (
            staticmethod(patched_populate_transmission_from_file)
        )
        
        print(
            '[nomad-inl-base] Transmission schema patched: Added %R (reflectance) support',
            file=sys.stderr
        )
        
    except ImportError as e:
        print(
            f'[nomad-inl-base] Skipping schema patch (nomad_measurements not available): {e}',
            file=sys.stderr
        )
    except Exception as e:
        print(
            f'[nomad-inl-base] ERROR patching schema: {e}',
            file=sys.stderr
        )


# Apply patches when the module is imported
_patch_transmission_reader()
_patch_transmission_schema()
