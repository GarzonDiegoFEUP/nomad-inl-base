# Contribute to This Plugin

## Running the Tests

### Install dev dependencies

```bash
cd packages/nomad-inl-base
pip install -e ".[dev]"
```

Or, if the project uses [uv](https://github.com/astral-sh/uv):

```bash
cd packages/nomad-inl-base
uv sync --extra dev
```

### Run all tests

```bash
pytest tests/ -v
```

### Run specific subsets

| Goal | Command |
|------|---------|
| Pure utility tests (no NOMAD infra) | `pytest tests/test_utils.py -v` |
| Schema normalization tests | `pytest tests/schema_packages/ -v` |
| Parser integration tests | `pytest tests/parsers/ -v` |
| Discover all tests without running | `pytest --co -q` |

---

## Test Layout

```
tests/
├── conftest.py                    # Shared fixtures (caplog, parsed_archive, sem_zip)
├── test_utils.py                  # Pure unit tests – no NOMAD infrastructure needed
├── parsers/
│   ├── __init__.py
│   └── test_parser.py             # Integration tests for all parsers
├── schema_packages/
│   ├── __init__.py
│   └── test_schema_package.py     # Schema normalization tests
└── data/
    ├── test.archive.yaml          # Demo schema fixture
    ├── schemas/                   # Synthetic YAML archives for schema tests
    │   ├── substrate.archive.yaml
    │   ├── thinfilm.archive.yaml
    │   ├── cleaning.archive.yaml
    │   └── spin_coating.archive.yaml
    └── <parser data files>        # Real instrument output files
```

---

## Adding a New Parser Test

1. **Add a data file** – place the instrument output file in `tests/data/`.

2. **Write the test** using the `parsed_archive` and `caplog` fixtures:

    ```python
    @pytest.mark.parametrize(
        'parsed_archive, caplog',
        [('tests/data/my_file.txt', None)],
        indirect=True,
    )
    def test_my_parser(parsed_archive, caplog):
        entry = parsed_archive.data
        assert entry is not None
        assert entry.some_quantity == expected_value
    ```

    The `parsed_archive` fixture calls `nomad.client.parse()` and
    `nomad.client.normalize_all()` on the file, and yields the resulting
    archive. It cleans up the generated `.archive.json` after the test.

    The `caplog` fixture uses structlog `LogCapture` and fails the test if any
    `error` or `critical` level log entry is emitted.

3. **Remove the skip mark** (if the test was previously skipped due to missing
   data).

---

## Adding a New Schema Test

1. **Create a YAML archive** in `tests/data/schemas/` that instantiates your
   schema:

    ```yaml
    data:
      m_def: nomad_inl_base.schema_packages.my_module.MySchema
      my_quantity: some_value
    ```

2. **Write the test**:

    ```python
    @pytest.mark.parametrize(
        'parsed_archive, caplog',
        [('tests/data/schemas/my_schema.archive.yaml', None)],
        indirect=True,
    )
    def test_my_schema(parsed_archive, caplog):
        entry = parsed_archive.data
        assert entry.my_quantity == 'some_value'
    ```

---

## Currently Skipped Tests

Four parsers have no test data yet and are marked with `@pytest.mark.skip`:

| Test | Reason |
|------|--------|
| `test_cv_parser` | No CV data file available |
| `test_ed_parser` | No ED data file available |
| `test_emsa_edx_parser` | No EMSA/EDX data file available |
| `test_bruker_afm_parser` | No Bruker AFM binary file available |

To enable these tests, add the corresponding data file to `tests/data/` and
remove the `@pytest.mark.skip` decorator.


