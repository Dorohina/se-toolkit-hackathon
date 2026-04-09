# Development Plans - Event Finder Bot

## Version 1 Plan (Core Feature)

### Goal
Build a functioning Telegram bot that allows users to search for local events by category, date, or location, and save their favorite events.

### Features
1. **Telegram Bot Setup**
   - Initialize bot with python-telegram-bot library
   - Basic command handlers (/start, /help)
   - Interactive inline keyboard navigation

2. **Database Layer**
   - PostgreSQL database setup
   - SQLAlchemy ORM models (Event, User, SavedEvent)
   - Database connection management

3. **Event Search**
   - Search by category (concert, theater, sport, business, IT)
   - Search by date (YYYY-MM-DD format)
   - Search by location (city or venue name)
   - Display upcoming events

4. **Save Events**
   - Save events to user's favorites
   - List saved events
   - Remove events from saved list

5. **User Management**
   - Automatic user registration on first use
   - Track user preferences

6. **Docker Support**
   - Dockerfile for backend
   - docker-compose.yml with PostgreSQL
   - Seed script for sample data

### Technical Stack
- **Language**: Python 3.12
- **Framework**: python-telegram-bot (async version)
- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy 2.0
- **Containerization**: Docker & Docker Compose

### Deliverables
- ✅ Working Telegram bot
- ✅ PostgreSQL database with events
- ✅ Search functionality (category, date, location)
- ✅ Save and list favorite events
- ✅ Docker Compose setup
- ✅ Documentation (README.md)

---

## Version 2 Plan (Enhanced Features)

### Goal
Extend Version 1 with meetup organization features, polish the UI, and deploy the product.

### Features
1. **Meetup Organization** (NEW)
   - Create meetups with title, location, and time
   - Join and leave meetups
   - View user's meetups (organized and participated)
   - View all upcoming meetups
   - Track meetup participants

2. **Improved UI** (ENHANCED)
   - Better event and meetup formatting
   - More inline keyboard interactions
   - Clearer error messages
   - Better user feedback

3. **Database Enhancements** (ENHANCED)
   - Meetup and MeetupParticipant models
   - Proper relationships between models
   - Improved queries with joins

4. **Code Quality** (ENHANCED)
   - Separate meetup repositories
   - Better error handling
   - Improved session management
   - Type hints throughout

5. **Deployment** (NEW)
   - Docker Compose for all services
   - Production-ready configuration
   - Health checks for PostgreSQL
   - PgAdmin for database management (optional)

6. **Documentation** (ENHANCED)
   - Comprehensive README.md
   - Development guide
   - Presentation guide
   - Demo screenshots

### Deliverables
- ✅ Meetup creation and management
- ✅ Meetup participant tracking
- ✅ Improved UI and formatting
- ✅ Docker Compose deployment
- ✅ Complete documentation
- ✅ Presentation (5 slides PDF)
- ✅ Demo video (2 minutes max)

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────┐
│         Telegram Bot (User)             │
│                                         │
│  /start, /events, /search, /saved,     │
│  /meetup, inline keyboards              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Bot Handlers (bot.py)           │
│                                         │
│  - Command handlers                     │
│  - Callback query handlers              │
│  - Message handlers                     │
│  - Session management                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Repositories Layer                 │
│                                         │
│  repositories.py (Events & Users)       │
│  meetup_repositories.py (Meetups)       │
│                                         │
│  - CRUD operations                      │
│  - Complex queries                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Database (PostgreSQL)              │
│                                         │
│  Tables:                                │
│  - events                               │
│  - users                                │
│  - saved_events                         │
│  - meetups                              │
│  - meetup_participants                  │
└─────────────────────────────────────────┘
```

### Data Flow

1. **User sends command** → Bot handler receives message
2. **Handler opens DB session** → Calls repository function
3. **Repository executes query** → Returns results
4. **Handler formats response** → Sends message to user
5. **Session closes** → Cleanup

---

## Testing Strategy

### Unit Tests
- Repository functions (CRUD operations)
- Event filtering and sorting
- User creation and retrieval
- Meetup operations

### Integration Tests
- Bot handlers with database
- Inline keyboard callbacks
- Command processing

### Manual Tests
- Start bot and verify welcome message
- Search events by different criteria
- Save and unsave events
- Create meetup and join it
- Verify data persistence

---

## Deployment Checklist

### Pre-deployment
- [ ] Get Telegram Bot Token from BotFather
- [ ] Configure .env file
- [ ] Test locally with Docker Compose
- [ ] Seed database with sample events
- [ ] Verify all bot commands work

### Deployment
- [ ] Deploy to server (Ubuntu 24.04 VM)
- [ ] Start Docker Compose services
- [ ] Verify PostgreSQL is running
- [ ] Verify bot is responding
- [ ] Check logs for errors

### Post-deployment
- [ ] Test bot from Telegram
- [ ] Verify database persistence
- [ ] Test all features end-to-end
- [ ] Monitor logs for issues

---

## Timeline

### During Lab (Version 1)
- Hour 1: Setup project structure and database models
- Hour 2: Implement event search functionality
- Hour 3: Implement save/list events
- Hour 4: Test with TA and get feedback

### After Lab (Version 2)
- Day 1: Implement meetup features
- Day 2: Improve UI and error handling
- Day 3: Docker Compose and deployment
- Day 4: Documentation and presentation
- Day 5: Record demo video and final testing

---

## TA Feedback Points (To be filled during lab)

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### How Feedback Was Addressed

1. **Feedback**: ___________________________________
   **Action**: _____________________________________

2. **Feedback**: ___________________________________
   **Action**: _____________________________________

3. **Feedback**: ___________________________________
   **Action**: _____________________________________
