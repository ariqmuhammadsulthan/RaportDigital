# Changelog

## 1.0.0 — Standalone template · 2026-11-13

- Installable Python package with included assets, templates and SQL schema;
  `raportdigital init`, `teacher`, `check` and `serve` commands.
- Separated web/storage handling from gradebook rules. The old `app.py` entry
  point and existing encrypted data formats remain compatible.
- Generated URLs and cookie paths support mounting under a prefix. Hosted startup
  requires a trusted proxy and hostname; local startup stays on loopback.
- Clear setup/storage errors, JSON API failures and guarded key handling.
  Invalid encrypted records are refused without showing cryptographic diagnostics.
- Non-root Docker image, small CI workflow and a real-browser fixture harness.
- Short quickstart, separate teacher/integration/operations guides, MIT licensing
  for original contributions and explicit upstream provenance.
- Corrected report-label typos and clarified autosave, issuing and restoration.

The app still includes automatic saves, five earlier revisions, fixed class
archives, spreadsheet paste checks and confirmed year-end progression. It has no
external service dependency or scheduled upstream synchronization.

Checks: 12 backend tests on Windows/Linux, Firefox and Chrome workflows, a clean
wheel install, and non-root Docker setup/HTTPS-proxy checks. Browser tests use
fictional records on loopback; they do not establish a production deployment.
The included commands are in [operations](docs/operations.md#test-and-update) and
[browser checks](tools/README.md).
