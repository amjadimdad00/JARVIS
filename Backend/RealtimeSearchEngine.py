import asyncio
import httpx
from ddgs import DDGS
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import wikipedia
import tzlocal
import re
import os

# ==============================
# Load Environment Variables
# ==============================
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")
OpenWeatherKey = env_vars.get("OpenWeatherKey")
NewsAPIKey = env_vars.get("NewsAPIKey")

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# ==============================
# System Prompt (Persona Setup)
# ==============================
System = f"""
Hello, I am {Username}, and you are {Assistantname}, an advanced AI chatbot.
You provide accurate, real-time, up-to-date information from the internet.

*** Guidelines: ***
- Always answer in a professional manner, with proper grammar, punctuation, and clarity.
- Be concise but informative.
- Address me as "Sir".
- Personality: Formal, witty, precise (Jarvis-like tone).
- If there is uncertainty or missing data, state it clearly without guessing.
- Do NOT fabricate links, titles, or facts.
- Reply only in English.
- Stay helpful and factual, no unnecessary roleplay.
- Do NOT use markdown formatting like *, _, or `
"""

# ==============================
# Chat Log Setup
# ==============================
CHAT_LOG_PATH = r"Data\ChatLog.json"
os.makedirs(os.path.dirname(CHAT_LOG_PATH), exist_ok=True)
try:
    with open(CHAT_LOG_PATH, "r") as f:
        messages = load(f)
except Exception:
    messages = []
    with open(CHAT_LOG_PATH, "w") as f:
        dump(messages, f)

# ==============================
# Async API Functions
# ==============================
async def WikipediaSearch(query):
    try:
        return await asyncio.to_thread(lambda: f"[Wikipedia]\n{wikipedia.summary(query, sentences=2)}\n")
    except Exception:
        return "[Wikipedia]\nNo relevant summary found.\n"

async def WeatherSearch(query, client):
    city = "Karachi"
    match = re.search(r"weather in ([a-zA-Z\s]+)", query.lower())
    if match:
        city = match.group(1).strip().title()

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OpenWeatherKey}&units=metric"
    try:
        resp = (await client.get(url)).json()
        if resp.get("main"):
            temp = resp["main"]["temp"]
            desc = resp["weather"][0]["description"]
            return f"[Weather]\n{city}: {temp}°C, {desc}\n"
        return f"[Weather]\nCould not fetch weather for {city}.\n"
    except Exception:
        return "[Weather]\nWeather data not available.\n"

async def NewsSearch(query, client):
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={NewsAPIKey}&pageSize=3"
    try:
        resp = (await client.get(url)).json()
        articles = resp.get("articles", [])
        if not articles:
            return "[News]\nNo recent news found.\n"
        return "[News]\n" + "\n".join(
            f"- {a.get('title','No title')} ({a.get('source',{}).get('name','')})" for a in articles
        )
    except Exception:
        return "[News]\nNews service unavailable.\n"

async def DuckDuckGoSearch(query):
    try:
        results = await asyncio.to_thread(lambda: list(DDGS().text(query, max_results=5)))
        if not results:
            return "[DuckDuckGo]\nNo search results found.\n"
        return "[DuckDuckGo]\n" + "\n\n".join(
            f"Title: {r.get('title','No title')}\nDescription: {r.get('body','No description')}\nURL: {r.get('href','No URL')}"
            for r in results
        )
    except Exception as e:
        return f"[DuckDuckGo]\nSearch unavailable ({e}).\n"

# ==============================
# Utility Functions
# ==============================
def AnswerModifier(answer):
    answer = re.sub(r'\*\*(.*?)\*\*', r'\1', answer)
    answer = re.sub(r'\*(.*?)\*', r'\1', answer)
    return "\n".join(line for line in answer.splitlines() if line.strip())

def Information(only=None):
    now = datetime.datetime.now(tzlocal.get_localzone())
    if only == "time":
        return now.strftime("%I:%M:%S %p")
    elif only == "date":
        return now.strftime("%d %b %Y")
    return now.strftime("%d %b %Y, %I:%M:%S %p")

# ==============================
# System Chat Setup
# ==============================
SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, Sir. How may I assist you?"}
]

# ==============================
# Main Realtime Search Engine
# ==============================
async def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages

    messages.append({"role": "user", "content": prompt})
    query_lower = prompt.lower()
    date_keywords = ["time", "hour", "current time", "date", "day", "month", "year"]

    if any(word in query_lower for word in date_keywords) and "holiday" not in query_lower:
        show_time = "time" in query_lower or "hour" in query_lower
        show_date = any(word in query_lower for word in ["date", "day", "month", "year"])
        now_info = Information("time" if show_time and not show_date else "date" if show_date and not show_time else None)
        return f"Sir, the current {'date and time' if show_time and show_date else 'time' if show_time else 'date'} is: {now_info} ({tzlocal.get_localzone()})"

    async with httpx.AsyncClient() as client_session:
        results = await asyncio.gather(
            WikipediaSearch(prompt),
            WeatherSearch(prompt, client_session),
            NewsSearch(prompt, client_session),
            DuckDuckGoSearch(prompt)
        )

    api_data = "\n".join(results)
    if api_data.strip():
        SystemChatBot.append({"role": "assistant", "content": f"Here is the information I found related to the query:\n{api_data}"})
    
    SystemChatBot.append({"role": "system", "content": Information()})
    answer = ""

    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=SystemChatBot + messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True
        )

        for chunk in completion:
            delta = getattr(chunk.choices[0], "delta", None)
            if delta and getattr(delta, "content", None):
                answer += delta.content
    except Exception as e:
        print(f"[Groq Error] {e}")
        return "Sorry Sir, I could not fetch realtime data."

    answer = AnswerModifier(answer.strip().replace("</s>", ""))
    messages.append({"role": "assistant", "content": answer})

    # Write messages once
    try:
        with open(CHAT_LOG_PATH, "w") as f:
            dump(messages, f, indent=4)
    except Exception as e:
        print(f"[File Write Error] {e}")

    # Prevent system chat growth
    SystemChatBot = SystemChatBot[:3]

    return answer

# ==============================
# Run Loop
# ==============================
async def main():
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = await RealtimeSearchEngine(user_input)
        print(f"{Assistantname}: {response}\n")

if __name__ == "__main__":
    asyncio.run(main())
