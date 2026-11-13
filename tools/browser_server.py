"""Disposable fixture server for browser_check.cjs; never use with real records."""
import json
import secrets
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from waitress import create_server
from werkzeug.security import generate_password_hash

from raportdigital import create_app

root = Path(sys.argv[1]).resolve()
app = create_app(root, local=True)
result = app.test_cli_runner().invoke(args=["init"])
if result.exception:
    raise result.exception
password = secrets.token_urlsafe(24)
with closing(sqlite3.connect(root / "records.sqlite3")) as db:
    db.execute("INSERT INTO users VALUES (?,?)", ("fixture", generate_password_hash(password)))
    db.commit()
server = create_server(app, host="127.0.0.1", port=0, url_prefix="/grades")
print(json.dumps({"port": server.effective_port, "password": password}), flush=True)
server.run()
