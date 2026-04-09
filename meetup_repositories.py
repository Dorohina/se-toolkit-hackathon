"""
CRUD operations for meetups.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models import Meetup, MeetupParticipant, User
from datetime import datetime
from typing import List, Optional, Tuple


async def create_meetup(
    db: AsyncSession,
    title: str,
    location: str,
    scheduled_time: datetime,
    organizer_user_id: int,
    description: Optional[str] = None,
    address: Optional[str] = None,
) -> Meetup:
    """Create a new meetup."""
    meetup = Meetup(
        title=title,
        description=description,
        organizer_user_id=organizer_user_id,
        location=location,
        address=address,
        scheduled_time=scheduled_time,
    )
    db.add(meetup)
    await db.commit()
    await db.refresh(meetup)
    return meetup


async def get_meetup_by_id(db: AsyncSession, meetup_id: int) -> Optional[Meetup]:
    """Get a meetup by ID with participants."""
    query = (
        select(Meetup)
        .options(selectinload(Meetup.participants))
        .where(Meetup.id == meetup_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_upcoming_meetups(db: AsyncSession, limit: int = 10) -> List[Meetup]:
    """Get upcoming meetups."""
    query = (
        select(Meetup)
        .options(selectinload(Meetup.participants))
        .where(Meetup.scheduled_time >= datetime.utcnow())
        .order_by(Meetup.scheduled_time)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_user_meetups(db: AsyncSession, user_id: int) -> List[Meetup]:
    """Get all meetups organized by or where user is a participant."""
    # Get organized meetups
    organized_query = select(Meetup).where(Meetup.organizer_user_id == user_id)
    organized_result = await db.execute(organized_query)
    organized = organized_result.scalars().all()
    
    # Get participated meetups
    participated_query = (
        select(Meetup)
        .join(MeetupParticipant, Meetup.id == MeetupParticipant.meetup_id)
        .where(MeetupParticipant.user_id == user_id)
    )
    participated_result = await db.execute(participated_query)
    participated = participated_result.scalars().all()
    
    # Combine and deduplicate
    all_meetups = {m.id: m for m in organized + participated}
    return sorted(all_meetups.values(), key=lambda m: m.scheduled_time)


async def join_meetup(db: AsyncSession, meetup_id: int, user_id: int) -> bool:
    """Join a meetup."""
    # Check if already joined
    existing = await db.execute(
        select(MeetupParticipant)
        .where(MeetupParticipant.meetup_id == meetup_id)
        .where(MeetupParticipant.user_id == user_id)
    )
    if existing.scalar_one_or_none():
        return False  # Already joined
    
    participant = MeetupParticipant(
        meetup_id=meetup_id,
        user_id=user_id,
    )
    db.add(participant)
    await db.commit()
    return True


async def leave_meetup(db: AsyncSession, meetup_id: int, user_id: int) -> bool:
    """Leave a meetup."""
    query = (
        select(MeetupParticipant)
        .where(MeetupParticipant.meetup_id == meetup_id)
        .where(MeetupParticipant.user_id == user_id)
    )
    result = await db.execute(query)
    participant = result.scalar_one_or_none()
    
    if participant:
        await db.delete(participant)
        await db.commit()
        return True
    return False


async def get_meetup_participants(
    db: AsyncSession, meetup_id: int
) -> List[Tuple[MeetupParticipant, User]]:
    """Get all participants of a meetup with their user info."""
    query = (
        select(MeetupParticipant, User)
        .join(User, MeetupParticipant.user_id == User.id)
        .where(MeetupParticipant.meetup_id == meetup_id)
    )
    result = await db.execute(query)
    return result.all()


async def cancel_meetup(db: AsyncSession, meetup_id: int, user_id: int) -> bool:
    """Cancel a meetup (only by organizer)."""
    meetup = await get_meetup_by_id(db, meetup_id)
    if not meetup or meetup.organizer_user_id != user_id:
        return False
    
    # Delete all participants first
    participants_query = select(MeetupParticipant).where(
        MeetupParticipant.meetup_id == meetup_id
    )
    participants_result = await db.execute(participants_query)
    participants = participants_result.scalars().all()
    
    for participant in participants:
        await db.delete(participant)
    
    await db.delete(meetup)
    await db.commit()
    return True
