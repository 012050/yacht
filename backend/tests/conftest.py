"""Shared test fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base
from app.core.config import Settings


@pytest.fixture
def settings():
    return Settings(
        DATABASE_URL="sqlite:///./test_data/yacht_test.db",
        SECRET_KEY="test-secret-key",
        JWT_ACCESS_EXPIRE_MINUTES=30,
        JWT_REFRESH_EXPIRE_DAYS=7,
        TURN_TIME_LIMIT=60,
    )


@pytest.fixture
def engine(settings: Settings):
    eng = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def no_autoflush_session(engine):
    """Session mirroring production SessionLocal (autoflush disabled)."""
    Session = sessionmaker(autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()
