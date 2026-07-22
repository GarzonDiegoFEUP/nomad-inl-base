# Reference – Testo Environmental Logger

This page documents the ELN entry types and parser used to record
temperature/humidity data from Testo 175H1 (and compatible) environmental
data loggers deployed around the lab.

---

## INLTestoLogger

**Category:** INL Entities  
**Base class:** `INLInstrument`, `PlotSection`  
**Label:** *INL Testo Logger*

Represents a Testo logger device at a fixed lab location. Each uploaded
`.vi2` export creates one entry of this type holding the records read from
that particular file (`measurement_records`). The physical device/location is
identified via the inherited `lab_id` field (e.g. `B.P0.Lg.06` or
`C.P0.Tl.01`).

On processing, the entry also looks up every other `INLTestoLogger` entry
that shares the same `lab_id` (across uploads) to build a deduplicated,
chronologically sorted temperature/humidity trend covering the full
measurement history recorded for that device, and shows it as two plots
(temperature and humidity vs. time) on the entry.

### Quantities

| Quantity | Type | Description |
|----------|------|-------------|
| `serial_number` | `str` | Serial number of the Testo logger device |
| `source_lab_name` | `str` | Raw lab-name string extracted from the uploaded `.vi2` file, before mapping to a `lab_id`/device location |

### Sub-sections

| Sub-section | Type | Description |
|-------------|------|-------------|
| `measurement_records` | `INLTestoMeasurementRecord` (repeats) | Temperature/humidity records parsed from this uploaded `.vi2` file |

### Trend merge and deduplication

`_collect_history` gathers records from the current entry plus every other
`INLTestoLogger` entry found via a `results.eln.lab_ids` search for the same
`lab_id`, then merges them into a single timestamp → (temperature, humidity)
mapping:

1. Records are grouped by their source entry's upload creation time, oldest
   upload first.
2. Records are merged by exact timestamp. If two entries report a record for
   the same timestamp, the value from the earliest-uploaded entry is kept
   (earliest upload wins) — this guarantees exactly one measurement per time
   point in the combined trend, with no duplicates.
3. The merged, deduplicated series is sorted chronologically and plotted.

This cross-entry lookup is skipped when running in a `ClientContext` (e.g.
the standalone `nomad-parse`/`nomad.client` CLI), since it requires the
server-side search index; only the current entry's own records are plotted
in that case.

### Plots

Two `PlotlyFigure`s are generated on every normalization:

- **Temperature Trend** — temperature (°C) vs. time.
- **Humidity Trend** — relative humidity (%) vs. time.

Both are titled with the device's `lab_id` when available.

---

## INLTestoMeasurementRecord

**Base class:** `ArchiveSection`  
**Label:** *Measurement Record*

A single temperature/humidity reading.

| Quantity | Type | Unit | Description |
|----------|------|------|-------------|
| `timestamp` | `Datetime` | – | Timestamp of the measurement, reconstructed from the logger ticker |
| `temperature` | `float` | K (displayed as °C) | Measured air temperature |
| `humidity` | `float` | – | Measured relative humidity (%RH) |

---

## INLTestoLoggerReference

**Base class:** `INLInstrumentReference`

A reference to an `INLTestoLogger` entry, for use from other schemas.

---

## .vi2 file format and parser

Testo `.vi2` files are OLE compound documents (the same container format
used by legacy `.doc`/`.xls` files). `TestoVI2Parser` is registered for any
mainfile matching `*.vi2` (case-insensitive).

### Streams read

| Internal stream (suffix match) | Contents |
|---------------------------------|----------|
| `summary` | Total record count and sample interval (ms) |
| `data/values` | Binary array of `(ticker, humidity, temperature)` records |
| `t17c` | Tab-separated key/value metadata, including `SerialNumber` and `ProgTime` (log start epoch) |
| `\x05SummaryInformation` | OLE summary info; the first plausible ASCII string (excluding stream names and serial-number-like tokens) is taken as the raw lab name |

Stream paths are located dynamically (`_find_ole_stream_path`) since the
logger's internal folder ID varies between files.

### Record reconstruction

1. Each binary record is unpacked as `ticker` (`u4`), `humidity` (`f4`),
   `temperature` (`f4`).
2. The start timestamp is computed from `ProgTime` (epoch seconds) plus the
   first record's `ticker` divided by a fixed logger clock-rate constant
   (`9.63857262`).
3. Subsequent timestamps are spaced using the summary's sample interval.
4. Temperature is stored in Kelvin (`°C + 273.15`); humidity is stored
   unitless as %RH.

If the essential `summary` or `data/values` streams are missing, or no
records are read, the file is logged as an error and skipped (no entry is
created). A mismatch between the summary's reported record count and the
number of records actually read is logged as a warning but does not stop
parsing.

### Lab name → device routing

The raw lab name extracted from the file is normalized (whitespace
collapsed, upper-cased) and looked up in a fixed alias table:

| Normalized lab name | Routed `lab_id` |
|----------------------|------------------|
| `STAR LAB`, `STARLAB` | `B.P0.Lg.06` |
| `SUPPORT`, `SUPPORT LAB` | `C.P0.Tl.01` |

If the lab name doesn't match any alias, a warning is logged and the entry
is created without a `lab_id` (so it won't be merged into any device's
trend until corrected manually).

### Output

The parser creates one `INLTestoLogger` child entry per uploaded `.vi2`
file (`<file>.TestoLogger.archive.yaml`), populated with `serial_number`,
`source_lab_name`, the routed `lab_id` (if recognized), and one
`INLTestoMeasurementRecord` per row parsed from the file.
