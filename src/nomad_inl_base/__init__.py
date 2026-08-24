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
            if logger:
                logger.info(f'[PATCH READER] Starting to parse {filename}')
            
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
            
            if logger and content_cleaned != content:
                logger.info(f'[PATCH READER] Converted commas to periods in {filename}')
            
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
                    'ordinate_type': 84,  # FIXED: was 80 (line 85 in file: %T, A, or %R)
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
                                # DEBUG: Log what we got for ordinate_type
                                if path == 'ordinate_type' and logger:
                                    logger.info(f'[PATCH READER] ordinate_type at metadata[{val}] = {repr(output[path])}')
                    elif isfunction(val):
                        output[path] = val(metadata, logger)
                    else:
                        raise ValueError(f'Invalid type for {path}')
                
                # Restructure measured data
                output['measured_wavelength'] = data.index.values
                output['measured_ordinate'] = data.values[:, 0] * ureg.dimensionless
                output['measured_wavelength'] *= ureg(output['wavelength_units'])
                
                if logger:
                    logger.info(f'[PATCH READER] Successfully parsed {filename}')
                    logger.info(f'[PATCH READER] ordinate_type from data_dict: {repr(output.get("ordinate_type"))}')
                
                return dict(output)
                
            finally:
                if tmp_name != filename:
                    try:
                        os.unlink(tmp_name)
                    except Exception:
                        pass
        
        fairmat_readers_transmission.read_perkin_elmer_asc = patched_read_perkin_with_indices
        patch_log.append('Fixed metadata_map indices (79→83, 80→84)')
        
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
    
    Adds:
    1. reflectance field to UVVisNirTransmissionResult
    2. Updates the schema section order to include reflectance
    3. Updates generate_plots to plot reflectance
    4. Patches normalize() directly to fix ordinate_type key issue
    
    Now supports measuring: absorbance (A), transmittance (%T), and reflectance (%R).
    """
    try:
        from nomad_measurements.transmission.schema import (
            UVVisNirTransmission,
            UVVisNirTransmissionResult,
        )
        from nomad.metainfo import Quantity
        import numpy as np
        
        # Patch 1: Add reflectance field to UVVisNirTransmissionResult
        if not hasattr(UVVisNirTransmissionResult, '_reflectance_patched'):
            reflectance_field = Quantity(
                type=np.float64,
                description='Measured reflectance ranging from 0 to 1.',
                shape=['*'],
                unit='dimensionless',
                a_plot={'x': 'array_index', 'y': 'reflectance'},
            )
            UVVisNirTransmissionResult.m_def.all_quantities['reflectance'] = (
                reflectance_field
            )
            UVVisNirTransmissionResult.reflectance = reflectance_field
            UVVisNirTransmissionResult._reflectance_patched = True
            print('[nomad-inl-base] Patch 1: Added reflectance field', file=sys.stderr)
        
        # Patch 2: Update m_eln section order to include reflectance
        if hasattr(UVVisNirTransmissionResult.m_def, 'a_eln'):
            if UVVisNirTransmissionResult.m_def.a_eln:
                if hasattr(
                    UVVisNirTransmissionResult.m_def.a_eln, 'properties'
                ) and UVVisNirTransmissionResult.m_def.a_eln.properties:
                    props = UVVisNirTransmissionResult.m_def.a_eln.properties
                    if hasattr(props, 'order') and props.order:
                        if 'reflectance' not in props.order:
                            # Add reflectance after absorbance in the order
                            if 'absorbance' in props.order:
                                idx = props.order.index('absorbance')
                                props.order.insert(idx + 1, 'reflectance')
                            else:
                                props.order.append('reflectance')
            print('[nomad-inl-base] Patch 2: Updated schema order', file=sys.stderr)
        
        # Patch 3: Update generate_plots method
        original_generate_plots = UVVisNirTransmissionResult.generate_plots
        
        def patched_generate_plots(self):
            """
            Patched version that generates plots for transmittance, absorbance, AND reflectance.
            """
            import plotly.express as px
            
            figures = []
            if self.wavelength is None:
                return figures

            for key in ['transmittance', 'absorbance', 'reflectance']:
                if getattr(self, key, None) is None:
                    continue

                x_label = 'Wavelength'
                xaxis_title = f'{x_label} (nm)'
                x = self.wavelength.to('nm').magnitude

                y_label = key.capitalize()
                yaxis_title = y_label
                y = getattr(self, key).magnitude

                line_linear = px.line(x=x, y=y)

                line_linear.update_layout(
                    title=f'{y_label} over {x_label}',
                    xaxis_title=xaxis_title,
                    yaxis_title=yaxis_title,
                    xaxis=dict(
                        fixedrange=False,
                    ),
                    yaxis=dict(
                        fixedrange=False,
                    ),
                    template='plotly_white',
                )

                from nomad.datamodel.metainfo.plot import PlotlyFigure
                figures.append(
                    PlotlyFigure(
                        label=f'{y_label} linear plot',
                        figure=line_linear.to_plotly_json(),
                    ),
                )

            return figures

        UVVisNirTransmissionResult.generate_plots = patched_generate_plots
        print('[nomad-inl-base] Patch 3: Updated generate_plots method', file=sys.stderr)
        
        # Patch 4: Patch the normalize function directly to intercept write_transmission_data calls
        # This is necessary because normalize has a pre-bound reference to the original write_transmission_data
        if hasattr(UVVisNirTransmission, 'normalize'):
            original_normalize = UVVisNirTransmission.normalize
            
            def patched_normalize(self, archive, logger):
                """
                Patched normalize that intercepts write_transmission_data to handle %R.
                """
                # Import locally to get the schema module's write_transmission_data
                from nomad_measurements.transmission.schema import write_transmission_data
                import sys
                from io import StringIO
                
                # We need to intercept the call. We'll monkey-patch write_transmission_data
                # temporarily inside this normalize call
                
                # Store the original function
                original_write = write_transmission_data
                
                # Create our patched version
                def patched_write_transmission_data(transmission, data_dict, archive, logger):
                    """
                    Patched version that adds support for %R (reflectance).
                    Also fixes the key access bug in the else clause.
                    """
                    ordinate_type = data_dict.get('ordinate_type')
                    
                    # DEBUG: Print what we got
                    if logger:
                        logger.info(f'[PATCH write_transmission_data] ordinate_type = {repr(ordinate_type)}')
                    
                    # Strip whitespace just in case
                    if isinstance(ordinate_type, str):
                        ordinate_type = ordinate_type.strip()
                    
                    if ordinate_type == 'A':
                        transmission.results[0].absorbance = data_dict['measured_ordinate']
                        if logger:
                            logger.info(f'[PATCH] Set absorbance')
                    elif ordinate_type == '%T':
                        transmission.results[0].transmittance = data_dict['measured_ordinate'] / 100
                        if logger:
                            logger.info(f'[PATCH] Set transmittance')
                    elif ordinate_type == '%R':
                        # NEW: Handle reflectance type
                        transmission.results[0].reflectance = data_dict['measured_ordinate'] / 100
                        if logger:
                            logger.info(f'[PATCH] Set reflectance - value from 0-100 divided by 100')
                    else:
                        # FIXED: Use correct key name 'ordinate_type' not 'ordinate'
                        if logger:
                            logger.warning(f"[PATCH] Unknown ordinate type '{ordinate_type}'. data_dict keys: {list(data_dict.keys())}")
                
                # Temporarily inject our patched version into the module namespace
                import nomad_measurements.transmission.schema as schema_module
                schema_module.write_transmission_data = patched_write_transmission_data
                
                try:
                    # Call the original normalize with our patched write_transmission_data in place
                    return original_normalize(self, archive, logger)
                finally:
                    # Restore the original
                    schema_module.write_transmission_data = original_write
            
            UVVisNirTransmission.normalize = patched_normalize
            print('[nomad-inl-base] Patch 4: Patched normalize() to intercept write_transmission_data', file=sys.stderr)
        
        print(
            '[nomad-inl-base] Transmission schema fully patched: '
            'Added reflectance field, updated order, plots, and normalize intercept',
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



# Apply reader patches immediately (no circular imports from fairmat_readers)
try:
    _patch_transmission_reader()
    print('[nomad-inl-base] Reader patches applied successfully', file=sys.stderr)
except ImportError:
    # fairmat_readers not available yet - will skip silently
    pass
except Exception as e:
    print(f'[nomad-inl-base] Error applying reader patches: {e}', file=sys.stderr)


# Lazy schema patch application to avoid circular imports during NOMAD initialization
_schema_patches_applied = False


def _apply_schema_patches_lazy():
    """Apply schema patches after NOMAD is fully initialized."""
    global _schema_patches_applied
    if _schema_patches_applied:
        return
    
    _schema_patches_applied = True
    try:
        _patch_transmission_schema()
    except Exception as e:
        print(
            f'[nomad-inl-base] Error applying schema patches: {e}',
            file=sys.stderr
        )


# Register schema patch to apply at NOMAD initialization time
def plugin_load(plugin_config):
    """NOMAD plugin hook called after plugin discovery and full initialization."""
    _apply_schema_patches_lazy()
    return None
