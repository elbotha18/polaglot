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

async def translate_to_target(text: str, target_language: str) -> str:
    """Translate English text to target language using Gemini - Strict Output"""
    prompt = (
        f"Translate the following English text to {target_language}.\n"
        f"Respond ONLY with the translated text. Do not provide explanations, "
        f"pronunciation guides, or alternate versions.\n\n"
        f"Text to translate: {text}"
    )
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

async def translate_to_english(text: str, source_language: str) -> str:
    """Translate source language text to English using Gemini - Strict Output"""
    prompt = (
        f"Translate the following {source_language} text to English.\n"
        f"Respond ONLY with the translated text. Do not provide explanations.\n\n"
        f"Text to translate: {text}"
    )
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception:
        return text

async def tutor_response(user_message: str, target_language: str, target_code: str, history: list = None) -> str:
    """
    Refined Tutor Mode: Dynamically switches between simple translation 
    and full question-answering based on user intent.
    """
    try:
        # 1. Determine direction and translations
        try:
            detected_lang = detect(user_message)
        except Exception:
            detected_lang = target_code

        if detected_lang == "en":
            # Student typed English
            student_text = user_message
            translation_text = await translate_to_target(user_message, target_language)
            input_lang = "English"
        else:
            # Student typed target language
            student_text = user_message
            translation_text = await translate_to_english(user_message, target_language)
            input_lang = target_language

        # 2. Prepare context from history
        context_str = ""
        if history:
            for msg in history:
                role = "Student" if msg["role"] == "user" else "PolaGlot"
                context_str += f"{role}: {msg['content']}\n"

        prompt = (
            f"You are PolaGlot, a warm and encouraging {target_language} language teacher.\n\n"
            "TASK:\n"
            "Analyze the Student's latest message. Determine if it is a QUESTION or a PHRASE.\n\n"
            "IF IT IS A PHRASE (Greeting, statement, single word):\n"
            "- Show the Student's input and its translation.\n"
            "- Provide a Breakdown of words and idiomatic phrases. Focus on how words function together in this specific context.\n\n"
            "IF IT IS A QUESTION (Asking for facts, help, or information):\n"
            "- Show the Student's input and its translation.\n"
            f"- Answer the question in {target_language} first, then English.\n"
            "- Provide a Breakdown of important words, grammatical structures, or phrases used in both the question and answer.\n\n"
            "FORMAT:\n"
            "**Student:** <Input text>\n"
            "**Translation:** `<Translated text>`\n\n"
            "---\n\n"
            "**PolaGlot:** (Only include this section if it was a QUESTION)\n"
            f"`<Your {target_language} Answer>`\n"
            "*Translation: <Your English Answer>*\n\n\n"
            "**Breakdown:**\n"
            "• `<word or phrase>`: <explanation of meaning and role in this context>\n\n"
            f"CONVERSATION HISTORY:\n{context_str}"
            f"STUDENT'S INPUT ({input_lang}): {student_text}\n"
            f"TRANSLATION: {translation_text}"
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

async def conversation_practice(user_message: str, target_language: str) -> str:
    """Respond naturally in target language for conversation practice"""
    prompt = (
        f"You are PolaGlot, a {target_language} language tutor.\n"
        f"Respond naturally in {target_language} to the following user message:\n"
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

async def correct_grammar(user_message: str, target_language: str) -> str:
    """Correct grammar of a sentence in target language"""
    prompt = (
        f"You are PolaGlot, a {target_language} language tutor.\n"
        f"Correct the grammar of the following {target_language} sentence:\n"
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

async def explain_vocab(user_message: str, target_language: str) -> str:
    """Explain the vocabulary of a word or phrase in target language"""
    prompt = (
        f"You are PolaGlot, a {target_language} language tutor.\n"
        f"Explain the meaning and usage of this {target_language} word or phrase in English:\n"
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

async def generate_welcome_message(target_language: str) -> str:
    """Generate a localized welcome message for the /start command."""
    prompt = (
        f"You are PolaGlot, a warm and encouraging {target_language} language teacher.\n"
        f"Create a short, welcoming message for a new student starting their first lesson in {target_language}.\n\n"
        "REQUIREMENTS:\n"
        f"1. Start with a greeting in {target_language}.\n"
        "2. The REST of the message must be in English.\n"
        "3. Introduce yourself (PolaGlot) as their tutor.\n"
        f"4. Briefly explain that they can send anything in English or {target_language} to start learning.\n"
        "5. Use emojis and keep it friendly. Respond ONLY with the message text."
    )
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return clean_text(response.text)
    except Exception as e:
        print(f"Error generating welcome message: {e}")
        # Generic fallback
        return f"Hello! I am PolaGlot, your {target_language} tutor. Send me a message to begin!"

async def generate_quiz(target_language: str) -> tuple[str, str]:
    """Provide a short target language quiz question and its answer."""
    prompt = (
        f"You are PolaGlot, a {target_language} language tutor.\n"
        f"Generate one short multiple-choice question in {target_language} with 3 options.\n"
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
