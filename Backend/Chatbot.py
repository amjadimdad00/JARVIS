import datetime
from groq import Groq
from json import load, dump
from dotenv import dotenv_values

# Config
env_vars = dotenv_values(".env")
USERNAME = env_vars["Username"]
ASSISTANTNAME = env_vars["Assistantname"]
GROQ_API_KEY = env_vars["GroqAPIKey"]
MODEL_NAME = "llama3-70b-8192"
MAX_HISTORY = 20

client = Groq(api_key=GROQ_API_KEY)

System = f"""You are {ASSISTANTNAME}, a highly accurate and advanced AI assistant. 
Your user's name is {USERNAME}. You have real-time information from the internet.

**Important Rules:**
1. Only tell the current time or date if the user asks about time or date directly.
2. Reply in English only.
3. Just answer the question.
4. Always answer in a professional manner, with proper grammar, punctuation, and clarity.
5. Be concise but informative.
6. Address me as "Sir".
6. Personality: Formal, witty, precise (Jarvis-like tone).
7. If there is uncertainty or missing data, state it clearly without guessing.
8. Do NOT fabricate links, titles, or facts.
9. Reply only in English.
10. Stay helpful and factual, no unnecessary roleplay.
11. Do NOT use markdown formatting like *, _, or `
"""

SystemChatBot = [{"role": "system", "content": System}]

# Load chat history once
try:
    with open(r"Data\ChatLog.json","r") as f:
        messages = load(f)
except FileNotFoundError:
    messages = []
    with open(r"Data\ChatLog.json","w") as f:
        dump(messages, f)

def RealtimeInformation():
    now = datetime.datetime.now()
    return (f"Day: {now.strftime('%A')}\nDate: {now.strftime('%d %B %Y')}\n"
            f"Time: {now.strftime('%I:%M:%S %p')}")

def AnswerModifier(answer):
    return '\n'.join(line for line in answer.split('\n') if line.strip())

def get_recent_history(messages):
    return messages[-MAX_HISTORY:]

def ChatBot(query, retries=2):
    global messages
    try:
        messages.append({"role": "user", "content": query})

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + get_recent_history(messages),
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True,
        )

        chunks = []
        for chunk in completion:
            if chunk.choices[0].delta.content:
                chunks.append(chunk.choices[0].delta.content)

        Answer = ''.join(chunks).replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})

        with open(r"Data\ChatLog.json","w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer)

    except Exception as e:
        if retries > 0:
            return ChatBot(query, retries-1)
        raise e

if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        print(ChatBot(user_input))
