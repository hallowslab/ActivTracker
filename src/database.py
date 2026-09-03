# database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

# SQLite database in current directory
engine = create_engine("sqlite:///tracker.sqlite3", echo=False)

# Scoped session for thread safety (Flask can reuse this later)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base()
Base.query = db_session.query_property()


def ensure_schema():
    """
    Apply lightweight additive column migrations for existing databases.

    New deployments get the current schema via `create_all`; existing ones may lack columns
    added after creation. Inspects the live tables and runs `ALTER TABLE ... ADD COLUMN` for
    any missing column, backfilling defaults. Idempotent.
    """
    from sqlalchemy import inspect

    # table -> column -> DDL fragment (type + default + nullability)
    additions = {
        "actions": {
            "kind": "VARCHAR(20) NOT NULL DEFAULT 'count'",
            "unit": "VARCHAR(30) NOT NULL DEFAULT ''",
        },
        "activity_log": {
            "value": "FLOAT NULL",
        },
    }

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, cols in additions.items():
            if table not in tables:
                continue  # fresh DB: create_all already produced full schema
            existing = {c["name"] for c in inspector.get_columns(table)}
            for col, ddl in cols.items():
                if col not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))
                    print(f"Migration: added column {table}.{col}")


def init_db():
    """Create all tables for models that have been imported."""
    import models  # must be after Base is defined

    Base.metadata.create_all(bind=engine)
    ensure_schema()
    print("Database initialized at tracker.sqlite3")
