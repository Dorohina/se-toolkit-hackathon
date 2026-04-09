"""
Database models for the Event Finder Bot.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Event(Base):
    """Represents a local event in the database."""
    
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)  # e.g., "concert", "meetup", "sport"
    location = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    organizer = Column(String(255), nullable=True)
    url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Event {self.title} on {self.start_time}>"


class User(Base):
    """Represents a Telegram bot user."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    language_code = Column(String(10), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    saved_events = relationship("SavedEvent", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username or self.telegram_id}>"


class SavedEvent(Base):
    """Represents a user's saved/favorite event."""
    
    __tablename__ = "saved_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    saved_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="saved_events")
    event = relationship("Event")
    
    def __repr__(self):
        return f"<SavedEvent user={self.user_id} event={self.event_id}>"


class Meetup(Base):
    """Represents a user-organized meetup."""
    
    __tablename__ = "meetups"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    organizer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)
    scheduled_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    participants = relationship("MeetupParticipant", back_populates="meetup")
    
    def __repr__(self):
        return f"<Meetup {self.title} at {self.scheduled_time}>"


class MeetupParticipant(Base):
    """Represents a participant in a meetup."""
    
    __tablename__ = "meetup_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    meetup_id = Column(Integer, ForeignKey("meetups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    meetup = relationship("Meetup", back_populates="participants")
    user = relationship("User")
    
    def __repr__(self):
        return f"<MeetupParticipant meetup={self.meetup_id} user={self.user_id}>"
