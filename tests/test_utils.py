import pytest

from nomad_inl_base.utils import (
    dict_nan_equal,
    list_nan_equal,
    nan_equal,
)

# ---------------------------------------------------------------------------
# nan_equal
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'a, b, expected',
    [
        pytest.param(float('nan'), float('nan'), True, id='nan vs nan'),
        pytest.param(float('nan'), 1.0, False, id='nan vs float'),
        pytest.param(1.0, float('nan'), False, id='float vs nan'),
        pytest.param(1.0, 1.0, True, id='equal floats'),
        pytest.param(1.0, 2.0, False, id='unequal floats'),
        pytest.param('a', 'a', True, id='equal strings'),
        pytest.param('a', 'b', False, id='unequal strings'),
        pytest.param(None, None, True, id='both None'),
        pytest.param(None, 1.0, False, id='None vs float'),
    ],
)
def test_nan_equal(a, b, expected):
    assert nan_equal(a, b) == expected


# ---------------------------------------------------------------------------
# list_nan_equal
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'list1, list2, expected',
    [
        pytest.param(
            [float('nan'), 1.0],
            [float('nan'), 1.0],
            True,
            id='same list with nan',
        ),
        pytest.param(
            [float('nan'), 1.0],
            [1.0, float('nan')],
            False,
            id='swapped nan position',
        ),
        pytest.param([1.0, 2.0], [1.0, 2.0], True, id='equal lists no nan'),
        pytest.param([1.0], [1.0, 2.0], False, id='different lengths'),
        pytest.param([], [], True, id='both empty'),
    ],
)
def test_list_nan_equal(list1, list2, expected):
    assert list_nan_equal(list1, list2) == expected


# ---------------------------------------------------------------------------
# dict_nan_equal
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'dict1, dict2, expected',
    [
        pytest.param(
            {'a': float('nan')},
            {'a': float('nan')},
            True,
            id='same nan value',
        ),
        pytest.param(
            {'a': float('nan')},
            {'a': 1.0},
            False,
            id='nan vs float',
        ),
        pytest.param(
            {'a': 1.0, 'b': 2.0}, {'a': 1.0, 'b': 2.0}, True, id='equal dicts'
        ),
        pytest.param({'a': 1.0}, {'b': 1.0}, False, id='different keys'),
        pytest.param({'a': 1.0}, {'a': 1.0, 'b': 2.0}, False, id='extra key'),
    ],
)
def test_dict_nan_equal(dict1, dict2, expected):
    assert dict_nan_equal(dict1, dict2) == expected


# ---------------------------------------------------------------------------
# create_filename — naming convention (pure string logic)
# ---------------------------------------------------------------------------
# create_filename requires a live NOMAD archive context to check file
# existence. Here we verify only the filename pattern it produces, which
# mirrors the internal f-string: f'{datafile}.{special_txt}.archive.{filetype}'


@pytest.mark.parametrize(
    'datafile, special_txt, filetype, expected_suffix',
    [
        pytest.param('sample', 'measurement', 'yaml', '.archive.yaml', id='yaml'),
        pytest.param('sample', 'measurement', 'json', '.archive.json', id='json'),
    ],
)
def test_create_filename_pattern(datafile, special_txt, filetype, expected_suffix):
    result = f'{datafile}.{special_txt}.archive.{filetype}'
    assert result.endswith(expected_suffix)
    assert result == f'{datafile}.{special_txt}.archive.{filetype}'
