# Reference – Analysis

This page documents the Jupyter notebook–based analysis ELN entries provided
by the [`nomad-analysis`](https://github.com/FAIRmat-NFDI/nomad-analysis)
plugin and extended here with INL-specific pre-defined notebook cells. These
entries live under the **Analysis using Jupyter notebooks** category.

| Schema | Label | `method` | Typical input entries |
|--------|-------|----------|------------------------|
| `EQEJupyterAnalysis` | EQE Jupyter Analysis | `EQE` | `INLEQE` |
| `SolarCellJupyterAnalysis` | Solar Cell IV Jupyter Analysis | `SolarCellIV` | `INLSolarCellIV` |
| `GDOESJupyterAnalysis` | GDOES Jupyter Analysis | `GDOES` | `INLGDOES` |
| `INLXRDJupyterAnalysis` | INL XRD Jupyter Analysis | `XRD` | `INLXRayDiffraction` |

All four schemas are defined in
[`nomad_inl_base.analysis.schema`](https://github.com/GarzonDiegoFEUP/nomad-inl-base/blob/main/src/nomad_inl_base/analysis/schema.py)
and are subclasses of `nomad_analysis.jupyter.schema.JupyterAnalysis`. The
underlying analysis functions live in
[`nomad_inl_base.analysis.analysis_source`](https://github.com/GarzonDiegoFEUP/nomad-inl-base/blob/main/src/nomad_inl_base/analysis/analysis_source.py).

---

## Common fields (inherited from `JupyterAnalysis`)

| Quantity / Action | Type | Description |
|--------------------|------|-------------|
| `query_for_inputs` | Query (repeats) | Search query used to find candidate input entries (e.g. all `INLEQE` entries for a given sample). |
| `trigger_reset_inputs` | Action | Clears `inputs` and re-populates it from `query_for_inputs`. |
| `inputs` | `SectionReference` (repeats) | The resolved list of referenced entries the notebook will analyze. Accessible in the notebook as `analysis.inputs`. |
| `trigger_generate_notebook` | Action | Generates the `.ipynb` file (see [How it works](#how-it-works)) and links it in `notebook`. Does nothing if `notebook` is already set. |
| `notebook` | File | The generated/uploaded Jupyter notebook, connected to the ELN entry. |
| `template` | Reference | Optional `JupyterAnalysisTemplate` entry to seed the notebook from a custom template instead of the default cells. |
| `method` | `str` | Set automatically by each subclass (`EQE`, `SolarCellIV`, `GDOES`, `XRD`). |

## How it works

1. Set **Search queries for inputs** (`query_for_inputs`) to match the
   measurement entries you want to analyze (e.g. by sample or upload).
2. Click **Reset Inputs** (`trigger_reset_inputs`). This populates `inputs`
   with references to the matched entries.
3. Click **Generate Notebook** (`trigger_generate_notebook`). This creates a
   `.ipynb` file with:
      - A header cell that loads the linked entry into a Python variable
        named `analysis` (via `nomad_analysis.utils.get_entry_data`).
      - A pre-defined code cell injecting the schema-specific analysis
        functions (`eqe_analysis`, `solar_cell_iv_analysis`, `gdoes_analysis`,
        or `xrd_voila_analysis` — see below).
      - A call to that function with `analysis.inputs` as the argument.
4. Open **Notebook** and run the cells. The analysis inputs (as resolved
   `SectionReference` objects) are available as `analysis.inputs`; each
   reference's target entry is `entry_input.reference`.

!!! note "Local fixes on top of `nomad-analysis`"
    The notebook generation in this plugin patches a few issues found in the
    upstream `nomad-analysis` v0.2.3 templates:

    - The header cell's `get_entry_data(..., url=NOMAD_ANALYSIS_BASE_URL)`
      call has its `url` argument commented out after generation, since it is
      not needed and can prevent the API call from succeeding (e.g. inside a
      JupyterHub container). `get_entry_data` falls back to the local NOMAD
      client URL.
    - The pre-defined analysis calls use `analysis.inputs` (not
      `analysis.data.inputs`, which does not exist).
    - `INLXRDJupyterAnalysis` uses a locally patched copy of
      `xrd_voila_analysis` where `get_input_entry_names` accesses
      `entry_input.reference.name` **before** the `isinstance` check. This
      forces resolution of the lazy reference proxy returned by the search
      API; without it, `isinstance(entry_input.reference, ELNXRayDiffraction)`
      can spuriously return `False` and no input entries show up in the
      notebook's dropdown.

---

## EQEJupyterAnalysis

**Base class:** `JupyterAnalysis`, `EntryData`
**Label:** `EQE Jupyter Analysis`

Generates a notebook that calls `eqe_analysis(analysis.inputs)`. For each
input `INLEQE` entry it:

- Calculates the short-circuit current density (Jsc) against the AM1.5G
  reference spectrum.
- Fits the bandgap using a sigmoid fit and the Keller (linear extrapolation)
  method.
- Plots the EQE spectrum (with a secondary energy axis) and prints a summary
  table across all input entries.

## SolarCellJupyterAnalysis

**Base class:** `JupyterAnalysis`, `EntryData`
**Label:** `Solar Cell IV Jupyter Analysis`

Generates a notebook that calls `solar_cell_iv_analysis(analysis.inputs)`.
For each input `INLSolarCellIV` entry it plots all JV curves, collects
Voc/Jsc/fill factor/efficiency into a summary table, and shows box plots of
the parameter distributions across all input entries.

## GDOESJupyterAnalysis

**Base class:** `JupyterAnalysis`, `EntryData`
**Label:** `GDOES Jupyter Analysis`

Generates a notebook that calls `gdoes_analysis(analysis.inputs)`. For each
input `INLGDOES` entry it plots the per-element depth profile and computes
FWHM-based layer thickness estimates for each element.

## INLXRDJupyterAnalysis

**Base class:** `JupyterAnalysis`, `EntryData`
**Label:** `INL XRD Jupyter Analysis`

Generates a notebook that calls `xrd_voila_analysis(analysis.inputs)`, an
interactive `ipywidgets`/Voila panel for XRD peak finding. It lets you:

- Select one of the input `INLXRayDiffraction` entries from a dropdown.
- Adjust peak-finding parameters (height, threshold, distance) used by
  `scipy.signal.find_peaks`.
- View the intensity vs. 2θ plot (log scale) with detected peaks marked.
- Export the peak table as JSON or CSV.
