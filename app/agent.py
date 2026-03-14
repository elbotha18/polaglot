import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from langdetect import detect, DetectorFactory
from gtts import gTTS
import edge_tts
import io

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

async def tutor_voice_response(audio_bytes: bytes, target_language: str, target_code: str, history: list = None) -> tuple[str, bytes]:
    """
    Handles voice input: Transcribes/Understands audio, generates a tutor response,
    and returns both the text and a TTS version of the response.
    """
    try:
        # Prepare context from history
        context_str = ""
        if history:
            for msg in history:
                role = "Student" if msg["role"] == "user" else "PolaGlot"
                context_str += f"{role}: {msg['content']}\n"

        prompt = (
            f"You are PolaGlot, a warm and encouraging {target_language} language teacher.\n\n"
            "TASK:\n"
            "The student has sent a VOICE NOTE. Listen to it carefully.\n"
            "1. Acknowledge what they said (transcribe the gist of it if helpful).\n"
            "2. Provide feedback on their pronunciation or spoken delivery if you detect any issues.\n"
            "3. Determine if they were asking a QUESTION or making a PHRASE/STATEMENT.\n\n"
            "IF IT IS A PHRASE (Greeting, statement, single word):\n"
            "- Show what you heard and its translation.\n"
            "- Provide a Breakdown of words and idiomatic phrases.\n\n"
            "IF IT IS A QUESTION:\n"
            "- Show what you heard and its translation.\n"
            f"- Answer the question in {target_language} first, then English.\n"
            "- Provide a Breakdown of important words, grammatical structures, or phrases.\n\n"
            "FORMAT:\n"
            "**What I heard:** <Transcribed/summarized spoken input>\n"
            "**Translation:** `<Translated text>`\n\n"
            "---\n\n"
            "**Pronunciation Note:** <Encouraging feedback on their speaking>\n\n"
            "**PolaGlot:**\n"
            f"`<Your {target_language} Answer/Response>`\n"
            "*Translation: <Your English Answer/Response>*\n\n\n"
            "**Breakdown:**\n"
            "• `<word or phrase>`: <explanation>\n\n"
            f"CONVERSATION HISTORY:\n{context_str}"
        )

        # Multimodal request
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                prompt,
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
            ]
        )

        text_reply = clean_text(response.text)
        
        # Generate TTS for the PolaGlot response part
        # We try to extract just the target language response for the voice reply
        voice_text = text_reply
        if "**PolaGlot:**" in text_reply:
            parts = text_reply.split("**PolaGlot:**")
            if len(parts) > 1:
                # Get the first line of the PolaGlot section which should be the target language
                lines = parts[1].strip().splitlines()
                if lines:
                    voice_text = lines[0].replace("`", "").strip()

        audio_reply_bytes = await generate_tts(voice_text, target_code)
        
        return text_reply, audio_reply_bytes

    except Exception as e:
        print(f"Agent Voice Error: {e}")
        return "Sorry, I couldn't process your voice note.", None

async def generate_tts(text: str, lang_code: str) -> bytes:
    """Generates TTS audio bytes for the given text using a high-quality female voice."""
    try:
        # Map simple lang codes to high-quality female neural voices
        voice_map = {
            "pl": "pl-PL-ZofiaNeural",
            "de": "de-DE-KatjaNeural",
            "es": "es-ES-ElviraNeural",
            "fr": "fr-FR-DeniseNeural",
            "it": "it-IT-ElsaNeural"
        }
        
        voice = voice_map.get(lang_code.lower())
        
        if voice:
            # Use Edge-TTS for high-quality neural female voices
            communicate = edge_tts.Communicate(text, voice)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            return audio_data
        else:
            # Fallback to gTTS for other languages
            tts = gTTS(text=text, lang=lang_code)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            return fp.getvalue()
    except Exception as e:
        print(f"TTS Error: {e}")
        # Final fallback to gTTS
        try:
            tts = gTTS(text=text, lang=lang_code)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            return fp.getvalue()
        except:
            return b""

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
