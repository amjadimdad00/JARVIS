import os
import time
from dotenv import dotenv_values
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import mtranslate as mt

# ------------------- Load Environment Variables -------------------
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage", "en")

# ------------------- Paths -------------------
current_dir = os.getcwd()
data_dir = os.path.join(current_dir, "Data")
os.makedirs(data_dir, exist_ok=True)
html_path = os.path.join(data_dir, "Voice.html")

temp_dir = os.path.join(current_dir, "Frontend", "Files")
os.makedirs(temp_dir, exist_ok=True)
status_file = os.path.join(temp_dir, "Status.data")

# ------------------- HTML Template -------------------
html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {{
            recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = '{InputLanguage}';
            recognition.continuous = true;

            recognition.onresult = function(event) {{
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            }};

            recognition.onend = function() {{
                recognition.start();
            }};
            recognition.start();
        }}

        function stopRecognition() {{
            recognition.stop();
            output.innerHTML = "";
        }}
    </script>
</body>
</html>'''

# ------------------- Write HTML Once -------------------
if not os.path.exists(html_path):
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_template)

link = f"file:///{html_path}"

# ------------------- Chrome Options -------------------
chrome_options = Options()
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36"
)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# ------------------- Helper Functions -------------------
def SetAssistantStatus(Status: str):
    with open(status_file, "w", encoding="utf-8") as f:
        f.write(Status)

question_words = {"how","what","who","where","when","why","which","whose","whom","can you","what's","where's","how's"}

def QueryModifier(Query: str) -> str:
    new_query = Query.strip().lower()
    last_char = new_query[-1] if new_query else ""
    if any(q in new_query for q in question_words):
        new_query = new_query.rstrip(".!?") + "?"
    else:
        new_query = new_query.rstrip(".!?") + "."
    return new_query.capitalize()

def UniversalTranslate(Text: str) -> str:
    translated = mt.translate(Text, "en", "auto")
    return translated.capitalize()

# ------------------- Speech Recognition -------------------
def SpeechRecognition():
    driver.get(link)

    # Cache element references for speed
    try:
        start_btn = driver.find_element(By.ID, "start")
        end_btn = driver.find_element(By.ID, "end")
        output_elem = driver.find_element(By.ID, "output")
    except Exception as e:
        print("Error initializing elements:", e)
        return None

    start_btn.click()

    while True:
        try:
            text = output_elem.text
            if text:
                end_btn.click()

                if InputLanguage.lower().startswith("en"):
                    return QueryModifier(text)
                else:
                    SetAssistantStatus("Translating")
                    return QueryModifier(UniversalTranslate(text))
            else:
                time.sleep(0.1)  # small sleep to reduce CPU usage
        except Exception as e:
            # Log exception but keep looping
            print(f"Recognition loop error: {e}")
            time.sleep(0.1)

# ------------------- Main Loop -------------------
if __name__ == "__main__":
    while True:
        result_text = SpeechRecognition()
        if result_text:
            print(result_text)
