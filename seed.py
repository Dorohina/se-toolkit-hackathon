"""
Seed script to populate database with sample events.
"""

import asyncio
from datetime import datetime, timedelta
from database import init_db, async_session_maker
from models import Event


async def seed_events():
    """Insert sample events into the database."""
    await init_db()

    now = datetime.utcnow()

    sample_events = [
        Event(
            title="Innopolis Tech Conference 2026",
            description="Annual technology conference featuring AI, blockchain, and robotics talks.",
            category="it",
            location="Innopolis",
            address="Universitetskaya St, 1",
            start_time=now + timedelta(days=2, hours=10),
            end_time=now + timedelta(days=2, hours=18),
            organizer="Innopolis University",
            url="https://example.com/innopolis-tech-conf",
        ),
        Event(
            title="Kazan IT Meetup: Python & Django",
            description="Community meetup for Python developers. Talks about Django best practices.",
            category="it",
            location="Kazan",
            address="Baumana St, 72",
            start_time=now + timedelta(days=3, hours=18),
            end_time=now + timedelta(days=3, hours=21),
            organizer="Kazan Dev Community",
            url="https://example.com/kazan-python",
        ),
        Event(
            title="Kazan Jazz Festival",
            description="Live jazz performance featuring local and international artists. Free entry.",
            category="concert",
            location="Kazan",
            address="Baumana St, 50",
            start_time=now + timedelta(days=5, hours=19),
            end_time=now + timedelta(days=5, hours=23),
            organizer="Jazz Club Kazan",
            url="https://example.com/kazan-jazz",
        ),
        Event(
            title="Innopolis Startup Pitch Night",
            description="Local startups pitch their ideas to investors and community.",
            category="business",
            location="Innopolis",
            address="Alexander Butlerov St, 17",
            start_time=now + timedelta(days=4, hours=18),
            end_time=now + timedelta(days=4, hours=21),
            organizer="Innopolis Ventures",
            url="https://example.com/pitch-night",
        ),
        Event(
            title="Kazan Theater: Romeo and Juliet",
            description="Classic Shakespeare play in modern interpretation.",
            category="theater",
            location="Kazan",
            address="Kamala Embankment, 12",
            start_time=now + timedelta(days=6, hours=19),
            end_time=now + timedelta(days=6, hours=22),
            organizer="Kazan Tatar Theater",
            url="https://example.com/romeo-juliet",
        ),
        Event(
            title="Innopolis Marathon 2026",
            description="Annual city marathon. 5km, 10km, and 21km routes available.",
            category="sport",
            location="Innopolis",
            address="City Central Park",
            start_time=now + timedelta(days=7, hours=9),
            end_time=now + timedelta(days=7, hours=14),
            organizer="Innopolis Sports Club",
            url="https://example.com/marathon",
        ),
        Event(
            title="Kazan Gaming Night: CS2 Tournament",
            description="Counter-Strike 2 tournament for local teams. Prize pool: 30,000 RUB.",
            category="it",
            location="Kazan",
            address="Chistopolskaya St, 67",
            start_time=now + timedelta(days=8, hours=18),
            end_time=now + timedelta(days=9, hours=2),
            organizer="CyberArena Kazan",
            url="https://example.com/cs2-tournament",
        ),
        Event(
            title="Innopolis Art Exhibition",
            description="Contemporary art exhibition featuring works from local artists.",
            category="theater",
            location="Innopolis",
            address="Innopolis University, Main Building",
            start_time=now + timedelta(days=1, hours=11),
            end_time=now + timedelta(days=1, hours=19),
            organizer="Innopolis Gallery",
            url="https://example.com/art-exhibition",
        ),
        Event(
            title="Kazan Food Festival",
            description="Taste traditional Tatar cuisine and street food from local vendors.",
            category="business",
            location="Kazan",
            address="Kreml St, 1",
            start_time=now + timedelta(days=9, hours=12),
            end_time=now + timedelta(days=9, hours=20),
            organizer="Kazan Tourism Board",
            url="https://example.com/food-festival",
        ),
        Event(
            title="Innopolis Rock Concert: The Echoes",
            description="Live rock concert with special guests DJ Pulse.",
            category="concert",
            location="Innopolis",
            address="Sputnik St, 15",
            start_time=now + timedelta(days=10, hours=20),
            end_time=now + timedelta(days=10, hours=23),
            organizer="Innopolis Events",
            url="https://example.com/rock-concert",
        ),
    ]

    async with async_session_maker() as session:
        session.add_all(sample_events)
        await session.commit()
        print(f"✅ Added {len(sample_events)} sample events to the database")


if __name__ == "__main__":
    asyncio.run(seed_events())
