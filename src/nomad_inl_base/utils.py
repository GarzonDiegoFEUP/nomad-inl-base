import json
import math

import yaml
from nomad.datamodel.context import ClientContext
from nomad.units import ureg


def get_reference(upload_id, entry_id):
    return f'../uploads/{upload_id}/archive/{entry_id}'


def get_entry_id(upload_id, filename):
    from nomad.utils import hash

    return hash(upload_id, filename)


def get_hash_ref(upload_id, filename):
    return f'{get_reference(upload_id, get_entry_id(upload_id, filename))}#data'


def dict_nan_equal(dict1, dict2):
    """
    Compare two dictionaries with NaN values.
    """
    if set(dict1.keys()) != set(dict2.keys()):
        return False
    for key in dict1:
        if not nan_equal(dict1[key], dict2[key]):
            return False
    return True


def nan_equal(a, b):
    """
    Compare two values with NaN values.
    """
    if isinstance(a, float) and isinstance(b, float):
        return a == b or (math.isnan(a) and math.isnan(b))
    elif isinstance(a, dict) and isinstance(b, dict):
        return dict_nan_equal(a, b)
    elif isinstance(a, list) and isinstance(b, list):
        return list_nan_equal(a, b)
    else:
        return a == b


def list_nan_equal(list1, list2):
    """
    Compare two lists with NaN values.
    """
    if len(list1) != len(list2):
        return False
    for a, b in zip(list1, list2):
        if not nan_equal(a, b):
            return False
    return True


def create_filename(
    datafile, data_measurement, special_txt, archive, logger, filetype='yaml'
):
    from nomad.datamodel.datamodel import EntryArchive, EntryMetadata

    # create a filename and archive

    filename = f'{datafile}.{special_txt}.archive.{filetype}'

    if archive.m_context.raw_path_exists(filename):
        logger.warn(f'Process archive already exists: {filename}')
    else:
        archive = EntryArchive(
            data=data_measurement,
            m_context=archive.m_context,
            metadata=EntryMetadata(upload_id=archive.m_context.upload_id),
        )

    return filename, archive


def create_archive(
    entry_dict, context, filename, file_type, logger, *, overwrite: bool = False
):
    import re as _re

    # Custom YAML dumper that guarantees all floats are written with a decimal
    # point so that PyYAML safe_load always reads them back as float, not str.
    # e.g.  -4e-13  →  -4.0e-13
    class _SafeFloatDumper(yaml.SafeDumper):
        pass

    def _represent_float(dumper, value):
        import math

        if math.isnan(value):
            return dumper.represent_scalar('tag:yaml.org,2002:float', '.nan')
        if value == float('inf'):
            return dumper.represent_scalar('tag:yaml.org,2002:float', '.inf')
        if value == float('-inf'):
            return dumper.represent_scalar('tag:yaml.org,2002:float', '-.inf')
        text = repr(value)
        # Insert .0 before 'e' only when the mantissa has no decimal point.
        # e.g. '-4e-13' → '-4.0e-13', '8e-13' → '8.0e-13'
        # but '2.4e-12' and '7.6e-12' are left unchanged (already have decimal).
        if _re.search(r'^-?[0-9]+[eE]', text):
            text = text.replace('e', '.0e', 1).replace('E', '.0E', 1)
        return dumper.represent_scalar('tag:yaml.org,2002:float', text)

    _SafeFloatDumper.add_representer(float, _represent_float)
    file_exists = context.raw_path_exists(filename)
    dicts_are_equal = None
    if isinstance(context, ClientContext):
        return None
    if file_exists:
        with context.raw_file(filename, 'r') as file:
            existing_dict = yaml.safe_load(file)
            dicts_are_equal = dict_nan_equal(existing_dict, entry_dict)
    if not file_exists or overwrite or dicts_are_equal:
        with context.raw_file(filename, 'w') as newfile:
            if file_type == 'json':
                json.dump(entry_dict, newfile)
            elif file_type == 'yaml':
                yaml.dump(entry_dict, newfile, Dumper=_SafeFloatDumper)
        context.upload.process_updated_raw_file(filename, allow_modify=True)
    elif file_exists and not overwrite and not dicts_are_equal:
        logger.error(
            f'{filename} archive file already exists. '
            f'You are trying to overwrite it with a different content. '
            f'To do so, remove the existing archive and click reprocess again.'
        )
    return get_hash_ref(context.upload_id, filename)


def create_child_entry(
    entry,
    archive,
    child_filename: str,
    filetype: str,
    raw_name: str,
    raw_ref: str,
    logger,
    *,
    guard: bool = False,
    overwrite: bool = False,
):
    """Write a child archive and set ``archive.data`` appropriately.

    In a server context the child ``.archive.yaml`` file is written and
    ``archive.data`` is set to a :class:`RawFile_` pointer so the raw-file
    entry and the editable measurement entry remain separate.  User edits
    (e.g. adding sample references) are preserved because ``create_archive``
    skips overwriting files whose content has changed.

    When ``guard=True`` the child archive is only written if it does not yet
    exist (used by parsers like MPR and SEM that want strict edit preservation).

    When ``overwrite=True`` the child archive is always written, even if it
    already exists with different content (used when the schema has changed and
    stale sidecar YAMLs must be regenerated).

    In a local / test :class:`ClientContext` ``create_archive`` is a no-op so
    the child file is never written.  In that case ``archive.data`` is set
    directly to the entry object so tests can inspect the parsed data.
    """
    from nomad.datamodel.context import ClientContext
    from nomad.datamodel.datamodel import EntryArchive, EntryMetadata

    if not guard or not archive.m_context.raw_path_exists(child_filename):
        child_archive = EntryArchive(
            data=entry,
            metadata=EntryMetadata(upload_id=archive.m_context.upload_id),
        )
        create_archive(
            child_archive.m_to_dict(),
            archive.m_context,
            child_filename,
            filetype,
            logger,
            overwrite=overwrite,
        )

    if isinstance(archive.m_context, ClientContext):
        archive.data = entry
    else:
        from nomad_inl_base.parsers.parser import RawFile_

        archive.data = RawFile_(name=raw_name, file_=raw_ref)


def fill_quantity(dataframe, column_header, read_unit=None):
    """
    Fetches a value from a DataFrame and optionally converts it to a specified unit.
    """
    try:
        if not dataframe[column_header].empty:
            value = dataframe[column_header]
        else:
            value = None
    except (KeyError, IndexError):
        value = None

    pint_value = None
    if read_unit is not None:
        try:
            if value is not None:
                pint_value = ureg.Quantity(
                    value.to_numpy(),
                    ureg(read_unit),
                )

            else:
                value = None
        except ValueError:
            if hasattr(value, 'empty') and not value.empty():
                pint_value = ureg.Quantity(
                    value.to_numpy(),
                    ureg(read_unit),
                )
            elif value == '':
                pint_value = None

    return pint_value if read_unit is not None else value
