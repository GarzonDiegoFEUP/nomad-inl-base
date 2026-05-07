import logging
import os
import zipfile

import pytest
import structlog
from nomad.client import parse
from nomad.utils import structlogging
from structlog.testing import LogCapture

structlogging.ConsoleFormatter.short_format = True
setattr(logging, 'Formatter', structlogging.ConsoleFormatter)


@pytest.fixture(name='caplog', scope='function')
def fixture_caplog(request):
    """
    Captures structlog log entries and raises an assertion error if any log
    entry matches a level listed in ``request.param``.

    Usage::

        @pytest.mark.parametrize('caplog', (['error', 'critical'],), indirect=True)
        def test_something(parsed_archive, caplog):
            ...

    If no ``indirect`` param is provided, defaults to checking for
    ``['error', 'critical']``.
    """
    caplog_fixture = LogCapture()
    processors = structlog.get_config()['processors']
    old_processors = processors.copy()

    forbidden_levels = getattr(request, 'param', ['error', 'critical'])

    try:
        processors.clear()
        processors.append(caplog_fixture)
        structlog.configure(processors=processors)
        yield caplog_fixture
        for record in caplog_fixture.entries:
            if record['log_level'] in forbidden_levels:
                assert False, record
    finally:
        processors.clear()
        processors.extend(old_processors)


@pytest.fixture(name='parsed_archive', scope='function')
def fixture_parsed_archive(request):
    """
    Parses a data file and yields the resulting ``EntryArchive``.

    Accepts either a plain file path string or a tuple
    ``(file_path, [extra_extensions])`` to clean up additional generated files
    (e.g. ``'.nxs'``, ``'.h5'``) alongside the default ``'.archive.json'``.

    Usage::

        @pytest.mark.parametrize('parsed_archive', ('tests/data/sample.txt',), indirect=True)
        def test_something(parsed_archive):
            assert parsed_archive.data is not None

        # With extra cleanup:
        @pytest.mark.parametrize(
            'parsed_archive', (('tests/data/sample.txt', ['.nxs']),), indirect=True
        )
        def test_something(parsed_archive):
            ...
    """
    clean_up_extensions = ['.archive.json']
    if isinstance(request.param, (tuple, list)):
        rel_file_path = request.param[0]
        clean_up_extensions.extend(request.param[1])
    else:
        rel_file_path = request.param

    archives = parse(rel_file_path)
    assert archives, f'No archives parsed from {rel_file_path}'
    entry_archive = archives[0]

    yield entry_archive

    base = rel_file_path.rsplit('.', 1)[0]
    for ext in clean_up_extensions:
        path = base + ext
        if os.path.exists(path):
            os.remove(path)


@pytest.fixture(name='sem_zip', scope='function')
def fixture_sem_zip(tmp_path):
    """
    Creates a temporary zip archive containing the SEM TIFF test file,
    named so that ``SEMZipParser`` pattern ``YYMMDD - *.zip`` matches it.

    Returns the path to the created zip file.
    """
    tif_src = os.path.join('tests', 'data', '250416 - sample.tif')
    zip_path = str(tmp_path / '250416 - sample.zip')

    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.write(tif_src, arcname='250416 - sample.tif')

    yield zip_path

    if os.path.exists(zip_path):
        os.remove(zip_path)
    archive_json = zip_path.rsplit('.', 1)[0] + '.archive.json'
    if os.path.exists(archive_json):
        os.remove(archive_json)
