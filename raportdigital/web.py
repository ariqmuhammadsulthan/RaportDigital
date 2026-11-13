import click
import hashlib
import json
import os
import re
import secrets
import sqlite3
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from flask import Flask, abort, g, redirect, render_template, request, url_for
from werkzeug.exceptions import HTTPException, InternalServerError, SecurityError, ServiceUnavailable
from werkzeug.security import check_password_hash, generate_password_hash

from .domain import CLASSES, validate, prepare_next_year
from .programs import configured_profiles, issued_profile

SCHEMA = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")


def check_storage(root):
    """Fail without creating a database or replacing an existing key."""
    if not (root / "records.sqlite3").is_file() or not (root / "records.key").is_file():
        raise RuntimeError("Data belum siap. Jalankan 'raportdigital init'; untuk data lama, pulihkan basis data dan kunci aslinya.")
    if len((root / "records.key").read_bytes()) != 32:
        raise RuntimeError("Kunci penyimpanan tidak valid. Pulihkan kunci asli; jangan membuat kunci pengganti.")


def create_app(directory=None, local=False, *, education=None, program_names=None):
    app = Flask(__name__)
    programs = configured_profiles(education, program_names)
    root = Path(directory or os.environ.get("RAPOR_DATA_DIR") or Path.home() / ".raportdigital").expanduser().resolve()
    code = Path(__file__).resolve().parent
    checkout = code.parent if (code.parent / "pyproject.toml").is_file() else code
    if root.is_relative_to(checkout):
        raise ValueError("Simpan basis data di luar repositori.")
    app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024
    app.config["RAPOR_DATA_DIR"] = root
    hosts = [host.strip() for host in os.environ.get("RAPOR_TRUSTED_HOSTS", "").split(",") if host.strip()]
    app.config["TRUSTED_HOSTS"] = hosts or None

    def db():
        if "db" not in g:
            # Requests must never create an empty database after a bad mount/path.
            g.db = sqlite3.connect((root / "records.sqlite3").as_uri() + "?mode=rw", uri=True, timeout=8)
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close(_):
        if "db" in g:
            g.db.close()

    @app.cli.command("init")
    def initialize():
        """Create storage, or apply the additive schema to existing storage."""
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = root / "records.key"
        if not path.exists():
            if (root / "records.sqlite3").exists():
                raise click.ClickException("Pulihkan kunci asli sebelum melanjutkan.")
            with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as key:
                key.write(AESGCM.generate_key(bit_length=256))
        if len(path.read_bytes()) != 32:
            raise click.ClickException("Kunci penyimpanan tidak valid. Pulihkan kunci asli.")
        database = root / "records.sqlite3"
        # Exclusive creation establishes private permissions before SQLite writes.
        if not database.exists():
            os.close(os.open(database, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
        db().executescript(SCHEMA)
        click.echo("Penyimpanan siap. Jalankan 'raportdigital teacher' untuk membuat akun.")

    @app.cli.command("check")
    def check():
        """Check storage and schema without printing credentials or pupil data."""
        try:
            check_storage(root)
            tables = {row[0] for row in db().execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {"users", "sessions", "attempts", "books", "issues", "drafts"} <= tables:
                raise RuntimeError("Skema belum lengkap. Cadangkan data, lalu jalankan 'raportdigital init'.")
            if db().execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise RuntimeError("Basis data perlu diperiksa. Pulihkan cadangan yang sudah diuji.")
        except (OSError, RuntimeError, sqlite3.Error) as error:
            raise click.ClickException(str(error)) from None
        click.echo("Penyimpanan dan skema siap. Kesesuaian kunci harus diuji dengan membuka buku dan arsip.")

    @app.cli.command("teacher")
    def teacher():
        """Create an account or reset its password and revoke its sessions."""
        try:
            check_storage(root)
        except (OSError, RuntimeError) as error:
            raise click.ClickException(str(error)) from None
        name = click.prompt("Nama akun").strip().lower()
        password = click.prompt("Kata sandi (minimal 14 karakter)", hide_input=True, confirmation_prompt="Ulangi kata sandi")
        if not re.fullmatch(r"[a-z0-9._-]{2,64}", name) or not 14 <= len(password) <= 256:
            raise click.ClickException("Nama akun: 2–64 huruf kecil, angka, titik, garis bawah atau tanda hubung. Kata sandi: 14–256 karakter.")
        with db():
            db().execute("INSERT OR REPLACE INTO users VALUES (?,?)", (name, generate_password_hash(password)))
            db().execute("DELETE FROM sessions WHERE name=?", (name,))
        click.echo("Akun siap. Semua sesi lama akun ini sudah dicabut.")

    messages = {
        400: "Permintaan tidak dapat dibaca. Muat ulang halaman, lalu coba lagi.",
        401: "Anda perlu masuk kembali. Salin perubahan yang belum tersimpan sebelum membuka ulang halaman.",
        403: "Akses ditolak. Periksa alamat aplikasi, lalu masuk kembali.",
        404: "Halaman atau buku nilai tidak ditemukan.",
        405: "Tindakan ini tidak tersedia.",
        413: "Ukuran buku melebihi 4 MB. Gunakan logo yang lebih kecil.",
        415: "Format permintaan tidak dikenali.",
        422: "Periksa kelengkapan data, nilai 0–100, dan keputusan akhir tahun.",
        409: "Buku berubah di tab atau perangkat lain. Salin perubahan yang belum tersimpan sebelum memuat ulang halaman.",
        500: "Data belum dapat dibuka. Hubungi pengelola aplikasi; jangan menghapus data atau mengganti kunci penyimpanan.",
        503: "Penyimpanan belum siap. Minta pengelola memeriksa pengaturan aplikasi.",
    }

    @app.errorhandler(500)
    @app.errorhandler(HTTPException)
    def http_error(error):
        response = error.get_response()
        message = messages.get(error.code, "Permintaan belum berhasil diproses.")
        if isinstance(error, SecurityError):
            # Host validation failed before Flask created a URL adapter.
            response.set_data(message)
            response.content_type = "text/plain; charset=utf-8"
        elif request.path.startswith("/api/"):
            response.set_data(app.json.dumps({"error": message, "code": error.code}))
            response.content_type = "application/json"
        else:
            response.set_data(render_template("error.html", message=message, status=error.code))
            response.content_type = "text/html; charset=utf-8"
        return response

    @app.errorhandler(InvalidTag)
    def unreadable_record(_):
        app.logger.error("Record integrity check failed; inspect storage and the original key.")
        return http_error(InternalServerError())

    @app.errorhandler(sqlite3.OperationalError)
    def storage_unavailable(_):
        app.logger.error("Storage unavailable; check data directory, initialization and permissions.")
        return http_error(ServiceUnavailable())

    @app.before_request
    def guard():
        if request.endpoint == "static":
            return
        if request.endpoint is None:
            return
        if not local and not request.is_secure:
            abort(403)
        if local and request.host.split(":")[0] not in {"localhost", "127.0.0.1"}:
            abort(403)
        token = request.cookies.get("rapor_session", "")
        g.token = hashlib.sha256(token.encode()).hexdigest()
        now = int(time.time())
        g.user = db().execute("SELECT * FROM sessions WHERE token=? AND seen>? AND created>?",
                               (g.token, now-1800, now-28800)).fetchone()
        if request.method == "POST":
            if request.headers.get("Origin") != request.host_url.rstrip("/"):
                abort(403)
        if request.endpoint == "login":
            return
        if not g.user:
            return abort(401) if request.path.startswith("/api/") else redirect(url_for("login"))
        if request.method == "POST" and not secrets.compare_digest(
                (request.headers.get("X-CSRF-Token") or request.form.get("csrf", "")).encode(), g.user["csrf"].encode()):
            abort(403)
        with db():
            db().execute("UPDATE sessions SET seen=? WHERE token=?", (now, g.token))

    @app.after_request
    def headers(response):
        response.headers.update({
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "same-origin", "X-Frame-Options": "DENY",
            "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
        })
        return response

    dummy = generate_password_hash(secrets.token_urlsafe())

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")
        now = int(time.time())
        addr = request.remote_addr or "-"
        with db():
            db().execute("DELETE FROM attempts WHERE start<=?", (now-300,))
            db().execute("INSERT INTO attempts VALUES (?,?,1) ON CONFLICT(ip) DO UPDATE SET count=count+1", (addr, now))
            count = db().execute("SELECT count FROM attempts WHERE ip=?", (addr,)).fetchone()[0]
        if count > 10:
            return render_template("login.html", error="Terlalu banyak percobaan. Coba lagi dalam lima menit."), 429
        name = request.form.get("name", "").lower().strip()
        user = db().execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()
        password = request.form.get("password", "")
        if len(password) > 256 or not check_password_hash(user["password"] if user else dummy, password) or not user:
            return render_template("login.html", error="Nama akun atau kata sandi salah."), 401
        token = secrets.token_urlsafe(32)
        with db():
            db().execute("DELETE FROM attempts WHERE ip=?", (addr,))
            db().execute("DELETE FROM sessions WHERE token=? OR seen<=? OR created<=?", (g.token,now-1800,now-28800))
            db().execute("INSERT INTO sessions VALUES (?,?,?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), name, secrets.token_urlsafe(32), now, now))
        response = redirect(url_for("home"))
        response.set_cookie("rapor_session", token, httponly=True, secure=not local, samesite="Strict", path=request.script_root or "/")
        return response

    @app.post("/logout")
    def logout():
        with db():
            db().execute("DELETE FROM sessions WHERE token=?", (g.token,))
        response = redirect(url_for("login"))
        response.delete_cookie("rapor_session", path=request.script_root or "/", secure=not local, httponly=True, samesite="Strict")
        return response

    def book_key(program, year):
        if program not in CLASSES or not 2000 <= year <= 2100:
            abort(404)
        return (g.user["name"], program, year)

    def record(key):
        return db().execute("SELECT * FROM books WHERE owner=? AND program=? AND year=?", key).fetchone()

    def crypt(value, context, encrypt):
        cipher = AESGCM((root / "records.key").read_bytes())
        aad = json.dumps(context).encode()
        if encrypt:
            nonce = os.urandom(12)
            return nonce + cipher.encrypt(nonce, json.dumps(value, ensure_ascii=False).encode(), aad)
        return json.loads(cipher.decrypt(value[:12], value[12:], aad))

    @app.template_filter("jakarta")
    def jakarta(timestamp):
        return datetime.fromtimestamp(timestamp, timezone(timedelta(hours=7))).strftime("%d/%m/%Y %H.%M WIB")

    @app.get("/")
    def home():
        today = date.today()
        year = request.args.get("year", today.year - int(today.month < 7), type=int)
        book_key("a", year)
        owner = g.user["name"]
        revisions = {r["program"]: r["rev"] for r in db().execute("SELECT program,rev FROM books WHERE owner=? AND year=?", (owner,year))}
        rows = db().execute("SELECT * FROM issues WHERE owner=? AND year=? ORDER BY id DESC", (owner,year))
        issues = [{"id": row["id"], "grade": row["grade"], "semester": row["semester"], "issued": row["issued"],
                   "name": issued_profile(issued_state(row), row["program"])["name"]} for row in rows]
        return render_template("home.html", programs=programs, classes=CLASSES, revisions=revisions, issues=issues, year=year)

    @app.get("/book/<program>/<int:year>")
    def editor(program, year):
        book_key(program, year)
        return render_template("editor.html", program=program, year=year, profile=programs[program], issue=0)

    @app.route("/api/book/<program>/<int:year>", methods=["GET", "POST"])
    def book(program, year):
        key = book_key(program, year)
        if request.method == "GET":
            row = record(key)
            if not row:
                return {"rev": 0, "state": None}
            return {"rev": row["rev"], "state": crypt(row["data"], (*key, row["rev"]), False)}
        data = request.get_json()
        if not isinstance(data, dict) or type(data.get("rev")) is not int:
            abort(400)
        with db():
            db().execute("BEGIN IMMEDIATE")
            row = record(key)
            rev = row["rev"] if row else 0
            if data["rev"] != rev:
                abort(409)
            action = data.get("action")
            if action == "rollover":
                if not row or year >= 2100:
                    abort(422)
                target = book_key(program, year + 1)
                if record(target):
                    return {"error": "Buku tahun tujuan sudah ada. Data tujuan tetap tersimpan."}, 409
                state = crypt(row["data"], (*key, rev), False)
                prepare_next_year(state, program, year)
                validate(state, program, year + 1)
                db().execute("INSERT INTO books VALUES (?,?,?,?,?)", (*target,1,crypt(state,(*target,1),True)))
                return {"url": url_for("editor", program=program, year=year+1)}
            if action == "issue":
                if not row:
                    abort(422)
                state = crypt(row["data"], (*key, rev), False)
                grade, semester = state["sch"]["kelas"], state["sch"]["sem"]
                group = state["c"][grade]
                marks = group["ms"][semester]
                subjects = [f"{k}{i}" for k in ("u","p","k") for i,r in enumerate(marks.get(k,[])) if r["n"] and not r["sp"]]
                if not subjects or not group["wali"].strip() or not marks["tgl"].strip() or not group["st"]:
                    abort(422)
                for student in group["st"]:
                    scores = student.get("n", {}).get(semester, {})
                    if not student.get("nama","").strip() or any(scores.get(k, "") == "" for k in subjects):
                        abort(422)
                state["reportVersion"] = 2
                state["reportProfile"] = programs[program]
                state["c"] = {grade: group}
                for student in group["st"]:
                    if semester == "Ganjil":
                        student.pop("decision", None)
                    student["n"] = {semester: student.get("n", {}).get(semester, {})}
                context = (*key, rev, grade, semester, "issue")
                db().execute("INSERT OR IGNORE INTO issues(owner,program,year,rev,grade,semester,issued,data) VALUES (?,?,?,?,?,?,?,?)",
                             (*key,rev,grade,semester,int(time.time()),crypt(state,context,True)))
                issued = db().execute("SELECT id FROM issues WHERE owner=? AND program=? AND year=? AND rev=? AND grade=? AND semester=?", (*key,rev,grade,semester)).fetchone()
                return {"url": url_for("archive", ident=issued[0])}
            if action == "history":
                versions = db().execute("SELECT rev FROM drafts WHERE owner=? AND program=? AND year=? ORDER BY rev DESC", key)
                return {"versions": [r["rev"] for r in versions]}
            if action == "restore":
                if type(data.get("version")) is not int:
                    abort(400)
                previous = db().execute("SELECT rev,data FROM drafts WHERE owner=? AND program=? AND year=? AND rev=?",
                                        (*key,data.get("version"))).fetchone()
                if not previous or not row:
                    abort(404)
                state = crypt(previous["data"], (*key,previous["rev"]), False)
            elif action is None:
                state = data.get("state")
            else:
                abort(400)
            validate(state, program, year)
            # Presentation is operator-controlled, never supplied by a teacher's browser.
            state.pop("reportProfile", None)
            if row:
                db().execute("INSERT INTO drafts VALUES (?,?,?,?,?)", (*key,rev,row["data"]))
                db().execute("DELETE FROM drafts WHERE owner=? AND program=? AND year=? AND rev<=?", (*key,rev-5))
            rev += 1
            db().execute("INSERT OR REPLACE INTO books VALUES (?,?,?,?,?)", (*key,rev,crypt(state,(*key,rev),True)))
        return {"rev": rev}

    def issued_record(ident):
        row = db().execute("SELECT * FROM issues WHERE id=? AND owner=?", (ident,g.user["name"])).fetchone()
        if not row:
            abort(404)
        return row

    def issued_state(row):
        context = tuple(row[k] for k in ("owner","program","year","rev","grade","semester")) + ("issue",)
        return crypt(row["data"], context, False)

    @app.get("/issued/<int:ident>")
    def archive(ident):
        row = issued_record(ident)
        profile = issued_profile(issued_state(row), row["program"])
        return render_template("editor.html", program=row["program"], year=row["year"], profile=profile, issue=ident)

    @app.get("/api/issued/<int:ident>")
    def snapshot(ident):
        row = issued_record(ident)
        return {"state": issued_state(row), "rev":row["rev"]}

    return app
