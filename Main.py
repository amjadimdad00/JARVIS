from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus,
)
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os
import atexit
from typing import List

# -------------------------
# Env & Defaults
# -------------------------

env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

DefaultMessage = f""" {Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}. I am doing well. How may I help you? """

functions = ["open", "close", "play", "system", "content","google search",
             "youtube search", "tired", "whatsapp", "github create ",
             "github create private ", "github delete ", "github list", 
             "github find ", "github open ", "github clone ", "github commit ",
             "github push ", "github pull ", "github branch create ",
             "github branch checkout ", "github search repo ", "github search user "
]

# -------------------------
# Helpers: I/O caching & status
# -------------------------

_chat_cache: List[dict] | None = None
_last_status: str | None = None

def SafeSetAssistantStatus(status: str) -> None:
    """Avoid redundant GUI updates by setting only when the value changes."""
    global _last_status
    if status != _last_status:
        try:
            SetAssistantStatus(status)
            _last_status = status
        except Exception:
            pass

def write_if_changed(filepath: str, new_content: str) -> None:
    """Write to file only if content differs."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            if f.read() == new_content:
                return
    except FileNotFoundError:
        # No existing file; proceed to write
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

# -------------------------
# Subprocess lifecycle
# -------------------------

subprocess_list: List[subprocess.Popen] = []

def CleanupSubprocesses():
    # Terminate any still-running child processes on exit
    for proc in list(subprocess_list):
        try:
            if proc.poll() is None:
                proc.terminate()
        except Exception:
            pass

def spawn_process(cmd: List[str]) -> subprocess.Popen:
    """Spawn a process and keep the list pruned of finished procs."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    subprocess_list.append(proc)
    # Prune finished
    alive = []
    for p in subprocess_list:
        try:
            if p.poll() is None:
                alive.append(p)
        except Exception:
            pass
    subprocess_list[:] = alive
    return proc

atexit.register(CleanupSubprocesses)

# -------------------------
# Chat log utils (with caching)
# -------------------------

def ShowDefaultChatIfNoChats() -> None:
    """Ensure minimal default artifacts exist to boot the UI."""
    try:
        with open(r"Data\ChatLog.json", "r", encoding="utf-8") as file:
            data = file.read()
            if len(data) < 5:
                os.makedirs(os.path.dirname(TempDirPath("Database.data")), exist_ok=True)
                write_if_changed(TempDirPath("Database.data"), "")
                write_if_changed(TempDirPath("Responses.data"), DefaultMessage)
    except FileNotFoundError:
        print("ChatLog.json file not found. Creating default response.")
        os.makedirs("Data", exist_ok=True)
        with open(r"Data\ChatLog.json", "w", encoding="utf-8") as file:
            file.write("[]")
        os.makedirs(os.path.dirname(TempDirPath("Responses.data")), exist_ok=True)
        write_if_changed(TempDirPath("Responses.data"), DefaultMessage)

def ReadChatLogJson() -> List[dict]:
    global _chat_cache
    if _chat_cache is not None:
        return _chat_cache
    try:
        with open(r"Data\ChatLog.json", "r", encoding="utf-8") as file:
            _chat_cache = json.load(file)
            return _chat_cache
    except FileNotFoundError:
        print("ChatLog.json not found.")
        _chat_cache = []
        return _chat_cache

def ChatLogIntegration() -> None:
    json_data = ReadChatLogJson()
    formatted_chatlog = "".join(
        f"{Username}: {entry['content']}\n" if entry.get("role") == "user" else f"{Assistantname}: {entry.get('content','')}\n"
        for entry in json_data
    )
    os.makedirs(os.path.dirname(TempDirPath("Database.data")), exist_ok=True)
    write_if_changed(TempDirPath("Database.data"), AnswerModifier(formatted_chatlog))

def ShowChatOnGUI() -> None:
    try:
        with open(TempDirPath("Database.data"), "r", encoding="utf-8") as file:
            data = file.read()
        if data:
            write_if_changed(TempDirPath("Responses.data"), data)
    except FileNotFoundError:
        print("Database.data file not found.")

# -------------------------
# Speech & TTS utilities
# -------------------------

def speak_async(text: str) -> None:
    threading.Thread(target=_safe_tts, args=(text,), daemon=True).start()

def _safe_tts(text: str) -> None:
    try:
        TextToSpeech(text)
    except Exception as e:
        print(f"TextToSpeech failed: {e}")

# -------------------------
# Initial setup
# -------------------------

def InitialExecution() -> None:
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatOnGUI()

# -------------------------
# Main execution logic
# -------------------------

def MainExecution() -> bool:
    try:
        TaskExecution = False
        ImageExecution = False
        ImageGenerationQuery = ""

        SafeSetAssistantStatus("Listening...")
        try:
            Query = SpeechRecognition()
        except Exception as e:
            print(f"SpeechRecognition failed: {e}")
            Query = ""

        ShowTextToScreen(f"{Username}: {Query}")
        SafeSetAssistantStatus("Thinking...")
        try:
            Decision = FirstLayerDMM(Query)
        except Exception as e:
            print(f"FirstLayerDMM failed: {e}")
            Decision = []

        print(f"\nDecision: {Decision}\n")

        G = any(i for i in Decision if i.startswith("general"))
        R = any(i for i in Decision if i.startswith("realtime"))

        Merged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
        )

        for q in Decision:
            if "generate" in q:
                ImageGenerationQuery = str(q)
                ImageExecution = True
                break

        # Execute automations (only once per cycle)
        for q in Decision:
            if not TaskExecution and any(q.startswith(func) for func in functions):
                try:
                    run(Automation(list(Decision)))
                    TaskExecution = True
                except Exception as e:
                    print(f"Automation failed: {e}")

        # Kick off image generation if needed
        if ImageExecution:
            try:
                os.makedirs(os.path.dirname(r"Frontend\Files\ImageGeneration.data"), exist_ok=True)
                with open(r"Frontend\Files\ImageGeneration.data", "w", encoding="utf-8") as file:
                    file.write(f"{ImageGenerationQuery},True")
                spawn_process(['python', r"Backend\ImageGeneration.py"])
            except Exception as e:
                print(f"Error starting ImageGeneration.py: {e}")

        # Handle general + realtime answers
        if (G and R) or R:
            SafeSetAssistantStatus("Searching...")
            try:
                Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
            except Exception as e:
                Answer = "Error fetching realtime response."
                print(f"RealtimeSearchEngine failed: {e}")
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            SafeSetAssistantStatus("Answering...")
            speak_async(Answer)
            return True
        else:
            for q in Decision:
                QueryFinal = q.replace("general", "").replace("realtime", "")
                if "general" in q:
                    SafeSetAssistantStatus("Thinking...")
                    try:
                        Answer = ChatBot(QueryModifier(QueryFinal))
                    except Exception as e:
                        Answer = "Error generating response."
                        print(f"ChatBot failed: {e}")
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SafeSetAssistantStatus("Answering...")
                    speak_async(Answer)
                    return True
                elif "realtime" in q:
                    SafeSetAssistantStatus("Searching...")
                    try:
                        Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                    except Exception as e:
                        Answer = "Error fetching realtime response."
                        print(f"RealtimeSearchEngine failed: {e}")
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SafeSetAssistantStatus("Answering...")
                    speak_async(Answer)
                    return True
                elif "exit" in q:
                    QueryFinal = "Okay, Bye!"
                    try:
                        Answer = ChatBot(QueryModifier(QueryFinal))
                    except Exception:
                        Answer = QueryFinal
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SafeSetAssistantStatus("Answering...")
                    speak_async(Answer)
                    os._exit(1)
    except Exception as e:
        print(f"Error in MainExecution: {e}")
    return False

# -------------------------
# Threads
# -------------------------

def FirstThread() -> None:
    valid_on = {"true", "on", "1"}
    valid_off = {"false", "off", "0"}

    while True:
        try:
            CurrentStatus = GetMicrophoneStatus().lower().strip()

            if CurrentStatus in valid_on:
                MainExecution()
                # Active polling should be snappy but not hot
                sleep(0.2)
            elif CurrentStatus in valid_off:
                AIStatus = GetAssistantStatus()
                if "Available..." not in AIStatus:
                    SafeSetAssistantStatus("Available...")
                # Relax when idle
                sleep(1.0)
            else:
                # Unexpected value -> reset and slow down a bit
                SetMicrophoneStatus("False")
                sleep(0.8)

        except Exception as e:
            print(f"Error in FirstThread: {e}")
            sleep(1.0)  # prevent rapid CPU spin on errors

def SecondThread() -> None:
    try:
        GraphicalUserInterface()
    except Exception as e:
        print(f"Error in GUI thread: {e}")

# -------------------------
# Entry point
# -------------------------

if __name__ == "__main__":
    InitialExecution()

    thread1 = threading.Thread(target=FirstThread, daemon=True)
    thread1.start()
    SecondThread()
