import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from functools import partial

# Load environment variables from .env file
load_dotenv()
from agent import (
    tutor_response,
    conversation_practice,
    correct_grammar,
    explain_vocab,
    generate_quiz,
    generate_welcome_message,
)
from database import (
    init_db, 
    save_user_state, 
    load_user_state, 
    add_message, 
    get_history,
    get_bot_configs,
    update_bot_welcome_message,
)

# Initialize database
init_db()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------------
# Access Control
# -------------------------

def get_allowed_users():
    """Read allowed user IDs from environment variable."""
    allowed_users_str = os.getenv("ALLOWED_USERS", "")
    if not allowed_users_str:
        return set()
    return {int(user_id.strip()) for user_id in allowed_users_str.split(",") if user_id.strip()}

ALLOWED_USERS = get_allowed_users()

def private_access_message(update: Update) -> str:
    user_id = update.effective_user.id if update.effective_user else "unknown"
    return f"This bot is private. Request a demo from the dev for your ID: {user_id}"

async def check_access(update):
    user_id = update.effective_user.id
    return user_id in ALLOWED_USERS

# -------------------------
# Command Handlers
# -------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_config: dict):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    user_id = update.effective_user.id
    bot_id = bot_config['id']
    lang_name = bot_config['language_name']
    welcome_msg = bot_config.get('welcome_message')

    # Generate and cache welcome message if it doesn't exist
    if not welcome_msg:
        await update.message.reply_chat_action(action="typing")
        welcome_msg = await generate_welcome_message(lang_name)
        update_bot_welcome_message(bot_id, welcome_msg)
        # Update the local bot_config for the current session
        bot_config['welcome_message'] = welcome_msg
    
    save_user_state(user_id, bot_id, mode="explain")
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

async def practice(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_config: dict):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    user_id = update.effective_user.id
    bot_id = bot_config['id']
    lang_name = bot_config['language_name']
    
    save_user_state(user_id, bot_id, mode="practice")
    await update.message.reply_text(
        f"**Immersion Mode Enabled!**\nI will now respond only in {lang_name} to help you practice natural conversation. Use /tutor to switch back.",
        parse_mode="Markdown"
    )

async def tutor_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_config: dict):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    user_id = update.effective_user.id
    bot_id = bot_config['id']
    
    save_user_state(user_id, bot_id, mode="explain")
    await update.message.reply_text(
        "**Tutor Mode Enabled!** 👨‍🏫\nI will now provide translations, explanations, and grammar notes for everything we discuss.",
        parse_mode="Markdown"
    )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_config: dict):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    user_id = update.effective_user.id
    bot_id = bot_config['id']
    lang_name = bot_config['language_name']
    
    await update.message.reply_chat_action(action="typing")
    question, answer = await generate_quiz(lang_name)
    save_user_state(user_id, bot_id, mode="quiz", quiz_pending=True, quiz_answer=answer)
    await update.message.reply_text(
        f"{question}\n\nReply with your guess, and I will reveal the answer.",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_config: dict):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    lang_name = bot_config['language_name']
    commands_text = (
        "**PolaGlot Commands:**\n"
        "/tutor - Smart Tutor mode (Explanations + English notes)\n"
        "/practice - Immersion mode (Target language only conversation)\n"
        "/quiz - Take a quick quiz\n"
        "/help - Show this list\n\n"
        f"**Tip:** You don't need commands to learn! Just send me any {lang_name} sentence to correct it, or ask me a question in English."
    )
    await update.message.reply_text(commands_text, parse_mode="Markdown")

# -------------------------
# Message handler
# -------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_config: dict):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    user_id = update.effective_user.id
    bot_id = bot_config['id']
    lang_name = bot_config['language_name']
    lang_code = bot_config['language_code']
    user_message = update.message.text
    
    # Load user state and history from database
    db_state = load_user_state(user_id, bot_id)
    history = get_history(user_id, bot_id)
    mode = db_state.get("mode", "explain")

    # Show "typing..." status while Gemini is processing
    await update.message.reply_chat_action(action="typing")

    try:
        if mode == "practice":
            # Immersion Mode
            reply = await conversation_practice(user_message, lang_name)
        elif mode == "quiz":
            if db_state.get("quiz_pending"):
                answer = db_state.get("quiz_answer", "Not available right now.")
                save_user_state(user_id, bot_id, quiz_pending=False)
                reply = f"Thanks! Correct answer: {answer}\nUse /quiz for another question."
            else:
                reply = "Use /quiz to start a new question."
        else:
            # Default to Smart Tutor Mode (Unified logic)
            reply = await tutor_response(user_message, lang_name, lang_code, history)
        
        # Save interaction to history
        add_message(user_id, bot_id, "user", user_message)
        add_message(user_id, bot_id, "assistant", reply)

    except Exception as e:
        logger.error(f"Bot Error: {e}")
        reply = "Sorry, PolaGlot cannot respond right now."

    await update.message.reply_text(reply, parse_mode="Markdown")

# -------------------------
# Run the bots
# -------------------------

async def run_single_bot(bot_config):
    """Initialize and run a single bot instance."""
    token = bot_config['token']
    lang_name = bot_config['language_name']
    
    logger.info(f"Starting bot for {lang_name}...")
    
    app = ApplicationBuilder().token(token).build()

    # Register commands with bot_config bound
    app.add_handler(CommandHandler("start", partial(start, bot_config=bot_config)))
    app.add_handler(CommandHandler("tutor", partial(tutor_mode_command, bot_config=bot_config)))
    app.add_handler(CommandHandler("practice", partial(practice, bot_config=bot_config)))
    app.add_handler(CommandHandler("quiz", partial(quiz, bot_config=bot_config)))
    app.add_handler(CommandHandler("help", partial(help_command, bot_config=bot_config)))

    # Register message handler with bot_config bound
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, partial(handle_message, bot_config=bot_config)))

    # Initialize and start
    await app.initialize()
    await app.start()
    
    # Extra delay to allow previous instances to clear
    await asyncio.sleep(5)
    
    await app.updater.start_polling(drop_pending_updates=True)
    
    # Keep it running until interrupted
    while True:
        await asyncio.sleep(3600)

async def main():
    configs = get_bot_configs()
    if not configs:
        logger.warning("No bot configurations found in database.")
        return

    # Start all bots concurrently with a substantial delay between them
    # Use gather to run them all in parallel after they've initialized
    tasks = []
    for config in configs:
        tasks.append(run_single_bot(config))
        # Large delay to ensure the previous bot is fully registered
        await asyncio.sleep(10)
        
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bots stopped by user.")
