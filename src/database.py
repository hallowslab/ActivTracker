# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

# SQLite database in current directory
engine = create_engine("sqlite:///tracker.sqlite3", echo=False)

# Scoped session for thread safety (Flask can reuse this later)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    """Create all tables for models that have been imported."""
    import models  # must be after Base is defined

    Base.metadata.create_all(bind=engine)
    print("Database initialized at tracker.sqlite3")
