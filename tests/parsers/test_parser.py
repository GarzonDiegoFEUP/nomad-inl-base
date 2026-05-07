import pytest
from nomad.client import normalize_all

# ---------------------------------------------------------------------------
# PC03 Cathode Chamber
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'parsed_archive, caplog',
    [(('tests/data/PC03_sample.CSV', []), ['error', 'critical'])],
    indirect=True,
    ids=['PC03_sample.CSV'],
)
def test_pc03_parse(parsed_archive, caplog):
    normalize_all(parsed_archive)
    assert parsed_archive.data is not None
    assert parsed_archive.data.timestamps is not None
    assert len(parsed_archive.data.timestamps) > 0
    assert parsed_archive.data.chamber_environment is not None
    assert parsed_archive.data.chamber_environment.pressure is not None
    assert parsed_archive.data.chamber_environment.pressure.value is not None
    assert len(parsed_archive.data.sources) == 4
    gas_flows = parsed_archive.data.chamber_environment.gas_flow
    assert len(gas_flows) > 0
    assert all(gf.name is not None for gf in gas_flows)


# ---------------------------------------------------------------------------
# PC04 Electrolyte Chamber
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'parsed_archive, caplog',
    [(('tests/data/PC04_sample.CSV', []), ['error', 'critical'])],
    indirect=True,
    ids=['PC04_sample.CSV'],
)
def test_pc04_parse(parsed_archive, caplog):
    normalize_all(parsed_archive)
    assert parsed_archive.data is not None
    assert parsed_archive.data.timestamps is not None
    assert len(parsed_archive.data.timestamps) > 0
    assert parsed_archive.data.chamber_environment is not None
    assert parsed_archive.data.chamber_environment.pressure is not None
    assert parsed_archive.data.chamber_environment.pressure.value is not None
    assert parsed_archive.data.dc_power_supply is not None


# ---------------------------------------------------------------------------
# Solar Cell IV — Results Table
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'parsed_archive, caplog',
    [(('tests/data/Sample_Results Table.txt', []), ['error', 'critical'])],
    indirect=True,
    ids=['Sample_Results_Table.txt'],
)
def test_solar_iv_results_table(parsed_archive, caplog):
    normalize_all(parsed_archive)
    assert parsed_archive.data is not None
    results = parsed_archive.data.results
    assert results is not None
    assert len(results) == 15
    r0 = results[0]
    assert r0.voc is not None
    assert 0.4 < r0.voc.magnitude < 0.7
    assert r0.efficiency is not None
    assert 0.0 < r0.efficiency < 100.0
    assert r0.fill_factor is not None
    assert 0.0 < r0.fill_factor < 100.0
    assert r0.jsc is not None
    assert r0.jsc.magnitude > 0


# ---------------------------------------------------------------------------
# Solar Cell IV — IV Graph curves
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'parsed_archive, caplog',
    [(('tests/data/Sample_IV Graph.txt', []), ['error', 'critical'])],
    indirect=True,
    ids=['Sample_IV_Graph.txt'],
)
def test_solar_iv_curves(parsed_archive, caplog):
    normalize_all(parsed_archive)
    assert parsed_archive.data is not None
    iv_curves = parsed_archive.data.iv_curves
    assert iv_curves is not None
    assert len(iv_curves) > 0
    curve = iv_curves[0]
    assert curve.voltage is not None
    assert len(curve.voltage) > 0
    assert curve.current is not None
    assert len(curve.current) > 0


# ---------------------------------------------------------------------------
# Four-Point Probe
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'parsed_archive, caplog',
    [(('tests/data/sample 4pp.xlsx', []), ['error', 'critical'])],
    indirect=True,
    ids=['sample_4pp.xlsx'],
)
def test_four_point_probe(parsed_archive, caplog):
    normalize_all(parsed_archive)
    assert parsed_archive.data is not None
    results = parsed_archive.data.results
    assert results is not None
    assert len(results) > 0
    r0 = results[0]
    assert r0.sheet_resistance_ave is not None
    assert r0.x_position is not None
    assert len(r0.x_position) > 0


# ---------------------------------------------------------------------------
# MPR — EIS Measurement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'parsed_archive, caplog',
    [(('tests/data/sample EIS.mpr', []), ['error', 'critical'])],
    indirect=True,
    ids=['sample_EIS.mpr'],
)
def test_mpr_eis(parsed_archive, caplog):
    normalize_all(parsed_archive)
    assert parsed_archive.data is not None
    assert parsed_archive.data.frequency is not None
    assert len(parsed_archive.data.frequency) > 0
    assert parsed_archive.data.real_impedance is not None
    assert len(parsed_archive.data.real_impedance) == len(parsed_archive.data.frequency)
    assert parsed_archive.data.imaginary_impedance is not None
    assert len(parsed_archive.data.imaginary_impedance) == len(
        parsed_archive.data.frequency
    )


# ---------------------------------------------------------------------------
# SEM Zip
# ---------------------------------------------------------------------------


def test_sem_zip(sem_zip, caplog):
    from nomad.client import normalize_all, parse

    archives = parse(sem_zip)
    assert archives, f'No archives parsed from {sem_zip}'
    entry_archive = archives[0]

    normalize_all(entry_archive)
    assert entry_archive.data is not None
    images = entry_archive.data.images
    assert images is not None
    assert len(images) > 0
    img = images[0]
    assert img.magnification is not None
    assert entry_archive.data.microscope_model is not None
    assert img.image_array is not None


# ---------------------------------------------------------------------------
# EQE
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'parsed_archive, caplog',
    [(('tests/data/sample EQE.txt', []), ['error', 'critical'])],
    indirect=True,
    ids=['sample_EQE.txt'],
)
def test_eqe(parsed_archive, caplog):
    normalize_all(parsed_archive)
    assert parsed_archive.data is not None
    assert parsed_archive.data.wavelength is not None
    assert parsed_archive.data.quantum_efficiency is not None
    assert len(parsed_archive.data.wavelength) == len(
        parsed_archive.data.quantum_efficiency
    )
    results = parsed_archive.data.results
    assert results is not None and len(results) > 0
    r0 = results[0]
    assert r0.jsc is not None
    assert r0.jsc.magnitude == pytest.approx(32.40, rel=1e-2)
    assert r0.bandgap is not None
    assert r0.bandgap.magnitude == pytest.approx(1.152, rel=1e-2)
    assert r0.device_id is not None


# ---------------------------------------------------------------------------
# GDOES
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'parsed_archive, caplog',
    [(('tests/data/sample gdoes.txt', []), ['error', 'critical'])],
    indirect=True,
    ids=['sample_gdoes.txt'],
)
def test_gdoes(parsed_archive, caplog):
    normalize_all(parsed_archive)
    assert parsed_archive.data is not None
    assert parsed_archive.data.depth is not None
    assert len(parsed_archive.data.depth) > 0
    profiles = parsed_archive.data.element_profiles
    assert profiles is not None and len(profiles) > 0
    element_names = {p.element_name for p in profiles}
    assert 'Se' in element_names
    assert 'Sb' in element_names
    assert 'Mo' in element_names
    # Derived ratio columns (containing '*' or '/') must not appear
    for name in element_names:
        assert '*' not in name
        assert '/' not in name


# ---------------------------------------------------------------------------
# KLA-Tencor Profiler
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'parsed_archive, caplog',
    [(('tests/data/sample profile.pdf', []), ['error', 'critical'])],
    indirect=True,
    ids=['sample_profile.pdf'],
)
def test_kla_profiler(parsed_archive, caplog):
    normalize_all(parsed_archive)
    assert parsed_archive.data is not None
    assert parsed_archive.data.recipe is not None
    results = parsed_archive.data.results
    assert results is not None and len(results) > 0
    r0 = results[0]
    assert r0.Ra is not None
    assert r0.Ra.magnitude > 0  # converted from Å → m
    assert r0.step_height is not None


# ---------------------------------------------------------------------------
# Skipped parsers (no test data available)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason='No test data available for CVParser')
def test_cv_parser():
    pass


@pytest.mark.skip(reason='No test data available for EDParser')
def test_ed_parser():
    pass


@pytest.mark.skip(reason='No test data available for EMSAEDXParser')
def test_emsa_edx_parser():
    pass


@pytest.mark.skip(reason='No test data available for BrukerAFMParser')
def test_bruker_afm_parser():
    pass
