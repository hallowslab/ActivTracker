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
    """Copy static files to the STATIC_ROOT directory."""
    source_dir = os.path.join(os.path.dirname(__file__), "static")
    target_dir = os.environ.get("STATIC_ROOT", "/var/www/activ/static")

    if not target_dir:
        click.echo("Error: STATIC_ROOT environment variable not set")
        return

    if os.path.exists(target_dir):
        click.echo(f"Removing existing files in {target_dir}")
        shutil.rmtree(target_dir)

    click.echo(f"Copying static files from {source_dir} to {target_dir}")
    shutil.copytree(source_dir, target_dir)
    click.echo("Static files copied successfully!")