# J.A.R.V.I.S 🤖

Your **AI-powered personal assistant** built with Python — automates tasks, writes content, chats with you like a real companion, and includes early support for GitHub automation (currently in testing).

---

## ✨ Features

### 🖥️ System Automation

- Open installed apps (fallback to website if not installed)
- Close apps
- Google Search & YouTube Search
- Play YouTube videos directly with voice command
- Control system volume (increase, decrease, mute, unmute)
- Adjust screen brightness
- System operations (shutdown, restart, sleep, lock)

### ✍️ Content Writing

- Generate letters, essays, poems, and more

### 💬 Communication

- Send automated WhatsApp messages (define your contacts list inside the code)

### 🎶 Entertainment

- “Tired” mode → plays a random song from a predefined list

### 🐙 GitHub Automation _(Testing Phase)_

⚠️ Currently in testing — not actively running right now.  
Features are implemented but still being verified.

- Create / Delete / List / Find / Open / Clone repositories
- Commit, Push, Pull changes
- Create & Checkout branches
- Search repos and users

### 🤖 AI Chatbot

- Interactive chatbot with custom responses

### 🖼️ Image Generation

- AI-based image generation using Pollinations API

### 🔎 Real-time Search Engine

- Google, Wikipedia, News, Weather
- Summarized results with contextual answers

### 🔊 Speech I/O

- Speech-to-Text and Text-to-Speech integration

### 🖼️ GUI

- Simple yet functional Python + PyQt5 GUI frontend

---

## 🛠️ Tech Stack

- **Languages:** Python
- **Libraries/Modules:** opencv-python, psutil, python-dotenv, groq, AppOpener, pywhatkit, bs4, rich, keyboard, cohere, googlesearch-python, selenium, mtranslate, pygame, edge-tts, PyQt5, webdriver-manager, ddgs, tzlocal, pycaw, comtypes, screen-brightness-control, aiofiles, github

---

## ⚡ Installation

### Clone repo

```bash
git clone https://github.com/amjadimdad00/JARVIS.git
cd JARVIS
```

### Create Virtual Environment (venv)

```bash
python -m venv venv
```

### Activate Venv Script

```bash
venv\Scripts\activate
```

### Install dependencies

```bash

pip install -r requirements.txt
```

### Run the main script

```bash
python Main.py

```

# 📋 Setup Notes

All required environment variables are already defined in the `.env` file.
You just need to add your own **API keys / tokens / usernames**.

Here’s the template:

```env
CohereAPIKey=
Username=
Assistantname=
GroqAPIKey=
InputLanguage=en
AssistantVoice=en-CA-LiamNeural
OpenWeatherKey=
NewsAPIKey=
GitHubToken=
GitHubUsername=
```

### 🔑 API Keys & Tokens

- **[Cohere API Key](https://dashboard.cohere.com/api-keys)** → For text generation (essays, poems, chatbot responses).
- **[Groq API Key](https://console.groq.com/keys)** → For fast LLM inference (used in decision-making / Brain model).
- **[OpenWeather API Key](https://home.openweathermap.org/api_keys)** → For weather data.
- **[News API Key](https://newsapi.org/register)** → For latest news integration.
- **[GitHub Personal Access Token](https://github.com/settings/tokens)** → For GitHub automation (create, delete, commit, push, etc.).

---

### ⚙️ Other Configs

- **Username** → Your own name (assistant will address you with this, or use "Sir" by default).
- **Assistantname** → Custom name for your J.A.R.V.I.S (you can change it to whatever you like).
- **InputLanguage** → Default is `en` (English), can be set to other supported languages.
- **AssistantVoice** → Voice for TTS. Default: `en-CA-LiamNeural`.
- **GitHubUsername** → Your GitHub handle (used in repo automation).

### 📱 WhatsApp Contacts

Inside `automation.py` you’ll find a `CONTACTS` dictionary.  
Add your own contacts here with their phone numbers:

```python
CONTACTS = {
    # Example
    "ChatGPT": "+1 (800) 242-8478",
}
```

### 🎶 Tired Mode Songs

The “Tired” mode plays a random song from a predefined list.  
Kindly add the exact same name of the song as in example.
You can update this list in `automation.py`:

```python
favorite_songs = [
  # Example
  "Afsanay",
]
```

---

### 🛠️ Customization Tips

- You can freely edit `automation.py` to extend functionality.
- Add more commands, songs, or contacts as per your needs.
- The assistant is designed to be modular — feel free to tweak or plug in new APIs.

---

### 🚧 Current Limitations

- GitHub automation features are still **in testing** (not actively running yet).
- WhatsApp automation depends on having a stable internet connection and correct contact numbers.
- Some features may require specific OS permissions (e.g., controlling volume, brightness, or apps).

---

### ✅ Next Steps

1. Add your **API keys** in the `.env` file.
2. Configure your **WhatsApp contacts** in `automation.py`.
3. (Optional) Update your **favorite songs** for Tired Mode.
4. Run `python Main.py` and start using J.A.R.V.I.S 🚀

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).  
You’re free to use, modify, and distribute it with attribution.

---

<p align="center">
  Made with 💖 by <a href="https://linkedin.com/in/amjadimdad" target="_blank"><b>Amjad Imdad</b></a><br>
  ✨ Star this repo if you found it useful! ✨<br>
  <sub>Contributions, feedback & PRs are always welcome 🚀</sub>
</p>
