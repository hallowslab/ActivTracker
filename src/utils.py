from datetime import datetime, timedelta, timezone
from database import db_session
from models import Action, ActivityLog, User
import random


def generate_fake_data(user_id: int, num_actions: int = 3, days: int = 30):
    """
    Generates fake actions and activity logs for testing
    """
    # Step 1: Create fake actions
    actions = []
    for i in range(num_actions):
        action = Action(
            name=f"Test Action {i+1}",
            user_id=user_id,
            notes="Generated for testing",
            properties={"unit": "count"},
        )
        db_session.add(action)
        actions.append(action)

    db_session.commit()

    # Step 2: Create random logs for each action
    for action in actions:
        for day in range(days):
            ts = datetime.now(timezone.utc) - timedelta(days=day)
            delta = random.randint(0, 3)  # 0–3 increments per day
            log = ActivityLog(
                action_id=action.id,
                timestamp=ts,
                delta=delta,
                note=f"Fake log for {action.name} on {ts.date()}",
                properties={},
            )
            db_session.add(log)

    db_session.commit()
    print(f"Generated {num_actions} actions with logs for user {user_id}")
