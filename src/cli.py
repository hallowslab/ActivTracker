# cli.py
import os
import shutil

import click

from database import db_session
from models import User
from utils import generate_fake_data


@click.command("create-test-data")
@click.argument("username")
@click.argument("actions", default=3)
@click.argument("days", default=30)
def create_test_data(username, actions=3, days=30):
    """
    Generate fake user action records for a given username.
    
    If the username does not exist, prints a not-found message and does nothing.
    
    Parameters:
        username (str): Username whose data will be generated.
        actions (int): Number of actions to create (default 3).
        days (int): Number of days over which generated actions are distributed (default 30).
    """
    user = db_session.query(User).filter_by(username=username).first()
    if not user:
        print(f"User {username} not found")
        return
    generate_fake_data(user.id, actions, days)
    print(f"Fake data generated for {username}")


@click.command("collect-static")
def collect_static():
    """
    Copy static files from the package's local "static" directory into the directory specified by the STATIC_ROOT environment variable.
    
    If STATIC_ROOT is not set, the command prints an error and exits without copying. While copying, the command reports each file copied and each file skipped due to permission errors, and prints a final summary containing the counts of copied and skipped files.
    """
    source_dir = os.path.join(os.path.dirname(__file__), "static")
    target_dir = os.environ.get("STATIC_ROOT")

    if not target_dir:
        click.echo("Error: STATIC_ROOT environment variable not set")
        return

    # Ensure target directory exists
    os.makedirs(target_dir, exist_ok=True)

    click.echo(f"Copying static files from {source_dir} to {target_dir}")

    # track stats
    copied = 0
    skipped = 0

    # Walk source directory and copy files individually
    for root, _, files in os.walk(source_dir):
        for f in files:
            src_file = os.path.join(root, f)
            rel_path = os.path.relpath(src_file, source_dir)
            dst_file = os.path.join(target_dir, rel_path)

            # Ensure parent directory exists
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)

            try:
                shutil.copy2(src_file, dst_file)
                click.echo(f"Copied {rel_path}")
                copied = copied + 1
            except PermissionError:
                click.echo(f"Skipped {rel_path} (permission denied)")
                skipped = skipped + 1

    click.echo(
        f"Static files collection complete! Copied: {copied}, Skipped: {skipped}"
    )