"""Compatibility entry point; new integrations can import raportdigital.create_app."""
from raportdigital import create_app

if __name__ == "__main__":
    from raportdigital.cli import cli
    cli(["serve", "--local"])
