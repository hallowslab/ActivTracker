# cli.py
import click
import os
import shutil

from database import db_session
from models import User
from utils import generate_fake_data


@click.command("create-test-data")
@click.argument("username")
@click.argument("actions", default=3)
@click.argument("days", default=30)
def create_test_data(username, actions=3, days=30):
    """Generate fake actions/logs for a user."""
    user = db_session.query(User).filter_by(username=username).first()
    if not user:
        print(f"User {username} not found")
        return
    generate_fake_data(user.id, actions, days)
    print(f"Fake data generated for {username}")


@click.command("collect-static")
def collect_static():
    """Copy static files to the STATIC_ROOT directory safely."""
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
