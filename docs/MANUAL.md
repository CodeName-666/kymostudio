# KymoStudio – Manual

[← Back to overview](../README.md) · **English** · [Deutsch](MANUAL.de.md)

Installation, operation, limits, configuration and checks in detail.

## Getting started on Windows

A separate installation with **Python 3.12** is recommended. Do not copy the
project blindly into an existing installation; test it in a new folder first.
In the unpacked project folder, in PowerShell or CMD:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe run.py --demo
```

Afterwards `start_windows.bat` launches the application, or:

```powershell
.venv\Scripts\python.exe run.py
```

The three demo signals need no connected hardware. Real connections are not
started automatically. Their settings are managed in the **Connections**
dialog; the interface distinguishes between "connected" and "connecting".

## Getting started on Linux/macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py --demo
```

Normal operation requires a desktop/graphics environment. Device permissions
and CAN drivers depend on the operating system and adapter. The original
connection type is called "Telnet", but it uses the existing TCP data stream;
no Telnet terminal emulation has been added.

## How you work with it

| Area | Operation |
|---|---|
| Workspace | Charts at the centre; floating, tiled or focused one at a time. |
| Sidebar | **Charts**, **Signals**, **Analysis** instead of one overloaded view. Adjustable width, can be hidden. |
| Signals | Search field; select a signal and assign it to one or more charts. Y(t) and X(t) are separate. |
| Charts | Time series, XY line, XY scatter and the existing XYZ scatter. Show/hide curves; change names and colours. |
| 2D navigation | Mouse wheel to zoom, drag to pan, double click to fit; optional coordinate crosshair. |
| Axes | Chart options for manual X/Y limits and time windows. Constant signals get a visible value range. |
| Settings | Grid, legend, antialiasing, crosshair, refresh interval, curve point limit and optional decimation. |
| Analysis | Count, minimum, maximum, mean, root mean square (RMS), standard deviation and latest **Y value** from the stored raw-data window. |
| Export | A single signal or the entire raw buffer as CSV; the visible chart workspace as PNG; the configuration as JSON. |

**Pausing the display does not stop acquisition.** Buffers remain bounded;
during a long pause older display and raw values may be lost. The status bar
shows the corresponding counters. To really stop recording, stop the
connection.

### Keyboard

| Shortcut | Action |
|---|---|
| Ctrl+N | Create chart |
| Ctrl+E | Export raw data as CSV |
| Ctrl+Space | Pause/resume display |
| Ctrl+B | Show/hide sidebar |
| Ctrl+, | Display settings |
| Ctrl+S | Save workspace |
| Ctrl+0 | Fit data in all charts |

## Data integrity and limits

Raw data is stored **before display decimation**. Statistics and CSV use this
store, not the possibly reduced curves. Missing X or Z coordinates stay empty
in the CSV; reception time is not a measured X value. The CSV export is UTF-8
with BOM, comma as field separator and dot as decimal separator. In
spreadsheet programs, use the CSV import with these settings if necessary.

| Limit | Value / meaning |
|---|---|
| Signal IDs in the data packet | Real integers from 0 to 255; no booleans. |
| Input packet | At most 64 KiB; invalid and non-finite values are rejected. |
| Input queue | At most 2,048 packets / 4 MiB per connection; older packets are removed on overload. |
| Raw data | At most 20,000 values per signal and 250,000 in total. |
| Display staging buffer | At most 4,096 points per signal and dimension. Further bounded buffers exist in QML. |
| 2D curves | Adjustable from 500 to 50,000 points, default 10,000. |
| Sources / signals / windows | At most 128 stored connections, 256 signals, 16 charts; 64 curves per chart. |
| 3D | Existing Quick3D renderer with at most 5,000 point objects per series; no newly implemented instanced GPU renderer. |

The refresh interval is a **target rate, not a guaranteed frame rate**. Very
many curves, 3D points, sources or high data rates can still cause high load.
This release is **not a lossless long-term recorder**. The CSV export contains
only the measurements still stored when the export starts. Counters for
raw-data replacement, invalid packets and overload are shown separately. When
a connection is stopped, the interface may wait up to 1.5 seconds for a
worker; with several problematic connections this time can add up.

## Configuration and migration

`config/config.json` is the bundled **template**, no longer the normal
location for running user settings. Default locations:

- Windows: `%APPDATA%\KymoStudio\config.json`
- Linux: `${XDG_CONFIG_HOME:-~/.config}/KymoStudio/config.json`
- macOS: `~/Library/Application Support/KymoStudio/config.json`

An existing `PlotterApp` directory from before the rename is moved to
`KymoStudio` once on first start.

`KYMO_CONFIG_HOME` overrides the user data directory; the old name
`PLOTTER_CONFIG_HOME` is still read. `python run.py --config PATH/config.json`
selects an explicit writable configuration. An existing file is validated
before use. Geometry and simple display preferences are additionally stored in
Qt `Settings`.

Back up an existing JSON configuration first, then import it in the new
interface. A successful import stops existing connections, clears raw data and
replaces connection definitions as well as the workspace. Imported connections
remain stopped. If a write error occurs after stopping, the old connections may
already be halted; they are not silently restarted.

Chart definitions, assignments, names, colours, visibility and 2D axis states
are saved. **Measurements are not saved in the workspace.** The "display
paused" setting and 3D camera positions are not saved as a complete session.

JSON may contain MQTT credentials in plain text. Do not publish configurations
and logs without checking them. No operating-system keychain has been added.
The log rotates in the user data directory under `logs/kymostudio.log`.

## Checks on the target machine

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe run.py --smoke-test
```

The smoke test uses a temporary profile, opens the QML application, starts the
demo and checks data reception as well as detected QML errors. It does not
replace a visual acceptance check. On Windows, then start `--demo` normally and
work through the
[acceptance checklist](TESTBERICHT.md#manuelle-abnahme-auf-dem-zielrechner) (German).

Additional checks (Node.js only for development tests, not needed by the app):

```bash
node tests/js/chart_math.test.cjs
node tools/check_qml_scripts.cjs
python tools/check_backend_contracts.py
python tools/benchmark_core.py
```

The GitHub Actions workflow runs tests, script and contract checks on every
push. Three tests read the firmware sources from a neighbouring
[KymoProbe](https://github.com/CodeName-666/kymoprobe) checkout; without it they
are skipped with a clear message.

## Project documents

[Changelog](../CHANGELOG.md) · [Architecture](ARCHITEKTUR.md) (German) ·
[Test report](TESTBERICHT.md) (German) · [open acceptance items](TESTBERICHT.md#manuelle-abnahme-auf-dem-zielrechner)

Historical planning/phase documents are in `docs/legacy/` and are not current
release evidence. Old QML components no longer used by the main view remain in
the source tree for compatibility.

The README screenshots are generated by `tools/capture_screenshots.py` with
demo data and a temporary profile; the logo set is generated by
`tools/build_brand.py`.
