import os
from dotenv import load_dotenv
from google import genai
from langdetect import detect, DetectorFactory

# -------------------------
# Ensure reproducible lang detection
# -------------------------
DetectorFactory.seed = 0

# -------------------------
# Load environment variables
# -------------------------
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=dotenv_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment")

# -------------------------
# Initialize Gemini client
# -------------------------
client = genai.Client(api_key=GEMINI_API_KEY)

# -------------------------
# Helper functions
# -------------------------

async def translate_to_polish(text: str) -> str:
    """Translate English text to Polish using Gemini"""
    prompt = f"Translate this English sentence to Polish, keeping meaning precise:\n{text}"
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception:
        return text  # fallback: return original text

def clean_text(text: str) -> str:
    """Clean extra formatting and optimize for Telegram Markdown compatibility"""
    # Just trim leading/trailing whitespace
    return text.strip()

async def tutor_response(user_message: str, history: list = None) -> str:
    """
    Unified Teacher Mode: Decides intent, answers/corrects/explains, 
    and provides Polish-first responses with history context.
    """
    try:
        # 1. Detect and ensure we have Polish version of input
        try:
            lang = detect(user_message)
        except Exception:
            lang = "pl"

        if lang == "en":
            user_message_polish = await translate_to_polish(user_message)
            user_message_english = user_message
        else:
            user_message_polish = user_message
            # Basic back-translation for Gemini's context
            user_message_english = "(Polish Input)"

        # 2. Prepare context from history
        context_str = ""
        if history:
            for msg in history:
                role = "Student" if msg["role"] == "user" else "PolaGlot"
                context_str += f"{role}: {msg['content']}\n"

        prompt = (
            "You are PolaGlot, a warm and encouraging Polish language teacher.\n"
            "Your goal is to help the student learn Polish through natural conversation and guidance.\n\n"
            "RULES:\n"
            "0. START by showing the Student's latest message in Polish and English.\n"
            "1. ALWAYS respond in Polish first (a natural answer or acknowledgement).\n"
            "2. Provide an English translation of your Polish response.\n"
            "3. If the student asked a question, answer it. If they sent a sentence with errors, gently correct them.\n"
            "4. Provide a short breakdown of important Polish words/grammar.\n"
            "5. Use Telegram Markdown (bold for keys, monospaced for Polish).\n\n"
            "FORMAT:\n"
            "**Student:** `<Student message in Polish>`\n"
            "*Translation: <Student message in English>*\n\n"
            "---\n\n"
            "**PolaGlot:** `<Polish Response>`\n"
            "*Translation: <English Translation>*\n\n\n"
            "**Teacher's Note:** <Your answer, correction, or encouraging feedback>\n\n\n"
            "**Breakdown:**\n"
            "• `<word>`: <explanation>\n\n"
            f"CONVERSATION HISTORY:\n{context_str}"
            f"STUDENT'S POLISH: {user_message_polish}\n"
            f"STUDENT'S ENGLISH: {user_message_english}"
        )

        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return clean_text(response.text)

    except Exception as e:
        print(f"Agent Error: {e}")
        return "Sorry, PolaGlot is a bit busy. Try again!"

# -------------------------
# Mode-specific functions
# -------------------------

async def conversation_practice(user_message: str) -> str:
    """Respond naturally in Polish for conversation practice"""
    prompt = (
        f"You are PolaGlot, a Polish language tutor.\n"
        f"Respond naturally in Polish to the following user message:\n"
        f"{user_message}\n"
        f"Keep it short, conversational, and do not provide explanations."
    )
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return clean_text(response.text)
    except Exception:
        return "Sorry, I can't respond right now."

async def correct_grammar(user_message: str) -> str:
    """Correct grammar of a Polish sentence"""
    prompt = (
        f"You are PolaGlot, a Polish language tutor.\n"
        f"Correct the grammar of the following Polish sentence:\n"
        f"{user_message}\n"
        f"Respond only with the corrected sentence, no explanations."
    )
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return clean_text(response.text)
    except Exception:
        return "Sorry, I can't correct the sentence right now."

async def explain_vocab(user_message: str) -> str:
    """Explain the vocabulary of a word or phrase"""
    prompt = (
        f"You are PolaGlot, a Polish language tutor.\n"
        f"Explain the meaning and usage of this Polish word or phrase in English:\n"
        f"{user_message}\n"
        f"Keep the explanation short and plain text."
    )
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return clean_text(response.text)
    except Exception:
        return "Sorry, I can't explain the vocabulary right now."

async def generate_quiz() -> tuple[str, str]:
    """Provide a short Polish quiz question and its answer."""
    prompt = (
        f"You are PolaGlot, a Polish language tutor.\n"
        f"Generate one short multiple-choice question in Polish with 3 options.\n"
        f"Return plain text in exactly this format:\n"
        f"Question: <question text>\n"
        f"A) <option A>\n"
        f"B) <option B>\n"
        f"C) <option C>\n"
        f"Answer: <letter and option text>"
    )
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        quiz_text = clean_text(response.text)

        answer = "Not available right now."
        question_lines = []

        for line in quiz_text.splitlines():
            stripped = line.strip()
            lower = stripped.lower()
            if lower.startswith("answer:"):
                answer = stripped.split(":", 1)[1].strip() or answer
            else:
                question_lines.append(line)

        question = "\n".join(question_lines).strip() or quiz_text
        return question, answer
    except Exception:
        return "Sorry, the quiz is not available right now.", "Not available right now."
