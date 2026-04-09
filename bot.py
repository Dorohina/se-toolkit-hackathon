"""
Telegram Bot handlers for the Event Finder Bot.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler,
)
from datetime import datetime, date
import logging

from database import async_session_maker
from repositories import (
    get_upcoming_events,
    get_events_by_category,
    get_events_by_date,
    get_events_by_location,
    get_event_by_id,
    get_all_categories,
    save_event_for_user,
    get_user_saved_events,
    remove_saved_event,
    get_or_create_user,
)
from meetup_repositories import (
    create_meetup,
    get_upcoming_meetups,
    get_user_meetups,
    join_meetup,
    leave_meetup,
    cancel_meetup,
    get_meetup_by_id,
)

logger = logging.getLogger(__name__)

# Conversation states for meetup creation
MEETUP_TITLE, MEETUP_LOCATION, MEETUP_DATE, MEETUP_TIME = range(4)


def get_chat(update: Update):
    """Get the chat object that works for both messages and callbacks."""
    if update.message:
        return update.message
    elif update.callback_query:
        return update.callback_query
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    async with async_session_maker() as db:
        user = await get_or_create_user(
            db,
            update.effective_user.id,
            update.effective_user.username,
            update.effective_user.first_name,
            update.effective_user.language_code,
        )
        
        welcome_text = (
            f"👋 Hi, {update.effective_user.first_name}!\n\n"
            "I'm a bot for finding local events and meetups.\n\n"
            "📋 *Available commands:*\n"
            "/events - Show upcoming events\n"
            "/search - Search events by category, date or location\n"
            "/saved - My saved events\n"
            "/meetup - Organize a meetup with friends\n"
            "/help - Show help\n\n"
            "Use the buttons below or send a command!"
        )
        
        keyboard = [
            [InlineKeyboardButton("📅 Upcoming events", callback_data="upcoming")],
            [InlineKeyboardButton("🔍 Search", callback_data="search")],
            [InlineKeyboardButton("⭐ My saved events", callback_data="saved")],
            [InlineKeyboardButton("👥 Organize meetup", callback_data="meetup")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "🤖 *Event Finder Bot - Help*\n\n"
        "*Search events:*\n"
        "• /events - Show upcoming events\n"
        "• /search - Search by parameters\n"
        "  - category:concert - Search by category\n"
        "  - date:2024-05-15 - Search by date\n"
        "  - location:London - Search by location\n\n"
        "*Save events:*\n"
        "• Press ⭐ on an event card to save it\n"
        "• /saved - Show saved events\n\n"
        "*Meetups:*\n"
        "• /meetup - Create or find a meetup\n"
        "• meetup:Title:Location:Date-Time - Create a meetup\n\n"
        "*Other:*\n"
        "• /start - Start over\n"
        "• /help - This help"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def show_upcoming_events(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Show upcoming events with pagination."""
    async with async_session_maker() as db:
        # First, acknowledge the click
        if update.callback_query:
            await update.callback_query.edit_message_text("⏳ Searching for upcoming events...")
        elif update.message:
            await update.message.reply_text("⏳ Searching for upcoming events...")
        
        events = await get_upcoming_events(db, limit=10)
        
        if not events:
            keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    "😔 No upcoming events yet. Try again later!",
                    reply_markup=reply_markup
                )
            elif update.message:
                await update.message.reply_text(
                    "😔 No upcoming events yet. Try again later!",
                    reply_markup=reply_markup
                )
            return
        
        # Store events in context for pagination
        context.user_data["events"] = [e.id for e in events]
        
        await _send_event_page(update, context, page)


async def _send_event_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Send a page of events."""
    event_ids = context.user_data.get("events", [])
    events_data = {}
    
    async with async_session_maker() as db:
        from repositories import get_event_by_id
        for eid in event_ids:
            evt = await get_event_by_id(db, eid)
            if evt:
                events_data[eid] = evt
    
    all_events = [events_data[eid] for eid in event_ids if eid in events_data]
    
    EVENTS_PER_PAGE = 1
    total_pages = len(all_events)
    
    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0
    
    event = all_events[page]
    event_text = format_event_message(event)
    event_text += f"\n\n📊 Event {page + 1} of {total_pages}"
    
    keyboard = [
        [InlineKeyboardButton("⭐ Save", callback_data=f"save_{event.id}")],
    ]
    
    # Navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"event_prev_{page}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️ Next", callback_data=f"event_next_{page}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(event_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(event_text, parse_mode="Markdown", reply_markup=reply_markup)


async def search_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command."""
    chat = get_chat(update)
    if not chat:
        return
    
    search_text = (
        "🔍 *Search Events*\n\n"
        "Send query in one of formats:\n"
        "• `category:concert` - search by category\n"
        "• `date:2024-05-15` - search by date\n"
        "• `location:Innopolis` - search by location\n\n"
        "Use button below for quick search:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎵 Concerts", callback_data="search_category:concert")],
        [InlineKeyboardButton("🎭 Theater", callback_data="search_category:theater")],
        [InlineKeyboardButton("⚽ Sport", callback_data="search_category:sport")],
        [InlineKeyboardButton("💼 Business", callback_data="search_category:business")],
        [InlineKeyboardButton("🎮 IT & Gaming", callback_data="search_category:it")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(chat, 'reply_text'):
        await chat.reply_text(search_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif hasattr(chat, 'edit_message_text'):
        await chat.edit_message_text(search_text, parse_mode="Markdown", reply_markup=reply_markup)


async def handle_search_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user search input."""
    query = update.message.text.strip()
    
    # Check if it's a meetup creation command
    if query.startswith("meetup:"):
        await handle_meetup_creation(update, context)
        return
    
    if ":" not in query:
        await update.message.reply_text(
            "❌ Invalid format. Use:\n"
            "• `category:name`\n"
            "• `date:YYYY-MM-DD`\n"
            "• `location:city`"
        )
        return
    
    search_type, search_value = query.split(":", 1)
    search_type = search_type.strip().lower()
    search_value = search_value.strip()
    
    async with async_session_maker() as db:
        if search_type == "category":
            events = await get_events_by_category(db, search_value)
        elif search_type == "date":
            try:
                target_date = date.fromisoformat(search_value)
                events = await get_events_by_date(db, target_date)
            except ValueError:
                await update.message.reply_text("❌ Invalid date format. Use YYYY-MM-DD")
                return
        elif search_type == "location":
            events = await get_events_by_location(db, search_value)
        else:
            await update.message.reply_text("❌ Unknown search type. Use category, date or location")
            return
        
        if not events:
            await update.message.reply_text("😔 Nothing found. Try a different query!")
            return
        
        await update.message.reply_text(f"🔍 Events found: {len(events)}\n")
        
        for event in events[:5]:
            event_text = format_event_message(event)
            keyboard = [
                [InlineKeyboardButton("⭐ Save", callback_data=f"save_{event.id}")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(event_text, parse_mode="Markdown", reply_markup=reply_markup)


async def show_saved_events(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Show user's saved events with pagination."""
    async with async_session_maker() as db:
        user_id = update.effective_user.id
        user = await get_or_create_user(db, user_id)
        
        saved_events = await get_user_saved_events(db, user.id)
        
        if not saved_events:
            text = "⭐ No saved events yet.\nUse search and press ⭐ to save events!"
            keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if update.callback_query:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
            elif update.message:
                await update.message.reply_text(text, reply_markup=reply_markup)
            return
        
        # Store saved event IDs for pagination
        context.user_data["saved_events"] = [e.id for e in saved_events]
        context.user_data["saved_event_user_id"] = user.id
        
        await _send_saved_event_page(update, context, page)


async def _send_saved_event_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Send a page of saved events."""
    event_ids = context.user_data.get("saved_events", [])
    user_id = context.user_data.get("saved_event_user_id")
    events_data = {}
    
    async with async_session_maker() as db:
        from repositories import get_event_by_id
        for eid in event_ids:
            evt = await get_event_by_id(db, eid)
            if evt:
                events_data[eid] = evt
    
    all_events = [events_data[eid] for eid in event_ids if eid in events_data]
    
    total_pages = len(all_events)
    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0
    
    event = all_events[page]
    event_text = format_event_message(event)
    event_text += f"\n\n📊 Saved event {page + 1} of {total_pages}"
    
    keyboard = [
        [InlineKeyboardButton("❌ Remove", callback_data=f"unsave_{event.id}")],
    ]
    
    # Navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"saved_prev_{page}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️ Next", callback_data=f"saved_next_{page}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(event_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(event_text, parse_mode="Markdown", reply_markup=reply_markup)


async def _send_search_event_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Send a page of search results."""
    event_ids = context.user_data.get("search_events", [])
    events_data = {}
    
    async with async_session_maker() as db:
        from repositories import get_event_by_id
        for eid in event_ids:
            evt = await get_event_by_id(db, eid)
            if evt:
                events_data[eid] = evt
    
    all_events = [events_data[eid] for eid in event_ids if eid in events_data]
    
    total_pages = len(all_events)
    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0
    
    event = all_events[page]
    event_text = format_event_message(event)
    event_text += f"\n\n📊 Search result {page + 1} of {total_pages}"
    
    keyboard = [
        [InlineKeyboardButton("⭐ Save", callback_data=f"save_{event.id}")],
    ]
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"search_prev_{page}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️ Next", callback_data=f"search_next_{page}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(event_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(event_text, parse_mode="Markdown", reply_markup=reply_markup)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button clicks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    async with async_session_maker() as db:
        if data == "upcoming":
            await show_upcoming_events(update, context)
        elif data == "search":
            await search_events(update, context)
        elif data == "saved":
            await show_saved_events(update, context)
        elif data == "meetup":
            await meetup_menu(update, context)
        elif data == "create_meetup":
            return await start_meetup_creation(update, context)
        elif data == "main_menu":
            await main_menu(update, context)
        elif data == "my_meetups":
            await show_my_meetups(update, context)
        elif data == "all_meetups":
            await show_all_meetups(update, context)
        elif data.startswith("save_"):
            event_id = int(data.split("_")[1])
            user = await get_or_create_user(db, update.effective_user.id)
            await save_event_for_user(db, user.id, event_id)
            keyboard = [
                [InlineKeyboardButton("⭐ View Saved", callback_data="saved")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("✅ Event saved!", reply_markup=reply_markup)
        elif data.startswith("unsave_"):
            event_id = int(data.split("_")[1])
            user = await get_or_create_user(db, update.effective_user.id)
            await remove_saved_event(db, user.id, event_id)
            keyboard = [
                [InlineKeyboardButton("⭐ View Saved", callback_data="saved")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("❌ Event removed from saved", reply_markup=reply_markup)
        elif data.startswith("join_"):
            meetup_id = int(data.split("_")[1])
            user = await get_or_create_user(db, update.effective_user.id)
            result = await join_meetup(db, meetup_id, user.id)
            if result:
                await query.edit_message_text("✅ Joined meetup!")
            else:
                await query.edit_message_text("ℹ️ You already joined this meetup")
        elif data.startswith("search_category:"):
            category = data.split(":")[1]
            events = await get_events_by_category(db, category)
            if not events:
                keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(f"😔 No events in '{category}' category", reply_markup=reply_markup)
                return
            # Store search results for pagination
            context.user_data["search_events"] = [e.id for e in events]
            await _send_search_event_page(update, context, 0)
        elif data.startswith("search_prev_"):
            page = int(data.split("_")[-1]) - 1
            await _send_search_event_page(update, context, page)
        elif data.startswith("search_next_"):
            page = int(data.split("_")[-1]) + 1
            await _send_search_event_page(update, context, page)
        elif data.startswith("event_prev_"):
            page = int(data.split("_")[-1]) - 1
            await _send_event_page(update, context, page)
        elif data.startswith("event_next_"):
            page = int(data.split("_")[-1]) + 1
            await _send_event_page(update, context, page)
        elif data.startswith("saved_prev_"):
            page = int(data.split("_")[-1]) - 1
            await _send_saved_event_page(update, context, page)
        elif data.startswith("saved_next_"):
            page = int(data.split("_")[-1]) + 1
            await _send_saved_event_page(update, context, page)
        elif data.startswith("meetup_prev_"):
            page = int(data.split("_")[-1]) - 1
            await _send_meetup_page(update, context, page)
        elif data.startswith("meetup_next_"):
            page = int(data.split("_")[-1]) + 1
            await _send_meetup_page(update, context, page)
        elif data.startswith("mymt_prev_"):
            page = int(data.split("_")[-1]) - 1
            await _send_my_meetup_page(update, context, page)
        elif data.startswith("mymt_next_"):
            page = int(data.split("_")[-1]) + 1
            await _send_my_meetup_page(update, context, page)


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu."""
    welcome_text = (
        "📋 *Main Menu*\n\n"
        "What would you like to do?\n\n"
        "📅 *Events* - Find local events\n"
        "👥 *Meetups* - Organize meetups with friends"
    )
    
    keyboard = [
        [InlineKeyboardButton("📅 Upcoming events", callback_data="upcoming")],
        [InlineKeyboardButton("🔍 Search events", callback_data="search")],
        [InlineKeyboardButton("⭐ My saved events", callback_data="saved")],
        [InlineKeyboardButton("👥 Organize meetup", callback_data="meetup")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)


async def meetup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show meetup menu."""
    meetup_text = (
        "👥 *Organize Meetups*\n\n"
        "Create a meetup with friends or find existing one!\n\n"
        "*To view meetups* use buttons below:"
    )
    
    keyboard = [
        [InlineKeyboardButton("➕ Create Meetup", callback_data="create_meetup")],
        [InlineKeyboardButton("📋 My meetups", callback_data="my_meetups")],
        [InlineKeyboardButton("🔍 All meetups", callback_data="all_meetups")],
        [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(meetup_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(meetup_text, parse_mode="Markdown", reply_markup=reply_markup)


async def start_meetup_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the meetup creation conversation."""
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🎉 *Let's create a meetup!*\n\n"
            "What's the *title* of your meetup?\n\n"
            "Example: `Coffee Meetup`, `Study Group`, `Movie Night`\n\n"
            "Send /cancel to cancel.",
            parse_mode="Markdown",
        )
    elif update.message:
        await update.message.reply_text(
            "🎉 *Let's create a meetup!*\n\n"
            "What's the *title* of your meetup?\n\n"
            "Example: `Coffee Meetup`, `Study Group`, `Movie Night`\n\n"
            "Send /cancel to cancel.",
            parse_mode="Markdown",
        )
    return MEETUP_TITLE


async def get_meetup_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get meetup title."""
    context.user_data["meetup_title"] = update.message.text.strip()
    
    await update.message.reply_text(
        "📍 Great! *Where* will the meetup be?\n\n"
        "Example: `Coffee House`, `Central Park`, `Innopolis University`\n\n"
        "Send /cancel to cancel.",
        parse_mode="Markdown",
    )
    return MEETUP_LOCATION


async def get_meetup_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get meetup location."""
    context.user_data["meetup_location"] = update.message.text.strip()
    
    await update.message.reply_text(
        "📅 Perfect! *When* is the meetup?\n\n"
        "Send the *date* in format: `YYYY-MM-DD`\n\n"
        "Example: `2024-05-15`\n\n"
        "Send /cancel to cancel.",
        parse_mode="Markdown",
    )
    return MEETUP_DATE


async def get_meetup_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get meetup date."""
    date_str = update.message.text.strip()
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        context.user_data["meetup_date"] = date_str
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid date format. Please use `YYYY-MM-DD`\n\n"
            "Example: `2024-05-15`",
            parse_mode="Markdown",
        )
        return MEETUP_DATE
    
    await update.message.reply_text(
        "⏰ And what *time*?\n\n"
        "Send the *time* in format: `HH:MM` (24-hour)\n\n"
        "Example: `15:00`, `18:30`\n\n"
        "Send /cancel to cancel.",
        parse_mode="Markdown",
    )
    return MEETUP_TIME


async def get_meetup_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get meetup time and create the meetup."""
    time_str = update.message.text.strip()
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid time format. Please use `HH:MM` (24-hour)\n\n"
            "Example: `15:00`, `18:30`",
            parse_mode="Markdown",
        )
        return MEETUP_TIME
    
    async with async_session_maker() as db:
        user = await get_or_create_user(db, update.effective_user.id)
        
        date_str = context.user_data["meetup_date"]
        scheduled_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        meetup = await create_meetup(
            db,
            title=context.user_data["meetup_title"],
            location=context.user_data["meetup_location"],
            scheduled_time=scheduled_time,
            organizer_user_id=user.id,
        )
        
        keyboard = [
            [InlineKeyboardButton("👥 View All Meetups", callback_data="all_meetups")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Meetup created!*\n\n"
            f"📅 *{meetup.title}*\n"
            f"📍 Location: {meetup.location}\n"
            f"⏰ Time: {meetup.scheduled_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Meetup ID: `{meetup.id}`\n"
            f"Share with friends to invite them!",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
        
        # Clear user data
        context.user_data.pop("meetup_title", None)
        context.user_data.pop("meetup_location", None)
        context.user_data.pop("meetup_date", None)
        
        return ConversationHandler.END


async def cancel_meetup_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel meetup creation."""
    context.user_data.clear()
    
    keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "❌ Meetup creation cancelled.",
        reply_markup=reply_markup,
    )
    return ConversationHandler.END


async def handle_meetup_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle meetup creation from text input - deprecated, kept for backward compatibility."""
    # This is now handled by the conversation handler
    return False


async def show_my_meetups(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Show user's meetups with pagination."""
    async with async_session_maker() as db:
        user = await get_or_create_user(db, update.effective_user.id)
        
        meetups = await get_user_meetups(db, user.id)
        
        if not meetups:
            text = "📋 No meetups yet.\nCreate your first with `/meetup` command"
            keyboard = [
                [InlineKeyboardButton("👥 Create meetup", callback_data="create_meetup")],
                [InlineKeyboardButton("🔍 All meetups", callback_data="all_meetups")],
                [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if update.callback_query:
                await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
            elif update.message:
                await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
            return
        
        context.user_data["my_meetups"] = [m.id for m in meetups]
        
        await _send_my_meetup_page(update, context, page)


async def _send_my_meetup_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Send a page of user's meetups."""
    meetup_ids = context.user_data.get("my_meetups", [])
    meetups_data = {}
    
    async with async_session_maker() as db:
        from meetup_repositories import get_meetup_by_id
        for mid in meetup_ids:
            m = await get_meetup_by_id(db, mid)
            if m:
                meetups_data[mid] = m
    
    all_meetups = [meetups_data[mid] for mid in meetup_ids if mid in meetups_data]
    
    total_pages = len(all_meetups)
    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0
    
    meetup = all_meetups[page]
    user_id = update.effective_user.id
    meetup_text = format_meetup_message(meetup, user_id)
    meetup_text += f"\n\n📊 Your meetup {page + 1} of {total_pages}"
    
    keyboard = [
        [InlineKeyboardButton("📤 Share ID", callback_data=f"share_meetup_{meetup.id}")],
    ]
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"mymt_prev_{page}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️ Next", callback_data=f"mymt_next_{page}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(meetup_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(meetup_text, parse_mode="Markdown", reply_markup=reply_markup)


async def show_all_meetups(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Show all upcoming meetups with pagination."""
    async with async_session_maker() as db:
        meetups = await get_upcoming_meetups(db, limit=10)

        if not meetups:
            text = "🔍 No upcoming meetups yet. Create the first one!"
            keyboard = [
                [InlineKeyboardButton("👥 Create meetup", callback_data="create_meetup")],
                [InlineKeyboardButton("📋 My meetups", callback_data="my_meetups")],
                [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if update.callback_query:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
            elif update.message:
                await update.message.reply_text(text, reply_markup=reply_markup)
            return

        context.user_data["all_meetups"] = [m.id for m in meetups]
        
        await _send_meetup_page(update, context, page)


async def _send_meetup_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Send a page of meetups."""
    meetup_ids = context.user_data.get("all_meetups", [])
    meetups_data = {}
    
    async with async_session_maker() as db:
        from meetup_repositories import get_meetup_by_id
        for mid in meetup_ids:
            m = await get_meetup_by_id(db, mid)
            if m:
                meetups_data[mid] = m
    
    all_meetups = [meetups_data[mid] for mid in meetup_ids if mid in meetups_data]
    
    total_pages = len(all_meetups)
    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0
    
    meetup = all_meetups[page]
    user_id = update.effective_user.id
    meetup_text = format_meetup_message(meetup, user_id)
    meetup_text += f"\n\n📊 Meetup {page + 1} of {total_pages}"
    
    keyboard = [
        [InlineKeyboardButton("✅ Join", callback_data=f"join_{meetup.id}")],
    ]
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"meetup_prev_{page}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️ Next", callback_data=f"meetup_next_{page}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(meetup_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.message:
        await update.message.reply_text(meetup_text, parse_mode="Markdown", reply_markup=reply_markup)


def format_meetup_message(meetup, user_id: int) -> str:
    """Format meetup as a readable message."""
    is_organizer = meetup.organizer_user_id == user_id
    
    message = (
        f"👥 *{meetup.title}*\n\n"
        f"📍 Location: {meetup.location}\n"
    )
    
    if meetup.address:
        message += f"🗺 Address: {meetup.address}\n"
    
    message += f"⏰ Time: {meetup.scheduled_time.strftime('%d.%m.%Y %H:%M')}\n"
    
    participant_count = len(meetup.participants) if hasattr(meetup, 'participants') else 0
    message += f"👥 Participants: {participant_count + 1}\n"
    
    if is_organizer:
        message += "\n👑 You are the organizer"
    
    if meetup.description:
        message += f"\n\n📝 {meetup.description[:200]}"
    
    return message


def format_event_message(event) -> str:
    """Format event as a readable message."""
    start_str = event.start_time.strftime("%d.%m.%Y %H:%M")
    end_str = event.end_time.strftime("%H:%M") if event.end_time else ""
    
    message = (
        f"📅 *{event.title}*\n\n"
        f"🏷 Category: {event.category}\n"
        f"📍 Location: {event.location}\n"
    )
    
    if event.address:
        message += f"🗺 Address: {event.address}\n"
    
    message += f"⏰ Time: {start_str}"
    if end_str:
        message += f" - {end_str}"
    
    if event.organizer:
        message += f"\n👤 Organizer: {event.organizer}"
    
    if event.url:
        message += f"\n🔗 [More info]({event.url})"
    
    if event.description:
        message += f"\n\n📝 {event.description[:200]}{'...' if len(event.description) > 200 else ''}"
    
    return message


def register_handlers(application):
    """Register all bot handlers."""
    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("events", show_upcoming_events))
    application.add_handler(CommandHandler("search", search_events))
    application.add_handler(CommandHandler("saved", show_saved_events))
    
    # Meetup creation conversation handler
    meetup_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_meetup_creation, pattern="^create_meetup$")],
        states={
            MEETUP_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_meetup_title)],
            MEETUP_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_meetup_location)],
            MEETUP_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_meetup_date)],
            MEETUP_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_meetup_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel_meetup_creation)],
    )
    application.add_handler(meetup_conv_handler)
    
    # Search input
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_input))
    
    # Callback queries
    application.add_handler(CallbackQueryHandler(handle_callback))
