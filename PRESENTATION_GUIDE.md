# Presentation Guide - Event Finder Bot

## Slide Structure (5 slides)

### Slide 1: Title
- **Product title**: Event Finder Bot
- **Your name**: [Your Name]
- **Your university email**: your.email@university.edu
- **Your group**: [Your Group]

### Slide 2: Context
- **End-user**: Residents or visitors in cities looking for local events or meetups
- **Problem**: It's difficult for people to find interesting local events or quickly organize meetups with friends
- **Product idea**: Telegram bot that helps users discover local events and organize meetups with friends

### Slide 3: Implementation
- **How you built the product**:
  - Backend: Python 3.12 with python-telegram-bot
  - Database: PostgreSQL 16 with SQLAlchemy ORM
  - Deployment: Docker & Docker Compose
- **Version 1**: Basic event search by category/date/location, save favorite events
- **Version 2**: Meetup creation and management, Docker deployment, improved UI
- **TA feedback addressed**: [Add feedback points here after lab]

### Slide 4: Demo (MOST IMPORTANT)
- **Pre-recorded video** (max 2 minutes with voice-over)
- **Demo script**:
  1. Start the bot with `/start`
  2. Show welcome message and inline keyboard
  3. Search for events by category
  4. Show event cards and demonstrate saving events
  5. Show saved events list
  6. Create a meetup with command
  7. Show meetup details
  
**Recording tips**:
- Use OBS Studio or similar for screen recording
- Speak clearly and explain each step
- Keep it under 2 minutes
- Show the bot working end-to-end

### Slide 5: Links
- **GitHub repo**: https://github.com/[your-username]/se-toolkit-hackathon
- **Deployed product**: https://t.me/[your_bot_username]
- **QR codes**: Generate QR codes for both links

## Tools to Create Presentation
- Google Slides (recommended for collaboration)
- Microsoft PowerPoint
- Canva (for better design)
- LaTeX Beamer (if you prefer code-based)

## Export Format
- Export as PDF before submitting through Moodle
- File name: `event-finder-bot-presentation.pdf`

---

## Quick QR Code Generation

For GitHub repo:
```bash
# Using qrencode (install via apt)
sudo apt install qrencode
qrencode -o github-qr.png "https://github.com/your-username/se-toolkit-hackathon"
```

For Telegram bot:
```bash
qrencode -o telegram-qr.png "https://t.me/your_bot_username"
```

Or use online services:
- https://www.qr-code-generator.com/
- https://qr.io/
