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

def translate_to_polish(text: str) -> str:
    """Translate English text to Polish using Gemini"""
    prompt = f"Translate this English sentence to Polish, keeping meaning precise:\n{text}"
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception:
        return text  # fallback: return original text

def clean_text(text: str) -> str:
    """Remove any extra formatting or Markdown"""
    import re
    text = re.sub(r"[*_`]", "", text)
    text = re.sub(r"\n\s*\n", "\n", text)
    return text.strip()

def polaglot_response(user_message: str) -> str:
    """
    Explain grammar and vocabulary in a Polish sentence
    Outputs plain text in Original / Translation / Breakdown format
    """
    try:
        # Detect language
        try:
            lang = detect(user_message)
        except Exception:
            lang = "pl"

        if lang == "en":
            user_message_polish = translate_to_polish(user_message)
        else:
            user_message_polish = user_message

        prompt = (
            f"You are PolaGlot, a Polish language tutor.\n"
            f"Explain grammar and vocabulary in the following sentence, in English.\n"
            f"Output exactly in this format, plain text, no Markdown or emojis:\n\n"
            f"Original: <English sentence>\n"
            f"Translation: <Polish sentence>\n"
            f"Breakdown:\n<each word>: <short explanation>\n\n"
            f"Sentence to explain:\n{user_message_polish}"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return clean_text(response.text)

    except Exception:
        return "Sorry, PolaGlot cannot respond right now."

# -------------------------
# Mode-specific functions
# -------------------------

def conversation_practice(user_message: str) -> str:
    """Respond naturally in Polish for conversation practice"""
    prompt = (
        f"You are PolaGlot, a Polish language tutor.\n"
        f"Respond naturally in Polish to the following user message:\n"
        f"{user_message}\n"
        f"Keep it short, conversational, and do not provide explanations."
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return clean_text(response.text)
    except Exception:
        return "Sorry, I can't respond right now."

def correct_grammar(user_message: str) -> str:
    """Correct grammar of a Polish sentence"""
    prompt = (
        f"You are PolaGlot, a Polish language tutor.\n"
        f"Correct the grammar of the following Polish sentence:\n"
        f"{user_message}\n"
        f"Respond only with the corrected sentence, no explanations."
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return clean_text(response.text)
    except Exception:
        return "Sorry, I can't correct the sentence right now."

def explain_vocab(user_message: str) -> str:
    """Explain the vocabulary of a word or phrase"""
    prompt = (
        f"You are PolaGlot, a Polish language tutor.\n"
        f"Explain the meaning and usage of this Polish word or phrase in English:\n"
        f"{user_message}\n"
        f"Keep the explanation short and plain text."
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return clean_text(response.text)
    except Exception:
        return "Sorry, I can't explain the vocabulary right now."

def generate_quiz() -> str:
    """Provide a short Polish quiz question"""
    prompt = (
        f"You are PolaGlot, a Polish language tutor.\n"
        f"Generate one short multiple-choice question in Polish with 3 options and the correct answer.\n"
        f"Provide only plain text."
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return clean_text(response.text)
    except Exception:
        return "Sorry, the quiz is not available right now."
