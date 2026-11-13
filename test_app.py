import copy
import hashlib
import json
import secrets
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from werkzeug.security import generate_password_hash
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app import create_app


class GradebookSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = create_app(self.root, local=True, education="school", program_names={})
        self.app.testing = True
        init = self.app.test_cli_runner().invoke(args=["init"])
        self.assertIsNone(init.exception)
        self.db = sqlite3.connect(self.root / "records.sqlite3")
        self.addCleanup(self.db.close)
        self.password = secrets.token_urlsafe()
        self.db.execute("INSERT INTO users VALUES (?,?)", ("fixture", generate_password_hash(self.password)))
        self.db.commit()
        self.client = self.app.test_client()
        self.origin = {"Origin": "http://localhost"}
        self.path = "/api/book/c-ipa/2026"

    def login(self):
        response = self.client.post("/login", data={"name":"fixture","password":self.password},headers=self.origin)
        self.assertEqual(response.status_code,302)
        csrf = self.db.execute("SELECT csrf FROM sessions").fetchone()[0]
        self.headers = {**self.origin, "X-CSRF-Token":csrf}

    def state(self):
        school = dict.fromkeys("nama npsn a1 a2 a3 ar pos web email tel kepala nipk tempat".split(),"")
        school.update(kelas="X",sem="Ganjil")
        subject = {"n":"Biologi","kkm":70,"sp":0,"a":"","b":""}
        marks = {"u":[],"p":[subject],"k":[],"e":[],"tgl":"10 November","batas":80}
        student = {"nama":"Siswa Uji","n":{"Ganjil":{"p0":"0"}}}
        group = {"wali":"Guru Uji","nip":"","naik":"","tahun":"2026/2027","st":[student],
                 "ms":{"Ganjil":marks,"Genap":marks}}
        return {"sch":school,"logo":"","c":dict.fromkeys(("X","XI","XII"),group)}

    def post(self, **payload):
        return self.client.post(self.path,json=payload,headers=self.headers)

    def test_access_and_revocation(self):
        self.assertEqual(self.client.get(self.path).status_code,401)
        self.login()
        self.assertEqual(self.client.post(self.path,json={},headers=self.origin).status_code,403)
        self.assertEqual(self.client.post(self.path,json={},headers={**self.headers,"Origin":"https://invalid.test"}).status_code,403)
        token = self.client.get_cookie("rapor_session").value
        stored = self.db.execute("SELECT token FROM sessions").fetchone()[0]
        self.assertEqual(stored,hashlib.sha256(token.encode()).hexdigest())
        self.client.post("/logout",headers=self.headers)
        self.client.set_cookie("rapor_session",token)
        self.assertEqual(self.client.get(self.path).status_code,401)

    def test_encryption_conflict_and_issue(self):
        self.login()
        state = self.state()
        self.assertEqual(self.post(rev=0,state=state).json,{"rev":1})
        self.assertEqual(self.post(rev=0,state=state).status_code,409)
        issued = self.post(rev=1,action="issue").json["url"].replace("/issued/","/api/issued/")
        self.assertEqual(self.post(rev=1,action="issue").json["url"],issued[4:])
        original = self.client.get(issued).json["state"]
        self.assertEqual(list(original["c"]),["X"])
        self.assertEqual(self.client.post(issued,headers=self.headers).status_code,405)
        state["c"]["X"]["st"][0]["n"]["Ganjil"]["p0"]="101"
        self.assertEqual(self.post(rev=1,state=state).status_code,422)
        state["c"]["X"]["st"][0]["n"]["Ganjil"]["p0"]="80"
        self.assertEqual(self.post(rev=1,state=state).status_code,200)
        self.assertEqual(self.client.get(issued).json["state"],original)
        ciphertext = self.db.execute("SELECT data FROM books").fetchone()[0]
        self.assertNotIn(b"Siswa Uji",ciphertext)
        self.db.execute("UPDATE books SET data=?",(ciphertext[:-1]+bytes([ciphertext[-1]^1]),))
        self.db.commit()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json["code"], 500)
        self.assertNotIn("InvalidTag", response.get_data(as_text=True))
        self.assertEqual(self.client.get(issued).json["state"], original)

    def test_roster_uses_confirmed_decisions_and_preserves_source(self):
        self.login()
        state = self.state()
        # Independent fixtures for each grade.
        state["c"] = {grade: copy.deepcopy(group) for grade,group in state["c"].items()}
        for grade,decision in [("X","Naik kelas"),("XI","Tinggal kelas"),("XII","Lulus")]:
            student = state["c"][grade]["st"][0]
            student.update(nama=grade,decision=decision,norap="sample")
        state["c"]["X"]["st"][0].pop("decision")
        self.assertEqual(self.post(rev=0,state=state).status_code,200)
        self.assertEqual(self.post(rev=1,action="rollover").status_code,422)
        state["c"]["X"]["st"][0]["decision"]="Naik kelas"
        self.assertEqual(self.post(rev=1,state=state).status_code,200)
        self.assertEqual(self.post(rev=1,action="rollover").status_code,409)
        self.assertEqual(self.post(rev=2,action="rollover").status_code,200)
        target = self.client.get(self.path.replace("2026","2027")).json["state"]
        self.assertEqual(target["c"]["XI"]["st"],[{"nama":"X"},{"nama":"XI"}])
        self.assertFalse(target["c"]["XII"]["st"])
        self.assertEqual(target["c"]["XI"]["ms"]["Genap"]["tgl"],"")
        self.assertEqual(self.post(rev=2,action="rollover").status_code,409)
        self.assertEqual(self.client.get(self.path).json["state"],state)

    def test_teacher_ownership_and_issued_write_guards(self):
        self.login()
        self.assertEqual(self.post(rev=0, state=self.state()).status_code, 200)
        archive = self.post(rev=1, action="issue").json["url"].replace("/issued/", "/api/issued/")
        self.db.execute("INSERT INTO users VALUES (?,?)", ("other", generate_password_hash(self.password)))
        self.db.commit()
        other = self.app.test_client()
        self.assertEqual(other.post("/login", data={"name": "other", "password": self.password},
                                    headers=self.origin).status_code, 302)
        self.assertEqual(other.get(archive).status_code, 404)
        self.assertEqual(other.get(self.path).json, {"rev": 0, "state": None})
        for sql in ("DELETE FROM issues", "UPDATE issues SET rev=99"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql)
            self.db.rollback()
        self.assertEqual(self.client.get(archive).status_code, 200)

    def test_bounded_encrypted_draft_restore(self):
        self.login()
        state = self.state()
        for revision in range(7):
            state["sch"]["nama"] = str(revision)
            self.assertEqual(self.post(rev=revision,state=state).status_code,200)
        self.assertEqual(self.post(rev=7,action="history").json["versions"],[6,5,4,3,2])
        self.assertEqual(self.post(rev=7,action="restore",version=1).status_code,404)
        self.assertEqual(self.post(rev=6,action="restore",version=2).status_code,409)
        self.assertEqual(self.post(rev=7,action="restore",version=2).json,{"rev":8})
        self.assertEqual(self.client.get(self.path).json["state"]["sch"]["nama"],"1")
        self.assertTrue(all(b"Siswa Uji" not in row[0] for row in self.db.execute("SELECT data FROM drafts")))

    def test_expiry_and_throttling(self):
        self.login()
        self.db.execute("UPDATE sessions SET seen=?",(int(time.time())-1801,))
        self.db.commit()
        self.assertEqual(self.client.get(self.path).status_code,401)
        for _ in range(10):
            self.assertEqual(self.client.post("/login",data={},headers=self.origin).status_code,401)
        self.assertEqual(self.client.post("/login",data={},headers=self.origin).status_code,429)

    def test_preset_changes_keep_books_and_freeze_issued_labels(self):
        self.login()
        state = self.state()
        state["reportProfile"] = {"name": "Browser-supplied name"}
        self.assertEqual(self.post(rev=0, state=state).status_code, 200)
        state.pop("reportProfile")
        self.assertEqual(self.client.get(self.path).json["state"], state)
        archive = self.post(rev=1, action="issue").json["url"]
        issued = self.client.get("/api" + archive).json["state"]
        self.assertEqual(issued["reportProfile"]["name"], "SMA IPA")

        # Same store and authenticated session, now opened with another preset.
        other = create_app(self.root, local=True, education="equivalency", program_names={}).test_client()
        other.set_cookie("rapor_session", self.client.get_cookie("rapor_session").value)
        self.assertEqual(other.get(self.path).json["state"], state)
        self.assertIn("<title>Paket C IPA", other.get("/book/c-ipa/2026").text)
        self.assertIn("<title>SMA IPA", other.get(archive).text)
        self.assertIn("SMA IPA · Kelas X", other.get("/?year=2026").text)
        self.assertEqual(other.get("/api" + archive).json["state"], issued)
        self.assertEqual(other.post(self.path, json={"rev": 1, "state": state}, headers=self.headers).status_code, 200)
        new_archive = other.post(self.path, json={"rev": 2, "action": "issue"}, headers=self.headers).json["url"]
        self.assertEqual(other.get("/api" + new_archive).json["state"]["reportProfile"]["name"], "Paket C IPA")

    def test_legacy_archives_keep_equivalency_presentation(self):
        self.login()
        state = self.state()
        state["c"] = {"X": state["c"]["X"]}
        context = ("fixture", "c-ipa", 2026, 1, "X", "Ganjil", "issue")
        nonce = secrets.token_bytes(12)
        cipher = AESGCM((self.root / "records.key").read_bytes())
        encrypted = nonce + cipher.encrypt(nonce, json.dumps(state).encode(), json.dumps(context).encode())
        ident = self.db.execute("INSERT INTO issues(owner,program,year,rev,grade,semester,issued,data) VALUES (?,?,?,?,?,?,?,?)",
                                (*context[:-1], int(time.time()), encrypted)).lastrowid
        self.db.commit()
        page = self.client.get(f"/issued/{ident}")
        self.assertEqual(page.status_code, 200)
        self.assertIn("<title>Paket C IPA", page.text)
        self.assertIn("PROGRAM PAKET C SETARA SMA", page.text)
        self.assertIn("Paket C IPA · Kelas X", self.client.get("/?year=2026").text)
        self.assertEqual(self.client.get(f"/api/issued/{ident}").json["state"], state)


if __name__ == "__main__":
    unittest.main()
