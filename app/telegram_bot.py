import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# Load environment variables from .env file
load_dotenv()
from agent import (
    tutor_response,
    conversation_practice,
    correct_grammar,
    explain_vocab,
    generate_quiz,
)
from database import init_db, save_user_state, load_user_state, add_message, get_history

# Initialize database
init_db()

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    user_id = update.effective_user.id
    save_user_state(user_id, mode="explain")
    await update.message.reply_text(
        "Cześć! Jestem PolaGlot 🤖 Your personal Polish language tutor.\n\n"
        "Just send me anything in English or Polish, and I will help you learn!\n"
        "I can translate, correct your grammar, explain words, or just chat.",
        parse_mode="Markdown"
    )

async def practice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    user_id = update.effective_user.id
    save_user_state(user_id, mode="practice")
    await update.message.reply_text(
        "**Immersion Mode Enabled!** 🇵🇱\nI will now respond only in Polish to help you practice natural conversation. Use /tutor to switch back.",
        parse_mode="Markdown"
    )

async def tutor_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    user_id = update.effective_user.id
    save_user_state(user_id, mode="explain")
    await update.message.reply_text(
        "**Tutor Mode Enabled!** 👨‍🏫\nI will now provide translations, explanations, and grammar notes for everything we discuss.",
        parse_mode="Markdown"
    )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    user_id = update.effective_user.id
    await update.message.reply_chat_action(action="typing")
    question, answer = await generate_quiz()
    save_user_state(user_id, mode="quiz", quiz_pending=True, quiz_answer=answer)
    await update.message.reply_text(
        f"{question}\n\nReply with your guess, and I will reveal the answer.",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    commands_text = (
        "**PolaGlot Commands:**\n"
        "/tutor - Smart Tutor mode (Explanations + English notes)\n"
        "/practice - Immersion mode (Polish only conversation)\n"
        "/quiz - Take a quick Polish quiz\n"
        "/help - Show this list\n\n"
        "**Tip:** You don't need commands to learn! Just send me any Polish sentence to correct it, or ask me a question in English."
    )
    await update.message.reply_text(commands_text, parse_mode="Markdown")

# -------------------------
# Message handler
# -------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Load user state and history from database
    db_state = load_user_state(user_id)
    history = get_history(user_id)
    mode = db_state.get("mode", "explain")

    # Show "typing..." status while Gemini is processing
    await update.message.reply_chat_action(action="typing")

    try:
        if mode == "practice":
            # Immersion Mode
            reply = await conversation_practice(user_message)
        elif mode == "quiz":
            if db_state.get("quiz_pending"):
                answer = db_state.get("quiz_answer", "Not available right now.")
                save_user_state(user_id, quiz_pending=False)
                reply = f"Thanks! Correct answer: {answer}\nUse /quiz for another question."
            else:
                reply = "Use /quiz to start a new question."
        else:
            # Default to Smart Tutor Mode (Unified logic)
            reply = await tutor_response(user_message, history)
        
        # Save interaction to history
        add_message(user_id, "user", user_message)
        add_message(user_id, "assistant", reply)

    except Exception as e:
        print(f"Bot Error: {e}")
        reply = "Sorry, PolaGlot cannot respond right now."

    await update.message.reply_text(reply, parse_mode="Markdown")

# -------------------------
# Run the bot
# -------------------------

def run_bot():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tutor", tutor_mode_command))
    app.add_handler(CommandHandler("practice", practice))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("help", help_command))

    # Register message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# -------------------------
# Run the bot
# -------------------------

def run_bot():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("explain", explain))
    app.add_handler(CommandHandler("correct", correct))
    app.add_handler(CommandHandler("practice", practice))
    app.add_handler(CommandHandler("vocab", vocab))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("help", help_command))

    # Register message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start bot
    app.run_polling()

if __name__ == "__main__":
    run_bot()
