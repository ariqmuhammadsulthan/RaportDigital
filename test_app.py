import hashlib
import secrets
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from cryptography.exceptions import InvalidTag
from werkzeug.security import generate_password_hash

from app import create_app


class GradebookSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = create_app(self.root, local=True)
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
        with self.assertRaises(InvalidTag):
            self.client.get(self.path)

    def test_expiry_and_throttling(self):
        self.login()
        self.db.execute("UPDATE sessions SET seen=?",(int(time.time())-1801,))
        self.db.commit()
        self.assertEqual(self.client.get(self.path).status_code,401)
        for _ in range(10):
            self.assertEqual(self.client.post("/login",data={},headers=self.origin).status_code,401)
        self.assertEqual(self.client.post("/login",data={},headers=self.origin).status_code,429)


if __name__ == "__main__":
    unittest.main()
