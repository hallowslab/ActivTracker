import random
from datetime import datetime, timedelta, timezone

from database import db_session
from models import Action, ActivityLog


def generate_fake_data(user_id: int, num_actions: int = 3, days: int = 30):
    """
    Create test Action records for a user and generate ActivityLog entries spanning recent days.
    
    Creates up to `num_actions` new Action rows for the given user (ensuring each action name is unique among the user's existing actions), assigns each action a small random properties dictionary, and inserts `days` of ActivityLog entries per action with randomized `delta` values. Changes are committed to the database; a short summary is printed.
    
    Parameters:
        user_id (int): ID of the user for whom actions and logs are created.
        num_actions (int): Number of test actions to create (default 3).
        days (int): Number of most-recent days to generate logs for each action (default 30).
    """
    _PROPS = ["distance", "time", "quantity"]

    def generate_properties(count: int = 1):
        _props = {}
        for i in range(count):
            _props[random.choice(_PROPS)] = random.randint(1, 10)
        return _props

    # Step 1: Create fake actions
    all_actions = db_session.query(Action).filter_by(user_id=user_id).all()
    actions = []
    existing_names = {a.name for a in all_actions}
    for i in range(num_actions):
        base_name = f"Test Action {len(all_actions)+1}"
        suffix = 1
        name = base_name
        while name in existing_names:
            suffix += 1
            name = f"Test Action {len(all_actions)+suffix}"
        action = Action(
            name=name,
            user_id=user_id,
            notes="Generated for testing",
            properties=generate_properties(random.randint(1, 3)),
        )
        db_session.add(action)
        actions.append(action)
        existing_names.add(name)

    db_session.commit()

    # Step 2: Create random logs for each action
    for action in actions:
        for day in range(days):
            ts = datetime.now(timezone.utc) - timedelta(days=day)
            delta = random.randint(-750, 1000)
            log = ActivityLog(
                action_id=action.id,
                timestamp=ts,
                delta=delta,
                notes=f"Fake log for {action.name} on {ts.date()}",
                properties={},
            )
            db_session.add(log)

    db_session.commit()
    print(f"Generated {num_actions} actions with logs for user {user_id}")