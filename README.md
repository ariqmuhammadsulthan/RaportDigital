# Rapor Digital

**English** | [Bahasa Indonesia](README.id.md)

A standalone gradebook starter for Indonesian educational institutions. Teachers
enter or paste marks, review each class, and print A4
reports. The reference app uses Flask, SQLite and plain JavaScript; no frontend
build, CDN or external account is required.
The app interface is in Indonesian.

Use it locally, host it as a service alongside your stack, or adapt the editor to
your own backend. It is a starting point you maintain, not a hosted service or a
promise of ongoing updates. Review the subject defaults and report format before
using real pupil records.

Start with **SD, SMP, SMA IPA and SMA IPS**, switch to **Paket A/B/C**, or use your
own program names. [Program setup](docs/integration.md#choose-programs) changes the
menus and reports without changing book IDs or moving saved marks.

## Start locally

Python 3.11 or newer. Download or clone this repository, open its folder, then:

**Windows — Command Prompt (CMD)**

```bat
python -m venv .venv
.venv\Scripts\python -m pip install -e .
.venv\Scripts\raportdigital init
.venv\Scripts\raportdigital teacher
.venv\Scripts\raportdigital serve --local
```

**macOS / Linux**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/raportdigital init
.venv/bin/raportdigital teacher
.venv/bin/raportdigital serve --local
```

Open [127.0.0.1:8765](http://127.0.0.1:8765). Create your own account when prompted;
there is no default password. Data and its encryption key live outside the code,
in `~/.raportdigital`. Stop with Ctrl+C.

## Choose a guide

| Task | Guide |
|---|---|
| Fill marks and print reports | [Teacher guide](docs/using.md) |
| Adapt the code or connect another backend | [Integration](docs/integration.md) |
| Host, back up, test or upgrade | [Operations](docs/operations.md) |
| Understand reuse and provenance | [License scope](docs/origins.md) |
| See the template changes | [Changelog](CHANGELOG.md) |

The app includes separate teacher accounts, automatic saving, five earlier book
revisions, fixed issued archives and year-end roster preparation. Spreadsheet
support is copy/paste from Excel; it does not upload `.xlsx` files. SSO, centrally
shared classes and digitally signed PDFs are not included.

The original app expansion and template contributions are [MIT licensed](LICENSE).
Inherited report-editor/layout material comes from an upstream project without a
declared license; [the provenance note](docs/origins.md) explains that boundary.
