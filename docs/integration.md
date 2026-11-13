# Adapt or integrate

[← README](../README.md) · [Operations](operations.md)

The included backend is Python/Flask. Other stacks can run it as a separate service
behind their reverse proxy, or implement the small HTTP contract below. It is not
a drop-in library for every framework. Use one origin for the editor and API;
cross-origin cookies/CORS and SSO require a deliberate authentication design.

## Code map

| File | Owns |
|---|---|
| `raportdigital/web.py` | App factory, accounts, sessions, encrypted records, HTTP routes |
| `raportdigital/domain.py` | Programs, classes, validation and year-end rules |
| `raportdigital/schema.sql` | SQLite tables and issued-record guards |
| `raportdigital/cli.py` | Setup/check commands and local/proxy launch modes |
| `raportdigital/static/report.js` | Initial book, input tables, spreadsheet paste and report rendering |
| `raportdigital/static/workbook.js` | Loading, autosave, revision checks, issuing and navigation |
| `raportdigital/templates/` | Login, book list, editor shell and generated URLs |
| `raportdigital/static/*.css` | App UI and A4 print layout |

Change school identity and subjects through **Pengaturan** first. For new-book
defaults, edit `def`, `mkc` and `mkms` in `report.js`. Changes do not rewrite saved
books. If changing program/class IDs or saved fields, update both browser defaults
and server validation, and provide a migration for existing data. Keep the
`reportVersion` branch when preserving old issued-report rendering.

## Run alongside another application

The WSGI factory is `raportdigital:create_app()`. It defaults to requiring HTTPS.
`app.py` remains a compatibility entry point for existing Flask commands.

The supplied launcher supports a prefix:

```sh
raportdigital serve --local --prefix /grades
```

Open `http://127.0.0.1:8765/grades/`. For hosted use, follow the proxy setup in
[operations](operations.md#hosting). A custom WSGI mount must set `SCRIPT_NAME` and
strip that prefix from `PATH_INFO`. Links, API URLs, redirects and cookie paths
follow the mount. The application does not trust forwarded headers by itself.

The editor shell supplies `data-program`, `data-year`, `data-issue`, `data-csrf`,
`data-endpoint` and `data-login` on its body. If replacing the backend, render these
values safely and retain the DOM IDs used by both scripts.

## HTTP contract

All record endpoints require the teacher's session. Every POST requires a matching
`Origin`; authenticated POSTs also require `X-CSRF-Token` (or a form `csrf` field).
Use JSON for record requests. Ownership always comes from the authenticated
session, never an owner ID supplied by the browser.

| Endpoint | Request / result |
|---|---|
| `POST /login` | Form `name`, `password`; establishes an HttpOnly, SameSite=Strict cookie |
| `POST /logout` | Revokes the current server session |
| `GET /api/book/{program}/{year}` | `{rev, state}`; new books return `rev: 0, state: null` |
| `POST /api/book/{program}/{year}` | `{rev, state}` atomically saves the next revision; returns `{rev}` |
| Same endpoint, `action: "history"` | `{rev, action}` returns `{versions: [...]}`, newest first |
| Same endpoint, `action: "restore"` | `{rev, action, version}` restores an earlier book as a new revision |
| Same endpoint, `action: "issue"` | `{rev, action}` archives the selected class/semester; returns `{url}` |
| Same endpoint, `action: "rollover"` | `{rev, action}` creates the following year's book; returns `{url}` |
| `GET /api/issued/{id}` | `{rev, state}` for an owned, fixed archive; no write endpoint |

`state` contains `sch` (school and selected class/semester), `logo` (PNG data URL),
`c` (class records), and optional `rows`. Each class holds `st` (pupils), `ms`
(Ganjil/Genap settings), `wali`, `nip`, `naik` and `tahun`. Settings contain subject
groups `u`, `p`, `k`, extracurriculars `e`, report date `tgl`, and threshold `batas`.
Pupil `n` maps semesters to string-valued marks such as `u0`, `p0`, `k0`, `e0`,
`izin`, `sakit`, `alpa`, and `catatan`. `domain.validate()` defines allowed fields
and limits; `test_app.py` contains a minimal synthetic book.

Keep revision comparisons and writes in one transaction. Return **409** on stale
revisions, **401/403** on failed authentication/security checks, **404** for unknown
or unowned records, **413** above 4 MB, and **422** for invalid state. API failures
return an `error` message; ordinary HTTP failures also include numeric `code`.
Never return decrypted records after an integrity failure. Porting the UI alone
does not carry over these server-side protections.
