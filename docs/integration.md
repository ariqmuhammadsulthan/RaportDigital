# Adapt or integrate

**English** | [Bahasa Indonesia](integration.id.md)

[← README](../README.md) · [Operations](operations.md)

The included backend is Python/Flask. Other stacks can run it as a separate service
behind their reverse proxy, or implement the small HTTP contract below. It is not
a drop-in library for every framework. Use one origin for the editor and API;
cross-origin cookies/CORS and SSO require a deliberate authentication design.

## Code map

| File | Owns |
|---|---|
| `raportdigital/web.py` | App factory, accounts, sessions, encrypted records, HTTP routes |
| `raportdigital/domain.py` | Stable program IDs, classes, validation and year-end rules |
| `raportdigital/programs.py` | School/equivalency presets, custom names and archive labels |
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
`reportVersion` and legacy-profile branches when preserving old issued-report rendering.

## Choose programs

Set these before starting the service, then restart it and reload open book pages:

| Setting | Default | Purpose |
|---|---|---|
| `RAPOR_EDUCATION` | `school` | `school` for SD/SMP/SMA; `equivalency` for Paket A/B/C |
| `RAPOR_PROGRAM_NAMES` | Unset | Path to a UTF-8 JSON file overriding menu and cover names |

For equivalency education, in Windows CMD:

```bat
set "RAPOR_EDUCATION=equivalency"
.venv\Scripts\raportdigital serve --local
```

On macOS/Linux, use `export RAPOR_EDUCATION=equivalency` before starting the service.
Containers accept the same setting with `-e RAPOR_EDUCATION=equivalency`.

For custom labels, create a file such as `C:\RaporConfig\programs.json`:

```json
{"a": "MI", "b": "MTs", "c-ipa": "MA IPA", "c-ips": "MA IPS"}
```

Then set `RAPOR_PROGRAM_NAMES` to that file's path. Omitted names use the preset.
Names are plain text, up to 120 characters. Only the server operator changes this
configuration; teachers still edit school identity and subjects in **Pengaturan**.
An embedded app can use `create_app(education="school", program_names={"a": "MI"})`.

| Stable ID | School | Equivalency | Classes |
|---|---|---|---|
| `a` | SD | Paket A | I–VI |
| `b` | SMP | Paket B | VII–IX |
| `c-ipa` | SMA IPA | Paket C IPA | X–XII |
| `c-ips` | SMA IPS | Paket C IPS | X–XII |

Both presets support the same entry, printing, archive and year-end workflows.
The equivalency preset includes Tingkatan, MIA/IIS class suffixes and empowerment/
skills examples. The school preset uses general report labels and separate arts
and physical-education examples. Subjects remain editable; neither preset claims
to define an official curriculum. Different class ranges or grading systems need
code changes, not just a new name.

Switching presets changes active book labels, but leaves saved subjects, pupils
and marks intact. New books receive the selected defaults. Issued archives retain
their publication labels; older archives retain their original equivalency format.
Reissuing the same book revision returns the existing archive. Save a revised book
before publishing a replacement.

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

The editor shell supplies `data-program`, `data-profile`, `data-year`, `data-issue`, `data-csrf`,
`data-endpoint` and `data-login` on its body. If replacing the backend, render these
values safely and retain the DOM IDs used by both scripts.
`data-profile` is HTML-escaped JSON with `name`, `cover`, `track` and `equivalency`.
For archives it comes from the encrypted snapshot's `reportProfile`, with a legacy
equivalency fallback when absent. The server stamps this field when issuing and
discards browser-supplied `reportProfile` on saves.

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

## Updating documentation

Update English and Indonesian pairs together: `name.md` and `name.id.md`. Keep
commands and API examples identical, and link to guides in the reader's language.
