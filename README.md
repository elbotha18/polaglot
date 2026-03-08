# PolaGlot 🇵🇱 – Your AI Polish Teacher

**PolaGlot** is a smart Telegram bot designed to help you master the Polish language through natural conversation, personalized guidance, and interactive quizzes.

---

## Features

- **Smart Tutor Mode** – Send any word or sentence in English or Polish. PolaGlot dynamically decides whether to translate, explain vocabulary, or correct your grammar.
- **Polish-First Responses** – The teacher always models correct Polish usage by responding in Polish first, followed by a translation and a helpful teacher's note.
- **Immersion Mode (`/practice`)** – Switch to a Polish-only environment for pure conversation practice.
- **Interactive Quizzes (`/quiz`)** – Reinforce your learning with quick, multiple-choice grammar and vocab quizzes.
- **Contextual Memory** – PolaGlot remembers the last few messages of your conversation, allowing for natural follow-up questions.

---

## Commands

- `/start` – Introduce PolaGlot and reset your session.
- `/tutor` – Switch to Smart Tutor mode (Translations + Explanations).
- `/practice` – Switch to Immersion mode (Polish-only conversation).
- `/quiz` – Take a quick Polish grammar or vocabulary quiz.
- `/help` – Show the list of available commands.

---

## Example Interaction

**User:** "How do I say 'I am learning' in Polish?"

**PolaGlot:**
**Student:** `I am learning`
*Translation: Uczę się*

---

**PolaGlot:** `Uczę się języka polskiego.`
*Translation: I am learning the Polish language.*


**Teacher's Note:** You use the reflexive verb **uczyć się**. Note that when you specify *what* you are learning, you use the Genitive case (języka polskiego).


**Breakdown:**
• `uczę`: I teach (first person singular)
• `się`: reflexive particle (makes it 'I teach myself' -> 'I learn')
• `języka`: language (Genitive case)

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/elbotha18/polaglot.git
cd polaglot
```

Install Python dependencies (recommended in a virtual environment):

```bash
pip install -r requirements.txt
```
Create a .env file in the project root with the following:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_google_gemini_api_key
```
Run the bot:

python app/main.py
Project Structure
polaglot/
├── app/
│   ├── main.py               # Entry point to start the bot
│   ├── agent.py              # Handles Gemini API calls, translations, grammar explanations
│   └── telegram_agent.py     # Telegram bot handlers and command routing
├── .env                      # Environment variables (not committed)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
Dependencies

Python 3.10+

python-telegram-bot

google-genai

langdetect

python-dotenv

Install via:

```bash
pip install python-telegram-bot google-genai langdetect python-dotenv
```

## Contributing

Contributions are welcome! Feel free to submit pull requests to add new features, improve language support, or enhance the bot’s explanations and quiz functionality.

## License

This project is licensed under the MIT License.
