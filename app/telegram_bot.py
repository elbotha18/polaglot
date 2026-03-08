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
    polaglot_response,
    conversation_practice,
    correct_grammar,
    explain_vocab,
    generate_quiz,
)

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
    
    context.user_data["mode"] = "explain"
    await update.message.reply_text(
        "Cześć! Jestem PolaGlot 🤖\nSend me a sentence in Polish and I'll explain the grammar and vocabulary!"
    )

async def explain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    context.user_data["mode"] = "explain"
    await update.message.reply_text(
        "Send me a Polish sentence, and I will explain its grammar and vocabulary."
    )

async def correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    context.user_data["mode"] = "correct"
    await update.message.reply_text(
        "Send me a Polish sentence, and I will correct the grammar."
    )

async def practice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    context.user_data["mode"] = "practice"
    await update.message.reply_text(
        "Let's practice! Send me a sentence and I'll respond in Polish."
    )

async def vocab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    context.user_data["mode"] = "vocab"
    await update.message.reply_text(
        "Send me a word or phrase, and I will explain its meaning and usage."
    )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    context.user_data["mode"] = "quiz"
    question, answer = generate_quiz()
    context.user_data["quiz_pending"] = True
    context.user_data["quiz_answer"] = answer
    await update.message.reply_text(
        f"{question}\n\nReply with your guess, and I will reveal the answer."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    commands_text = (
        "/start - Introduce PolaGlot\n"
        "/explain - Explain a Polish sentence\n"
        "/correct - Correct grammar\n"
        "/practice - Conversation practice\n"
        "/vocab - Explain vocabulary\n"
        "/quiz - Short Polish quiz\n"
        "/help - Show this list"
    )
    await update.message.reply_text(commands_text)

# -------------------------
# Message handler
# -------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        await update.message.reply_text(private_access_message(update))
        return
    
    user_message = update.message.text
    mode = context.user_data.get("mode", "explain")

    try:
        if mode == "correct":
            reply = correct_grammar(user_message)
        elif mode == "practice":
            reply = conversation_practice(user_message)
        elif mode == "vocab":
            reply = explain_vocab(user_message)
        elif mode == "quiz":
            if context.user_data.get("quiz_pending"):
                answer = context.user_data.get("quiz_answer", "Not available right now.")
                context.user_data["quiz_pending"] = False
                reply = f"Thanks! Correct answer: {answer}\nUse /quiz for another question."
            else:
                reply = "Use /quiz to start a new question."
        else:  # default explanation
            reply = polaglot_response(user_message)
    except Exception:
        reply = "Sorry, PolaGlot cannot respond right now."

    await update.message.reply_text(reply)

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
