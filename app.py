import getpass
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
from flask import Flask, abort, g, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

PROGRAMS = {"a": "Paket A", "b": "Paket B", "c-ipa": "Paket C IPA", "c-ips": "Paket C IPS"}
CLASSES = {"a": "I II III IV V VI", "b": "VII VIII IX", "c-ipa": "X XI XII", "c-ips": "X XI XII"}
SEMESTERS = ("Ganjil", "Genap")
SCHEMA = """
CREATE TABLE IF NOT EXISTS users(name TEXT PRIMARY KEY, password TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, name TEXT NOT NULL, csrf TEXT NOT NULL,
    seen INTEGER NOT NULL, created INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS attempts(ip TEXT PRIMARY KEY, start INTEGER NOT NULL, count INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS books(owner TEXT, program TEXT, year INTEGER, rev INTEGER, data BLOB,
    PRIMARY KEY(owner,program,year));
CREATE TABLE IF NOT EXISTS issues(id INTEGER PRIMARY KEY, owner TEXT, program TEXT, year INTEGER,
    rev INTEGER, grade TEXT, semester TEXT, issued INTEGER, data BLOB,
    UNIQUE(owner,program,year,rev,grade,semester));
CREATE TRIGGER IF NOT EXISTS keep_issued BEFORE UPDATE ON issues
BEGIN SELECT RAISE(ABORT,'issued record'); END;
CREATE TRIGGER IF NOT EXISTS retain_issued BEFORE DELETE ON issues
BEGIN SELECT RAISE(ABORT,'issued record'); END;
"""


def create_app(directory=None, local=False):
    app = Flask(__name__)
    root = Path(directory or os.environ.get("RAPOR_DATA_DIR") or Path.home() / ".raportdigital").resolve()
    if root.is_relative_to(Path(__file__).resolve().parent):
        raise ValueError("Simpan basis data di luar repositori.")
    app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(root / "records.sqlite3", timeout=8)
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close(_):
        if "db" in g:
            g.db.close()

    @app.cli.command("init")
    def initialize():
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = root / "records.key"
        if not path.exists():
            if (root / "records.sqlite3").exists():
                raise RuntimeError("Pulihkan kunci asli sebelum melanjutkan.")
            with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as key:
                key.write(AESGCM.generate_key(bit_length=256))
        db().executescript(SCHEMA)

    @app.cli.command("teacher")
    def teacher():
        name = input("Nama akun: ").strip().lower()
        password = getpass.getpass("Kata sandi (minimal 14 karakter): ")
        if not re.fullmatch(r"[a-z0-9._-]{2,64}", name) or not 14 <= len(password) <= 256:
            raise ValueError("Nama akun atau panjang kata sandi tidak sesuai.")
        if password != getpass.getpass("Ulangi kata sandi: "):
            raise ValueError("Kata sandi berbeda.")
        with db():
            db().execute("INSERT OR REPLACE INTO users VALUES (?,?)", (name, generate_password_hash(password)))
            db().execute("DELETE FROM sessions WHERE name=?", (name,))

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
        response = redirect("/")
        response.set_cookie("rapor_session", token, httponly=True, secure=not local, samesite="Strict")
        return response

    @app.post("/logout")
    def logout():
        with db():
            db().execute("DELETE FROM sessions WHERE token=?", (g.token,))
        response = redirect("/login")
        response.delete_cookie("rapor_session")
        return response

    def book_key(program, year):
        if program not in PROGRAMS or not 2000 <= year <= 2100:
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
        issues = db().execute("SELECT id,program,grade,semester,rev,issued FROM issues WHERE owner=? AND year=? ORDER BY id DESC", (owner,year)).fetchall()
        return render_template("home.html", programs=PROGRAMS, revisions=revisions, issues=issues, year=year)

    @app.get("/book/<program>/<int:year>")
    def editor(program, year):
        book_key(program, year)
        return render_template("editor.html", program=program, year=year, title=PROGRAMS[program], issue=0)

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
            if data.get("action") == "issue":
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
                state["c"] = {grade: group}
                for student in group["st"]:
                    student["n"] = {semester: student.get("n", {}).get(semester, {})}
                context = (*key, rev, grade, semester, "issue")
                db().execute("INSERT OR IGNORE INTO issues(owner,program,year,rev,grade,semester,issued,data) VALUES (?,?,?,?,?,?,?,?)",
                             (*key,rev,grade,semester,int(time.time()),crypt(state,context,True)))
                issued = db().execute("SELECT id FROM issues WHERE owner=? AND program=? AND year=? AND rev=? AND grade=? AND semester=?", (*key,rev,grade,semester)).fetchone()
                return {"url": url_for("archive", ident=issued[0])}
            state = data.get("state")
            validate(state, program, year)
            rev += 1
            db().execute("INSERT OR REPLACE INTO books VALUES (?,?,?,?,?)", (*key,rev,crypt(state,(*key,rev),True)))
        return {"rev": rev}

    def issued_record(ident):
        row = db().execute("SELECT * FROM issues WHERE id=? AND owner=?", (ident,g.user["name"])).fetchone()
        if not row:
            abort(404)
        return row

    @app.get("/issued/<int:ident>")
    def archive(ident):
        row = issued_record(ident)
        return render_template("editor.html", program=row["program"], year=row["year"], title=PROGRAMS[row["program"]], issue=ident)

    @app.get("/api/issued/<int:ident>")
    def snapshot(ident):
        row = issued_record(ident)
        context = tuple(row[k] for k in ("owner","program","year","rev","grade","semester")) + ("issue",)
        return {"state": crypt(row["data"], context, False), "rev":row["rev"]}

    return app


def subject_key(name):
    return re.sub("[^a-z0-9]", "", name.lower())


def validate(state, program, year):
    def strings(obj, keys):
        return isinstance(obj, dict) and all(isinstance(obj.get(k), str) and len(obj[k]) <= 4000 for k in keys.split())

    def number(value):
        return type(value) in (int,float) and 0 <= value <= 100

    try:
        grades = CLASSES[program].split()
        school = state["sch"]
        assert_valid = (strings(school, "nama npsn a1 a2 a3 ar pos web email tel kepala nipk tempat")
                        and school["kelas"] in grades and school["sem"] in SEMESTERS and set(state["c"]) == set(grades)
                        and type(state.get("rows",30)) is int and 1 <= state.get("rows",30) <= 1000)
        logo = state["logo"]
        if not assert_valid or not isinstance(logo,str) or (logo and not re.fullmatch(r"data:image/png;base64,[A-Za-z0-9+/]+=*",logo)):
            abort(422)
        for group in state["c"].values():
            if not isinstance(group,dict) or not strings(group, "wali nip naik tahun") or group["tahun"] != f"{year}/{year+1}" or set(group["ms"]) != set(SEMESTERS):
                abort(422)
            for m in group["ms"].values():
                if not program.startswith("c") and m.get("p") != []:
                    abort(422)
                if not strings(m,"tgl") or not number(m["batas"]) or not isinstance(m["e"],list) or len(m["e"]) > 30 or not all(strings(e,"n p k") for e in m["e"]):
                    abort(422)
                names = set()
                for k in (("u","p","k") if program.startswith("c") else ("u","k")):
                    if not isinstance(m[k],list) or len(m[k]) > 80:
                        abort(422)
                    for r in m[k]:
                        if not strings(r,"n a b") or not number(r["kkm"]) or r["sp"] not in (0,1):
                            abort(422)
                        if r["n"]:
                            key = subject_key(r["n"])
                            if not key or key in names or key in ("izin","sakit","alpa","constructor","prototype"):
                                abort(422)
                            names.add(key)
            if not isinstance(group["st"],list) or len(group["st"]) > 1000:
                abort(422)
            for student in group["st"]:
                if not isinstance(student,dict) or set(student) - set("nama nipd nisn jk tl tgl agama alamat norap anak tel dk dtg ayah ibu kayah kibu wali kwali n".split()) or not all(isinstance(v,str) and len(v)<=4000 for k,v in student.items() if k!="n"):
                    abort(422)
                for sem, scores in student.get("n",{}).items():
                    if sem not in SEMESTERS or not isinstance(scores,dict):
                        abort(422)
                    for k,v in scores.items():
                        if re.fullmatch(r"e[0-9]{1,2}",k) and isinstance(v,str) and len(v)<=40:
                            continue
                        if k == "catatan" and isinstance(v,str) and len(v)<=4000:
                            continue
                        if not re.fullmatch(r"(?:[upk][0-9]{1,2}|izin|sakit|alpa)",k):
                            abort(422)
                        if not isinstance(v,str) or len(v)>12 or (v and (not re.fullmatch(r"[0-9]+(?:[.][0-9]+)?",v) or (not v.isdigit() if k in ("izin","sakit","alpa") else not 0<=float(v)<=100))):
                            abort(422)
    except (KeyError, TypeError, AttributeError, ValueError, OverflowError):
        abort(422)


if __name__ == "__main__":
    from waitress import serve
    print("Rapor Digital tersedia di http://127.0.0.1:8765")
    serve(create_app(local=True), host="127.0.0.1", port=8765, max_request_body_size=4*1024*1024)


