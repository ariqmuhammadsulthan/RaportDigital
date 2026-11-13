"""Installation, CLI and mounting contracts for template adopters."""
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from raportdigital import create_app
from raportdigital.cli import cli


class TemplateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "data"
        env = patch.dict(os.environ, {"RAPOR_DATA_DIR": str(self.root), "RAPOR_TRUSTED_HOSTS": ""})
        env.start()
        self.addCleanup(env.stop)
        self.runner = CliRunner()

    def init(self):
        result = self.runner.invoke(cli, ["init"])
        self.assertEqual(result.exit_code, 0, result.output)

    def account(self):
        result = self.runner.invoke(cli, ["teacher"], input="teacher\nlong-test-passphrase\nlong-test-passphrase\n")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn("long-test-passphrase", result.output)

    def test_setup_is_repeatable_and_never_replaces_a_missing_key(self):
        result = self.runner.invoke(cli, ["check"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertFalse(self.root.exists())
        self.init()
        key = (self.root / "records.key").read_bytes()
        self.account()
        self.init()
        self.assertEqual((self.root / "records.key").read_bytes(), key)
        self.assertEqual(self.runner.invoke(cli, ["check"]).exit_code, 0)
        (self.root / "records.key").unlink()
        self.assertNotEqual(self.runner.invoke(cli, ["init"]).exit_code, 0)
        self.assertFalse((self.root / "records.key").exists())

    def test_password_reset_revokes_existing_sessions(self):
        self.init()
        self.account()
        client = create_app(local=True).test_client()
        result = client.post("/login", data={"name": "teacher", "password": "long-test-passphrase"},
                             headers={"Origin": "http://localhost"})
        self.assertEqual(result.status_code, 302)
        self.assertEqual(client.get("/").status_code, 200)
        self.account()
        self.assertEqual(client.get("/api/book/a/2026").status_code, 401)

    def test_mounted_app_links_cookies_and_api_urls(self):
        self.init()
        self.account()
        client = create_app(local=True).test_client()
        env = {"SCRIPT_NAME": "/grades"}
        login = client.post("/login", data={"name": "teacher", "password": "long-test-passphrase"},
                            headers={"Origin": "http://localhost"}, environ_overrides=env)
        self.assertEqual(login.location, "/grades/")
        self.assertIn("Path=/grades", login.headers["Set-Cookie"])
        # test_client matches cookie paths before SCRIPT_NAME is applied.
        cookie = client.get_cookie("rapor_session", path="/grades")
        client.set_cookie("rapor_session", cookie.value, path="/")
        page = client.get("/book/a/2026", environ_overrides=env)
        self.assertEqual(page.status_code, 200)
        html = page.get_data(as_text=True)
        self.assertIn('data-endpoint="/grades/api/book/a/2026"', html)
        self.assertIn('data-login="/grades/login"', html)
        self.assertIn('src="/grades/static/report.js"', html)
        self.assertIn('action="/grades/logout"', html)
        with closing(sqlite3.connect(self.root / "records.sqlite3")) as db:
            csrf = db.execute("SELECT csrf FROM sessions").fetchone()[0]
        logout = client.post("/logout", headers={"Origin": "http://localhost", "X-CSRF-Token": csrf},
                             environ_overrides=env)
        self.assertEqual(logout.location, "/grades/login")
        self.assertIn("Path=/grades", logout.headers["Set-Cookie"])

    def test_hosted_requests_require_https_and_expected_host(self):
        self.init()
        self.account()
        with patch.dict(os.environ, {"RAPOR_TRUSTED_HOSTS": "grades.example.test"}):
            client = create_app().test_client()
        self.assertEqual(client.get("/login", base_url="http://grades.example.test").status_code, 403)
        self.assertEqual(client.get("/login", base_url="https://wrong.example.test").status_code, 400)
        login = client.post("/login", base_url="https://grades.example.test",
                            headers={"Origin": "https://grades.example.test"},
                            data={"name": "teacher", "password": "long-test-passphrase"})
        self.assertEqual(login.status_code, 302)
        for flag in ("Secure", "HttpOnly", "SameSite=Strict"):
            self.assertIn(flag, login.headers["Set-Cookie"])

    def test_launcher_refuses_unsafe_modes_and_passes_prefix(self):
        self.init()
        with patch("raportdigital.cli.serve") as serve:
            for args in (["--local", "--host", "0.0.0.0"], [], ["--trusted-proxy", "*"],
                         ["--local", "--prefix", "//bad"]):
                self.assertNotEqual(self.runner.invoke(cli, ["serve", *args]).exit_code, 0)
            serve.assert_not_called()
            result = self.runner.invoke(cli, ["serve", "--local", "--prefix", "/grades"])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(serve.call_args.kwargs["host"], "127.0.0.1")
            self.assertEqual(serve.call_args.kwargs["url_prefix"], "/grades")
            with patch.dict(os.environ, {"RAPOR_TRUSTED_HOSTS": "grades.example.test"}):
                result = self.runner.invoke(cli, ["serve", "--trusted-proxy", "127.0.0.1"])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(serve.call_args.kwargs["trusted_proxy_headers"], {"x-forwarded-proto", "x-forwarded-for"})

    def test_data_cannot_live_in_source_and_missing_storage_is_not_created(self):
        with self.assertRaises(ValueError):
            create_app(Path(__file__).parent / "instance")
        client = create_app(local=True).test_client()
        self.assertEqual(client.get("/api/book/a/2026").status_code, 503)
        self.assertFalse(self.root.exists())


if __name__ == "__main__":
    unittest.main()
