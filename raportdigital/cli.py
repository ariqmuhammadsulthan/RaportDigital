"""Explicit local and HTTPS-proxy launch modes; no development server."""
import ipaddress
import os
import re

import click
from waitress import serve

from . import create_app
from .web import check_storage


@click.group()
def cli():
    """Initialize, manage and run a standalone Rapor Digital instance."""


def manage(command):
    app = create_app()
    with app.app_context():
        click.get_current_context().invoke(app.cli.commands[command])


@cli.command("init")
def initialize():
    """Create storage or apply the additive schema."""
    manage("init")


@cli.command("teacher")
def teacher():
    """Create an account or reset its password and revoke its sessions."""
    manage("teacher")


@cli.command("check")
def check():
    """Check storage and schema without displaying private records."""
    manage("check")


@cli.command("serve")
@click.option("--local", is_flag=True, help="HTTP on this computer only.")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", type=click.IntRange(1, 65535), default=8765, show_default=True)
@click.option("--prefix", default="", help="Optional URL path, for example /grades.")
@click.option("--trusted-proxy", envvar="RAPOR_TRUSTED_PROXY", help="IP address of the single HTTPS reverse proxy.")
def run(local, host, port, prefix, trusted_proxy):
    """Run with Waitress. Hosted mode requires a trusted HTTPS proxy."""
    if prefix and not re.fullmatch(r"(?:/[A-Za-z0-9_-]+)+", prefix):
        raise click.UsageError("Use a prefix such as /grades, without a trailing slash.")
    if local and (host not in {"127.0.0.1", "localhost"} or trusted_proxy):
        raise click.UsageError("--local only allows localhost/127.0.0.1 and no proxy.")
    options = {}
    if not local:
        try:
            ipaddress.ip_address(trusted_proxy or "")
        except ValueError:
            raise click.UsageError("Hosted mode requires --trusted-proxy with one IP address.") from None
        if not os.environ.get("RAPOR_TRUSTED_HOSTS", "").strip():
            raise click.UsageError("Set RAPOR_TRUSTED_HOSTS to your public hostname first.")
        options = dict(trusted_proxy=trusted_proxy, trusted_proxy_count=1,
                       trusted_proxy_headers={"x-forwarded-proto", "x-forwarded-for"})
    app = create_app(local=local)
    try:
        check_storage(app.config["RAPOR_DATA_DIR"])
    except (OSError, RuntimeError) as error:
        raise click.ClickException(str(error)) from None
    click.echo(f"Rapor Digital: {host}:{port}{prefix or '/'} ({'local HTTP' if local else 'HTTPS proxy required'})")
    serve(app, host=host, port=port, url_prefix=prefix,
          max_request_body_size=app.config["MAX_CONTENT_LENGTH"],
          clear_untrusted_proxy_headers=True, expose_tracebacks=False, **options)
