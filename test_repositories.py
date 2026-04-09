"""
Tests for repository functions.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from models import Base, Event, User, SavedEvent
from repositories import (
    get_upcoming_events,
    get_events_by_category,
    get_events_by_date,
    get_events_by_location,
    save_event_for_user,
    get_user_saved_events,
    remove_saved_event,
    get_or_create_user,
)


# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test engine."""
    return create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(scope="session")
async def setup_db(engine):
    """Create test tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
async def session(engine, setup_db):
    """Create a new session for each test."""
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def sample_event(session):
    """Create a sample event."""
    event = Event(
        title="Test Concert",
        description="A test concert for testing",
        category="concert",
        location="Moscow",
        address="Test Street, 1",
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=1, hours=2),
        organizer="Test Organizer",
        url="https://example.com",
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


@pytest.fixture
async def sample_user(session):
    """Create a sample user."""
    user = User(
        telegram_id=12345,
        username="testuser",
        first_name="Test",
        language_code="en",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_upcoming_events(session, sample_event):
    """Test getting upcoming events."""
    events = await get_upcoming_events(session, limit=10)
    assert len(events) == 1
    assert events[0].title == "Test Concert"


@pytest.mark.asyncio
async def test_get_events_by_category(session, sample_event):
    """Test filtering events by category."""
    events = await get_events_by_category(session, "concert")
    assert len(events) == 1
    assert events[0].category == "concert"


@pytest.mark.asyncio
async def test_get_events_by_location(session, sample_event):
    """Test filtering events by location."""
    events = await get_events_by_location(session, "Moscow")
    assert len(events) == 1
    assert events[0].location == "Moscow"


@pytest.mark.asyncio
async def test_save_and_get_user_events(session, sample_event, sample_user):
    """Test saving events for a user and retrieving them."""
    saved = await save_event_for_user(session, sample_user.id, sample_event.id)
    assert saved.user_id == sample_user.id
    assert saved.event_id == sample_event.id
    
    saved_events = await get_user_saved_events(session, sample_user.id)
    assert len(saved_events) == 1
    assert saved_events[0].id == sample_event.id


@pytest.mark.asyncio
async def test_remove_saved_event(session, sample_event, sample_user):
    """Test removing a saved event."""
    await save_event_for_user(session, sample_user.id, sample_event.id)
    
    result = await remove_saved_event(session, sample_user.id, sample_event.id)
    assert result is True
    
    saved_events = await get_user_saved_events(session, sample_user.id)
    assert len(saved_events) == 0


@pytest.mark.asyncio
async def test_get_or_create_user(session):
    """Test getting or creating a user."""
    user = await get_or_create_user(session, 99999, "newuser", "New")
    assert user.telegram_id == 99999
    assert user.username == "newuser"
    
    # Get the same user again
    user2 = await get_or_create_user(session, 99999)
    assert user2.id == user.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
