import cohere
from rich import print
from dotenv import dotenv_values

# ========== SETUP ==========
env_vars = dotenv_values(".env")
co = cohere.Client(env_vars.get("CohereAPIKey"))

funcs = {
    "exit", "general", "realtime", "open", "close", 
    "play", "generate image", "system", "content",
    "google search", "youtube search", "reminder",
    "tired", "whatsapp",
}

preamble = """
You are a very accurate Decision-Making Model, which decides what kind of a query is given to you.
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation like 'open facebook, instagram', 'can you write a application and open it in notepad'
*** Do not answer any query, just decide what kind of query is given to you. ***

-> Respond with 'general ( query )' if a query can be answered by a llm model (conversational ai chatbot) and doesn't require any up to date information.
-> Respond with 'realtime ( query )' if a query requires up to date information or is about a known person/entity.
-> Respond with 'open (application name)' if a query is asking to open any application.
-> Respond with 'close (application name)' if a query is asking to close any application.
-> Respond with 'play (song name)' if a query is asking to play any song.
-> Respond with 'generate image (image prompt)' if a query is requesting to generate an image.
-> Respond with 'reminder (datetime with message)' if a query is requesting to set a reminder.
-> Respond with 'system (task name)' if a query is asking to mute, unmute, volume up, etc.
-> Respond with 'content (topic)' if a query is asking to write any type of content.
-> Respond with 'google search (topic)' if a query is asking to search something on Google.
-> Respond with 'youtube search (topic)' if a query is asking to search something on YouTube.
-> If the query is asking multiple tasks, respond with them separated by commas.
-> If the user says goodbye, respond with 'exit'.
-> If you can't decide, respond with 'general (query)'.

Examples:
User: How are you?
Chatbot: general How are you?
User: open chrome and firefox
Chatbot: open chrome, open firefox
User: what's today's date?
Chatbot: general what's today's date?
User: bye jarvis
Chatbot: exit
"""

# ========== HELPERS ==========
def parse_response(raw: str) -> list[str]:
    """Clean and filter Cohere's response into valid tasks"""
    return [
        task.strip()
        for task in raw.replace("\n", " ").split(",")
        if any(task.strip().startswith(func) for func in funcs)
    ]

def FirstLayerDMM(prompt: str) -> list[str]:
    """Classify the query into a task type, with special handling for 'tired'"""
    
    # Special keyword check
    if "tired" in prompt.lower():
        return ["tired"]
    
    stream = co.chat_stream(
        model="command-r-plus",
        message=prompt,
        temperature=0.0,   # deterministic classification
        connectors=[],
        preamble=preamble,
    )

    response = "".join(
        event.text for event in stream if event.event_type == "text-generation"
    )

    tasks = parse_response(response)
    
    if not tasks:
        return [f"general {prompt}"]   # fallback
    
    return tasks

# ========== MAIN LOOP ==========
if __name__ == "__main__":
    while True:
        query = input("You: ")
        if not query.strip():
            continue
        print(FirstLayerDMM(query))
