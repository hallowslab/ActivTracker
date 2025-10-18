# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

# SQLite database in current directory
engine = create_engine("sqlite:///tracker.db", echo=False)

# Scoped session for thread safety (Flask can reuse this later)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    """Import all models and create database tables."""
    import models  # ensure models are imported before create_all()

    Base.metadata.create_all(bind=engine)
    print("Database initialized at tracker.db")
