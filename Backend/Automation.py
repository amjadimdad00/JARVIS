from GithubAuto import (
    create_repo,
    delete_repo,
    list_repos,
    find_repo_by_name,
    open_repo_in_browser,
    clone_repo,
    git_commit,
    git_push,
    git_pull,
    git_create_branch,
    git_checkout_branch,
    search_repos,
    search_users,
)
import asyncio
import os
import re
import subprocess
import webbrowser
from dotenv import dotenv_values
from rich import print
from datetime import datetime, timedelta
import json
import random

# ---------------- CONFIG ---------------- #
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

useragent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/100.0.4896.75 Safari/537.36"
)

messages = []
client = None

SystemChatBot = [
    {
        "role": "system",
        "content": (
            f"Hello, I am {os.environ.get('Username', 'Assistant')}, "
            "You're a content writer. You have to write content like letters, codes, "
            "applications, essays, notes, songs, poems, etc."
        ),
    }
]

# Precompiled regex for performance
num_pattern = re.compile(r"\b(\d{1,3})\b")

# ---------------- UTILS ---------------- #
def get_client():
    """Lazy load Groq client only when needed."""
    global client
    if client is None:
        from groq import Groq
        client = Groq(api_key=GroqAPIKey)
    return client

# ---------------- FEATURES ---------------- #
def GoogleSearch(topic: str):
    from pywhatkit import search
    search(topic)
    return True

def YouTubeSearch(topic: str):
    url = f"https://www.youtube.com/results?search_query={topic}"
    webbrowser.open(url)
    return True

def PlayYoutube(query: str):
    from pywhatkit import playonyt
    playonyt(query)
    return True

def OpenApp(app: str):
    try:
        from AppOpener import open as appopen
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except Exception:
        import requests
        from bs4 import BeautifulSoup
        import urllib.parse

        url = f"https://duckduckgo.com/html/?q={app}"
        headers = {"User-Agent": useragent}
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            result = soup.find("a", {"class": "result__a"})
            if result and result.get("href"):
                href = result["href"]
                parsed = urllib.parse.urlparse(href)
                query = urllib.parse.parse_qs(parsed.query)
                direct_url = (
                    urllib.parse.unquote(query["uddg"][0])
                    if "uddg" in query
                    else href
                )
                chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                webbrowser.register(
                    "chrome", None, webbrowser.BackgroundBrowser(chrome_path)
                )
                webbrowser.get("chrome").open(direct_url)
                return True
        return False

def CloseApp(app: str):
    try:
        from AppOpener import close
        close(app, match_closest=False, output=True, throw_error=False)
        return True
    except Exception:
        return False

def Content(topic: str):
    def open_notepad(file):
        subprocess.Popen(["notepad.exe", file])

    def content_writer_ai(prompt):
        client = get_client()
        messages.append({"role": "user", "content": prompt})
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True,
        )
        answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                answer += chunk.choices[0].delta.content
        answer = answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": answer})
        return answer

    topic = topic.replace("Content", "").strip()
    content_by_ai = content_writer_ai(topic)

    os.makedirs("Data", exist_ok=True)
    filename = rf"Data\{topic.lower().replace(' ', '')}.txt"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content_by_ai)

    open_notepad(filename)
    return True

# ---------------- SYSTEM CONTROLS ---------------- #
async def System(command: str):
    command = command.lower()

    async def run_cmd(*args):
        try:
            await asyncio.create_subprocess_exec(*args)
        except Exception as e:
            print(f"[red]System command failed: {e}[/red]")

    if command == "lock":
        await run_cmd("rundll32.exe", "user32.dll,LockWorkStation")
    elif command == "shutdown":
        await run_cmd("shutdown", "/s", "/t", "1")
    elif command == "restart":
        await run_cmd("shutdown", "/r", "/t", "1")
    elif command == "sleep":
        await run_cmd("rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0")
    elif command == "hibernate":
        await run_cmd("rundll32.exe", "powrprof.dll,SetSuspendState", "1,1,0")
    # Volume and brightness logic remains same as before
    return True

# ---------------- REMINDER SYSTEM ---------------- #
reminders = []
time_pattern = re.compile(r"(\d{1,2}(:\d{2})?\s?(AM|PM|am|pm)?)")
relative_pattern = re.compile(r"(?:after|in)?\s*(\d+)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)", re.IGNORECASE)

os.makedirs("Data", exist_ok=True)
REMINDER_FILE = os.path.join("Data", "Reminder.json")

def parse_time(time_str: str):
    now = datetime.now()
    time_str = time_str.strip().upper().replace(".", "")
    try:
        if ":" in time_str:
            h, m = map(int, time_str.split(":"))
        else:
            h = int(time_str)
            m = 0
        if "PM" in time_str and h != 12:
            h += 12
        elif "AM" in time_str and h == 12:
            h = 0
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target < now:
            target += timedelta(days=1)
        return (target - now).total_seconds(), target.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None, None

def parse_relative_time(command: str):
    match = relative_pattern.search(command)
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2).lower()
    if "sec" in unit:
        return value
    elif "min" in unit:
        return value * 60
    elif "hour" in unit or "hr" in unit:
        return value * 3600
    return None

async def reminder_task(msg, delay, target_time_str):
    await asyncio.sleep(delay)
    print(f"[bold green]Reminder:[/bold green] {msg} (scheduled for {target_time_str})")

def load_reminders():
    if os.path.exists(REMINDER_FILE):
        with open(REMINDER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_reminders(data):
    with open(REMINDER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

async def Reminder(command: str):
    command_lower = command.lower()

    # LIST
    if any(kw in command_lower for kw in ["list all reminders", "tell me all reminders", "show all reminders"]):
        data = load_reminders()
        if not data:
            print("[yellow]No reminders found.[/yellow]")
        else:
            print("[bold blue]All Reminders:[/bold blue]")
            for i, r in enumerate(data, start=1):
                print(f"{i}. {r['message']} -> {r['time']}")
        return True

    # REMOVE
    if command_lower.startswith("remove"):
        message_to_remove = command[6:].strip()
        data = load_reminders()
        new_data = [r for r in data if r['message'] != message_to_remove]
        if len(new_data) < len(data):
            save_reminders(new_data)
            print(f"[yellow]Reminder removed:[/yellow] {message_to_remove}")
        else:
            print(f"[red]Reminder not found:[/red] {message_to_remove}")
        return True

    # ADD
    if command_lower.startswith("add"):
        part = command[3:].strip()
        delay_seconds = parse_relative_time(part)
        if delay_seconds is not None:
            target_time_str = (datetime.now() + timedelta(seconds=delay_seconds)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            match = time_pattern.search(part)
            if not match:
                print(f"[red]No valid time found in: {part}[/red]")
                return False
            time_str = match.group(0)
            delay_seconds, target_time_str = parse_time(time_str)
            if delay_seconds is None:
                print(f"[red]Failed to parse time: {time_str}[/red]")
                return False

        message = re.sub(r"reminder", "", part, flags=re.IGNORECASE)
        message = re.sub(relative_pattern, "", message).replace("at", "").replace("and", "").strip()

        task = asyncio.create_task(reminder_task(message, delay_seconds, target_time_str))
        reminders.append(task)

        data = load_reminders()
        data.append({"message": message, "time": target_time_str})
        save_reminders(data)
        print(f"[yellow]Reminder set for {target_time_str} -> {message}[/yellow]")
        return True

    print("[red]Invalid reminder command. Use add/remove/list.[/red]")
    return False

# ---------------- TIRED FUNCTION ---------------- #
async def Tired(_):
    favorite_songs = [
        "GUZAARISHEIN",
        "Main Rahoon",
        "Karde Karam Tu",
        "Afsanay",
        "Departune Lane",
        "Mileya Ni",
        "Jaadugar",
        "GAME SHURU",
        "Paardarshi",
        "Tu Hai Kahan"
    ]
    song = random.choice(favorite_songs)
    print(f"[bold green]You are tired. Playing your favorite song:[/bold green] {song}")
    await asyncio.to_thread(PlayYoutube, song)
    return True

# ---------------- WHATSAPP AUTOMATION ---------------- #

CONTACTS = {
    # Example
    "ChatGPT": "+1 (800) 242-8478"
}

def WhatsAppMsg(command: str):
    try:
        import pywhatkit as kit

        parts = command.strip().split(" ", 1)
        if len(parts) < 2:
            print("[red]Invalid format. Use: whatsapp <contact/number> <message>[/red]")
            return False

        target, message = parts
        target = target.lower().strip()

        # If target is a saved contact name, use its number
        phone = CONTACTS.get(target, target)

        # If it’s not a full international format, prepend country code
        if not phone.startswith("+"):
            phone = "+92" + phone  # change default country code if needed

        kit.sendwhatmsg_instantly(phone, message, wait_time=10, tab_close=False)
        print(f"[green]WhatsApp message sent to {target} ({phone}):[/green] {message}")
        return True

    except Exception as e:
        print(f"[red]WhatsApp sending failed: {e}[/red]")
        return False

# ---------------- COMMAND HANDLER ---------------- #
COMMANDS = {
    "open ": OpenApp,
    "close ": CloseApp,
    "play ": PlayYoutube,
    "content ": Content,
    "google search ": GoogleSearch,
    "youtube search ": YouTubeSearch,
    "system ": System,
    "reminder ": Reminder,
    "tired": Tired,
    "whatsapp": WhatsAppMsg,
    "github create ": lambda arg: create_repo(arg, private=False),
    "github create private ": lambda arg: create_repo(arg, private=True),
    "github delete ": lambda arg: delete_repo(arg, confirm=True),
    "github list": lambda _: list_repos(),
    "github find ": find_repo_by_name,
    "github open ": open_repo_in_browser,
    "github clone ": lambda arg: clone_repo(arg.split()[0], arg.split()[1]),
    "github commit ": lambda arg: git_commit(*arg.split(" ", 1)),
    "github push ": git_push,
    "github pull ": git_pull,
    "github branch create ": lambda arg: git_create_branch(*arg.split()),
    "github branch checkout ": lambda arg: git_checkout_branch(*arg.split()),
    "github search repo ": search_repos,
    "github search user ": search_users,
}

async def TranslateAndExecute(commands: list[str]):
    tasks = []
    for command in commands:
        for prefix, func in COMMANDS.items():
            if command.startswith(prefix):
                arg = command.removeprefix(prefix).strip()
                if asyncio.iscoroutinefunction(func):
                    tasks.append(func(arg))
                else:
                    tasks.append(asyncio.to_thread(func, arg))
                break
        else:
            print(f"[red]No Functions Found. For: {command}[/red]")

    return await asyncio.gather(*tasks)

async def Automation(commands: list[str]):
    await TranslateAndExecute(commands)
    return True

# ---------------- ASYNC INPUT ---------------- #
async def async_input(prompt: str = ""):
    return await asyncio.to_thread(input, prompt)

# ---------------- MAIN LOOP ---------------- #
if __name__ == "__main__":
    async def main():
        while True:
            query = await async_input("Enter Command: ")
            await Automation([query])

    asyncio.run(main())
