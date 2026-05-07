import pytest
from nomad.client import normalize_all, parse

# ---------------------------------------------------------------------------
# Demo / template schema
# ---------------------------------------------------------------------------


def test_new_schema_package():
    entry_archive = parse('tests/data/test.archive.yaml')[0]
    normalize_all(entry_archive)
    assert entry_archive.data.message == 'Hello Markus!'


# ---------------------------------------------------------------------------
# INLSubstrate — geometry auto-created on normalize
# ---------------------------------------------------------------------------


def test_inl_substrate():
    entry_archive = parse('tests/data/schemas/substrate.archive.yaml')[0]
    normalize_all(entry_archive)
    data = entry_archive.data
    assert data.name == 'TestSubstrate'
    assert data.material == 'SLG'
    assert data.geometry is not None
    # Default height is 1 mm → 0.001 m
    assert data.geometry.height.magnitude == pytest.approx(0.001, rel=1e-3)


# ---------------------------------------------------------------------------
# INLThinFilm — geometry height set from thickness
# ---------------------------------------------------------------------------


def test_inl_thinfilm():
    entry_archive = parse('tests/data/schemas/thinfilm.archive.yaml')[0]
    normalize_all(entry_archive)
    data = entry_archive.data
    assert data.name == 'TestFilm'
    assert data.material == 'CIGS'
    assert data.geometry is not None
    assert data.geometry.height.magnitude == pytest.approx(2.0e-6, rel=1e-3)


# ---------------------------------------------------------------------------
# INLCleaning — steps parsed, no substrate creation in test mode
# ---------------------------------------------------------------------------


def test_inl_cleaning():
    entry_archive = parse('tests/data/schemas/cleaning.archive.yaml')[0]
    normalize_all(entry_archive)
    data = entry_archive.data
    assert data.substrate_material == 'SLG'
    assert len(data.steps) == 3
    step_names = [s.name for s in data.steps]
    assert 'Acetone' in step_names
    assert 'IPA' in step_names
    assert 'DI Water' in step_names


# ---------------------------------------------------------------------------
# INLSpinCoating — step parameters preserved after normalize
# ---------------------------------------------------------------------------


def test_inl_spin_coating():
    entry_archive = parse('tests/data/schemas/spin_coating.archive.yaml')[0]
    normalize_all(entry_archive)
    data = entry_archive.data
    assert len(data.steps) == 1
    step = data.steps[0]
    assert step.speed.magnitude == pytest.approx(2000, rel=1e-3)
    assert step.duration.magnitude == pytest.approx(30, rel=1e-3)
