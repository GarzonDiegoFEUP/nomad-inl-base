# Install This Plugin

## Installing in a NOMAD Oasis

Add the plugin to your Oasis configuration. In your
`nomad.yaml` (or the equivalent config file for your Oasis deployment), add:

```yaml
plugins:
  include:
    - "schemas/nomad_inl_base"
  options:
    schemas/nomad_inl_base:
      python_package: nomad_inl_base
```

Then add the package to your Oasis `requirements.txt` (or `pyproject.toml`):

```
nomad-inl-base
```

or, to pin to the latest release from GitHub:

```
nomad-inl-base @ git+https://github.com/GarzonDiegoFEUP/nomad-inl-base.git
```

Restart your Oasis worker and app containers after making changes.

---

## Local development installation

This repository uses [uv](https://github.com/astral-sh/uv) for dependency
management and [poe](https://github.com/nat-n/poethepoet) for task running.

### 1. Clone the repository and install

```bash
git clone https://github.com/GarzonDiegoFEUP/nomad-inl-base.git
cd nomad-inl-base
uv sync
```

### 2. Start the NOMAD back-end

```bash
uv run poe start
```

### 3. Start the NOMAD GUI (in a separate terminal)

```bash
uv run poe gui start
```

The GUI is available at `http://localhost:3000` and the API at
`http://localhost:8000`.

### 4. Run the tests

```bash
uv run pytest tests/
```

---

## Dependencies

The plugin depends on:

| Package | Purpose |
|---------|--------|
| `nomad-lab` | Core NOMAD framework |
| `nomad-material-processing` | Base deposition and entity schemas |
| `nomad-measurements` | XRD and UV-Vis measurement parsers |
| `nomad-baseclasses` | Wet-chemical deposition property sections |
