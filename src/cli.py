# cli.py
import click
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
