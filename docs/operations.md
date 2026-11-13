# Run and maintain

**English** | [Bahasa Indonesia](operations.id.md)

[← README](../README.md) · [Integration](integration.md)

## Storage and accounts

Set `RAPOR_DATA_DIR` before **every** setup or server command to use a directory
other than `~/.raportdigital`. Keep it outside the source tree and web root. In CMD:

```bat
set "RAPOR_DATA_DIR=C:\RaporData"
.venv\Scripts\raportdigital init
.venv\Scripts\raportdigital teacher
.venv\Scripts\raportdigital check
```

`init` is repeatable and applies the additive schema. It refuses to invent a new
key when an existing database has lost its key. `teacher` creates an account or
resets its password and revokes all its sessions. Passwords are prompted without
echoing. There is no public registration or default account.

`check` inspects the key's shape, required tables and SQLite consistency. It does
not prove the key decrypts existing records; open a book and an archive to verify.
Restrict directory access to the service/operator account. New Unix directories
and files are private; on Windows, set and verify the directory ACL yourself.

## Hosting

Use a trusted HTTPS reverse proxy and a private backend connection. The launcher
accepts one proxy IP, rejects plain HTTP in hosted mode, and requires an explicit
public hostname. For a proxy on the same machine, in CMD:

```bat
set "RAPOR_TRUSTED_HOSTS=grades.example.org"
.venv\Scripts\raportdigital serve --trusted-proxy 127.0.0.1
```

Configure the proxy to preserve the public `Host`, set `X-Forwarded-Proto: https`,
and replace `X-Forwarded-For` with the client address. Keep the default backend
binding at `127.0.0.1:8765`. `--prefix /grades` also works when the proxy preserves
that path. Multiple trusted hostnames can be comma-separated; allowlist exact
hosts. The proxy must reject other hosts and redirect HTTP to HTTPS.

For a container, initialize one persistent volume:

```sh
docker build -t raportdigital .
docker volume create raportdigital-data
docker run --rm -v raportdigital-data:/data raportdigital init
docker run --rm -it -v raportdigital-data:/data raportdigital teacher
docker run --rm -v raportdigital-data:/data raportdigital check
```

The image runs as UID 10001. Set
`RAPOR_TRUSTED_HOSTS` and `RAPOR_TRUSTED_PROXY` to the public hostname and actual
proxy peer IP; its default server binds port 8080. Connect it only to the proxy's
private network. For bind mounts, ensure UID 10001 can write the directory.
Initialization is explicit, never an automatic startup reset.

For example, replace the network, hostname and proxy IP below with your own:

```sh
docker run -d --name raportdigital --network your-proxy-network -v raportdigital-data:/data -e RAPOR_TRUSTED_HOSTS=grades.example.org -e RAPOR_TRUSTED_PROXY=192.0.2.10 raportdigital
```

Point the proxy at `raportdigital:8080` on that private network. No public backend
port is needed. The example IP is a placeholder, not a usable default.

The Python factory can also run under another WSGI server. Configure trusted proxy
handling there; do not blindly accept forwarded headers from the internet. See
the [Waitress proxy documentation](https://docs.pylonsproject.org/projects/waitress/en/stable/reverse-proxy.html).
Do not serve this repository as static hosting or expose a Flask debug server.

## Protection and backup

Books, revision history and issued records use AES-256-GCM with account/program/
year/revision context. Account names and other metadata are not encrypted. Session
tokens are hashed in SQLite; sessions expire after 30 idle minutes or eight hours
total. Local mode permits HTTP only for loopback use; hosted cookies are Secure.

The host administrator and anyone holding both database and key are trusted.
Encryption does not protect a compromised host or detect restoration of an entire
older database. Issued-record SQL guards are not a digital signature on PDFs.

Stop the service before copying `records.sqlite3`. Back up `records.key` separately
with restricted access, and keep both from the same instance. Use disk encryption.
Test restoration in a private directory: run `check`, sign in, and open a book and
an archive. Losing the key loses access to encrypted records. Never regenerate it
as part of an upgrade.

## Test and update

**Upgrading an equivalency instance:** set `RAPOR_EDUCATION=equivalency` before
starting the updated service. The default is now SD/SMP/SMA. See
[program setup](integration.md#choose-programs) for custom names. Keep these
settings (and any custom-name file) with your service configuration and backups.

From the repository root after installation:

```bat
.venv\Scripts\python -m unittest discover -v
.venv\Scripts\python -m pip wheel --no-deps . --wheel-dir dist
```

Tests use temporary directories and synthetic records. CI runs Python checks and
wheel building on Windows/Linux. Optional real-browser checks are described in
[tools](../tools/README.md). CI is validation, not an ongoing maintenance service.

Existing users can keep `RAPOR_DATA_DIR`, run the updated install command, then
`init` and `check`. `python app.py` still starts the local server; existing
`python -m flask --app app init` and `teacher` commands still work. Stored books,
accounts and revisions remain compatible; new archives also store their report
labels, while old archives keep their equivalency labels. New installs can use the
wheel without the source checkout; it includes templates, assets and schema.

Maintain your own dependency updates, backups and access controls. This is a
one-off starter; compatibility with future upstream commits is not promised.
