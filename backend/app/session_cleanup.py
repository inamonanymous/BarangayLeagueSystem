import os
import re
import struct
import time

import click
from flask import current_app
from flask.cli import with_appcontext


@click.command("cleanup-expired-sessions")
@click.option(
    "--confirm-stopped",
    is_flag=True,
    required=True,
    help="Confirm that all application servers using this session directory are stopped.",
)
@with_appcontext
def cleanup_expired_sessions(confirm_stopped: bool) -> None:
    """Remove expired filesystem sessions while application servers are stopped."""
    directory = current_app.config["SESSION_FILE_DIR"]
    now = time.time()
    removed = 0

    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                if not re.fullmatch(r"[0-9a-f]{32}", entry.name):
                    continue
                if not entry.is_file(follow_symlinks=False):
                    continue
                with open(entry.path, "rb") as session_file:
                    header = session_file.read(4)
                if len(header) != 4:
                    raise click.ClickException(
                        f"Invalid session file header: {entry.path}"
                    )
                expires = struct.unpack("I", header)[0]
                if expires and expires < now:
                    os.remove(entry.path)
                    removed += 1
    except OSError as exc:
        raise click.ClickException(f"Session cleanup failed: {exc}") from exc

    click.echo(f"Removed {removed} expired session file(s).")
