"""
CRUD operations for events.
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models import Event, SavedEvent, User
from datetime import datetime, date
from typing import List, Optional


async def get_events_by_category(
    db: AsyncSession,
    category: str,
    limit: int = 10
) -> List[Event]:
    """Get events filtered by category."""
    query = (
        select(Event)
        .where(Event.category.ilike(f"%{category}%"))
        .where(Event.is_active == True)
        .where(Event.start_time >= datetime.utcnow())
        .order_by(Event.start_time)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_events_by_date(
    db: AsyncSession,
    target_date: date,
    limit: int = 10
) -> List[Event]:
    """Get events for a specific date."""
    query = (
        select(Event)
        .where(func.date(Event.start_time) == target_date)
        .where(Event.is_active == True)
        .order_by(Event.start_time)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_events_by_location(
    db: AsyncSession,
    location: str,
    limit: int = 10
) -> List[Event]:
    """Get events filtered by location."""
    query = (
        select(Event)
        .where(Event.location.ilike(f"%{location}%"))
        .where(Event.is_active == True)
        .where(Event.start_time >= datetime.utcnow())
        .order_by(Event.start_time)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_upcoming_events(
    db: AsyncSession,
    limit: int = 10
) -> List[Event]:
    """Get upcoming events."""
    query = (
        select(Event)
        .where(Event.is_active == True)
        .where(Event.start_time >= datetime.utcnow())
        .order_by(Event.start_time)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_event_by_id(db: AsyncSession, event_id: int) -> Optional[Event]:
    """Get a single event by ID."""
    query = select(Event).where(Event.id == event_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_all_categories(db: AsyncSession) -> List[str]:
    """Get all unique event categories."""
    query = select(Event.category).where(Event.is_active == True).distinct()
    result = await db.execute(query)
    return [row[0] for row in result.all()]


async def save_event_for_user(
    db: AsyncSession,
    user_id: int,
    event_id: int
) -> SavedEvent:
    """Save an event for a user."""
    saved_event = SavedEvent(user_id=user_id, event_id=event_id)
    db.add(saved_event)
    await db.commit()
    await db.refresh(saved_event)
    return saved_event


async def get_user_saved_events(
    db: AsyncSession,
    user_id: int
) -> List[Event]:
    """Get all events saved by a user."""
    query = (
        select(Event)
        .join(SavedEvent, Event.id == SavedEvent.event_id)
        .where(SavedEvent.user_id == user_id)
        .order_by(SavedEvent.saved_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


async def remove_saved_event(
    db: AsyncSession,
    user_id: int,
    event_id: int
) -> bool:
    """Remove a saved event for a user."""
    query = (
        select(SavedEvent)
        .where(SavedEvent.user_id == user_id)
        .where(SavedEvent.event_id == event_id)
    )
    result = await db.execute(query)
    saved_event = result.scalar_one_or_none()
    
    if saved_event:
        await db.delete(saved_event)
        await db.commit()
        return True
    return False


async def get_or_create_user(
    db: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    language_code: Optional[str] = None
) -> User:
    """Get or create a user."""
    query = select(User).where(User.telegram_id == telegram_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language_code=language_code or "en"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user
