# PolaGlot – Polish Language Telegram Bot

**PolaGlot** is a Telegram bot designed to help users learn Polish. It provides explanations of grammar and vocabulary, corrects sentences, allows conversation practice, and offers short quizzes to reinforce learning.

---

## Features

- `/start` – Introduces PolaGlot and instructions for usage.  
- `/explain` – Explain a Polish sentence with grammar and vocabulary breakdown in English.  
- `/correct` – Correct the grammar of a Polish sentence.  
- `/practice` – Practice conversation in Polish; PolaGlot responds naturally in Polish.  
- `/vocab` – Explain the meaning and usage of a word or phrase.  
- `/quiz` – Generate a short Polish quiz question.  
- `/help` – Show the list of available commands.  

The bot automatically detects if input is in English and translates it to Polish before explaining.

---

## Example Interaction

**/practice**  
Let's practice! Send me a sentence and I'll respond in Polish.

**User:** Jak się masz?  
**Bot:**  
Original: How are you?  
Translation: Jak się masz?  

**Breakdown:**  
- Jak – how  
- się – reflexive particle  
- masz – you have (from 'mieć' - to have)  

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
