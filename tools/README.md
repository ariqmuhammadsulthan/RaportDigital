# Browser checks

**English** | [Bahasa Indonesia](README.id.md)

[← README](../README.md) · [Operations](../docs/operations.md)

Install Playwright and its browsers in a disposable directory outside this
repository, or use an existing installation. No browser tooling ships in the app.
From the repository root, in CMD:

```bat
set "PYTHON_BIN=%CD%\.venv\Scripts\python.exe"
set "RAPOR_PLAYWRIGHT=C:\path\to\node_modules\playwright"
set "RAPOR_EDUCATION=school"
set "RAPOR_BROWSER=firefox"
node tools\browser_check.cjs
set "RAPOR_EDUCATION=equivalency"
node tools\browser_check.cjs
set "RAPOR_EDUCATION=school"
set "RAPOR_BROWSER=chromium"
node tools\browser_check.cjs
set "RAPOR_EDUCATION=equivalency"
node tools\browser_check.cjs
set "RAPOR_EDUCATION="
```

`RAPOR_CHROMIUM` can point to an installed Chrome executable. Set
`PLAYWRIGHT_BROWSERS_PATH` if your browser download directory is nonstandard.

The harness starts a real app on an ephemeral loopback port under `/grades`, with
a temporary SQLite database and generated fixture password. It exercises login,
all program names/covers/defaults, Excel paste, saving/reload, mobile preview, issuing, print
media and logout. It closes the browser/server and deletes its own temporary data.
It does not use real teacher records, production or an external login provider.
Run each browser with both `school` (default) and `equivalency`. An optional
`RAPOR_PROGRAM_NAMES` file also checks custom labels and their safe rendering.
