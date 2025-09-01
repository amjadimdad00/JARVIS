import tkinter as tk
from PIL import Image, ImageTk, ImageSequence, ImageDraw, ImageFont
import os
from datetime import datetime
import psutil
import socket
import subprocess
import cv2

def TempDirPath(filename):
    temp_dir = os.path.join(os.getcwd(), "Frontend", "Files")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    return os.path.join(temp_dir, filename)

def ShowTextToScreen(Text):
    """Write given text to Responses.data"""
    with open(TempDirPath("Responses.data"), 'w', encoding='utf-8') as f:
        f.write(Text)

def AnswerModifier(Answer):
    """Remove empty lines and extra spaces from answer"""
    lines = Answer.split('\n')
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def QueryModifier(Query):
    """Format query with proper capitalization and punctuation"""
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ['how','what','who','where','when','why','which','whom','can you',"what's", "where's","how's"]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.','?','!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.','?','!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()

def SetMicrophoneStatus(Command):
    with open(TempDirPath('Mic.data'), 'w', encoding='utf-8') as file:
        file.write(Command)
    
def GetMicrophoneStatus():
    try:
        with open(TempDirPath('Mic.data'), 'r', encoding='utf-8') as file:
            Status = file.read().strip()
        return Status
    except FileNotFoundError:
        return "OFF"

def SetAssistantStatus(Status):
    with open(TempDirPath('Status.data'), 'w', encoding='utf-8') as file:
        file.write(Status)

def GetAssistantStatus():
    with open(TempDirPath('Status.data'), 'r', encoding='utf-8') as file:
        Status = file.read()
    return Status

class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("J.A.R.V.I.S")
        self.root.configure(bg="black")
        self.root.attributes("-fullscreen", True)

        # Transparent color for chat panel (Windows only)
        self.root.wm_attributes("-transparentcolor", "#123456")

        # Hotkey binding for Alt+F4
        self.root.bind("<Alt-F4>", self.close_window)

        # Sizes
        self.gif_w, self.gif_h = 300, 300
        self.minimize_w, self.minimize_h = 200, 60
        self.chat_w, self.chat_h = 200, 60

        # Paths
        base_path = os.path.dirname(__file__)
        self.gif_path = os.path.join(base_path, "Graphics", "Jarvis.gif")
        self.border_path = os.path.join(base_path, "Graphics", "Border.png")
        self.usage_border_path = os.path.join(base_path, "Graphics", "Usage_Border.png")
        self.chat_border_path = os.path.join(base_path, "Graphics", "Chat_Border.png")
        self.font_path = os.path.join(base_path, "Fonts", "mw.ttf")

        # Fonts
        self.gif_font = ImageFont.truetype(self.font_path, 25)
        self.datetime_font = ImageFont.truetype(self.font_path, 18)
        self.usage_font = ImageFont.truetype(self.font_path, 16)
        self.network_font = ImageFont.truetype(self.font_path, 12)

        # Minimize Button
        self.create_minimize_button()

        # Chat Button
        self.create_chat_button()

        # Date/Time Label
        self.create_datetime_label()

        # GIF Animation
        self.load_gif_frames()
        self.container = tk.Frame(root, bg="black")
        self.container.pack(expand=True)
        self.gif_label = tk.Label(self.container, bg="black")
        self.gif_label.pack()
        self.animate_gif(0)

        # Usage Panel
        self.pre_render_numbers()
        self.create_usage_panel()

        # Video Panel
        self.create_video_panel()

    # ---------------- Close Window ----------------
    def close_window(self, event=None):
        self.root.destroy()

    # ---------------- Minimize Button ----------------
    def create_minimize_button(self):
        img = Image.open(self.border_path).convert("RGBA").resize((self.minimize_w, self.minimize_h))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(self.font_path, 20)
        text = "Minimize"
        bbox = draw.textbbox((0, 0), text, font=font)
        draw.text(((img.width - (bbox[2]-bbox[0]))//2, (img.height - (bbox[3]-bbox[1]))//2),
                  text, font=font, fill=(255,255,255,255))
        self.minimize_img = ImageTk.PhotoImage(img)
        self.minimize_button = tk.Label(self.root, image=self.minimize_img, bg="black", cursor="hand2")
        self.minimize_button.place(x=20, y=15)
        self.minimize_button.bind("<Button-1>", self.minimize_window)
        self.minimize_button.bind("<Button-3>", self.toggle_microphone)
    
    def toggle_microphone(self, event=None):
        current_status = GetMicrophoneStatus()
        if current_status.upper() == "ON":
            SetMicrophoneStatus("OFF")
            print("Microphone turned OFF")
        else:
            SetMicrophoneStatus("ON")
            print("Microphone turned ON")

    def minimize_window(self, event=None):
        self.root.withdraw()
        self.root.after(50, self.root.iconify)
        self.root.after(100, self.root.lower)

    # ---------------- Chat Button ----------------
    def create_chat_button(self):
        img = Image.open(self.border_path).convert("RGBA").resize((self.chat_w, self.chat_h))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(self.font_path, 20)
        text = "CHAT"
        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        draw.text(((img.width - (bbox[2]-bbox[0]) )//2, (img.height - (bbox[3]-bbox[1]))//2),
                text, font=font, fill=(255,255,255,255))
        self.chat_img = ImageTk.PhotoImage(img)
        self.chat_button = tk.Label(self.root, image=self.chat_img, bg="black", cursor="hand2")
        self.chat_button.place(x=(self.root.winfo_screenwidth()-self.chat_w)//2, y=15)
        self.chat_button.lift()
        self.chat_button.bind("<Button-1>", self.open_chat_window)

    # ---------------- Mousewheel ----------------
    def _on_mousewheel(self, event):
        self.msg_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # ---------------- Chat Window ----------------
    def open_chat_window(self, event=None):
        self.chat_frame = tk.Frame(self.root, bg="black")
        self.chat_frame.place(x=0, y=0, relwidth=1, relheight=1)
        
        # ---------------- Home Button ----------------
        img = Image.open(self.border_path).convert("RGBA").resize((200, 60))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(self.font_path, 20)
        text = "HOME"
        bbox = draw.textbbox((0,0), text, font=font)
        draw.text(
            ((img.width - (bbox[2]-bbox[0])) // 2, (img.height - (bbox[3]-bbox[1])) // 2),
            text, font=font, fill=(255,255,255,255)
        )
        self.home_img = ImageTk.PhotoImage(img)
        self.home_button = tk.Label(self.chat_frame, image=self.home_img, bg="black", cursor="hand2")
        self.home_button.place(relx=0.5015, y=15, anchor="n")
        self.home_button.bind("<Button-1>", self.close_chat_window)

        # ---------------- Scrollable Messages ----------------
        self.msg_canvas = tk.Canvas(self.chat_frame, bg="black", highlightthickness=0)
        self.msg_canvas.place(relx=0.5, rely=0.15, anchor="n", width=800, height=500)

        self.msg_frame = tk.Frame(self.msg_canvas, bg="black")
        self.msg_window = self.msg_canvas.create_window((0,0), window=self.msg_frame, anchor="nw")

        # Mousewheel scroll
        self.msg_canvas.bind("<Enter>", lambda e: self.msg_canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.msg_canvas.bind("<Leave>", lambda e: self.msg_canvas.unbind_all("<MouseWheel>"))
        self.msg_frame.bind("<Configure>", lambda e: self.msg_canvas.configure(scrollregion=self.msg_canvas.bbox("all")))

        # ---------------- Messages List ----------------
        self.messages = []

        # Start loading messages from file periodically
        self.load_messages()
    
    def load_messages(self):
        """Load messages from Database.data and display in chat"""
        try:
            with open(TempDirPath("Database.data"), 'r', encoding='utf-8') as f:
                messages = f.read().strip()
            if messages and (not hasattr(self, 'messages') or not self.messages or messages != self.messages[-1]):
                self.add_message(AnswerModifier(messages))
                if not hasattr(self, 'messages'):
                    self.messages = []
                self.messages.append(messages)
        except FileNotFoundError:
            pass
        self.root.after(500, self.load_messages)

    # ---------------- Add Message ----------------
    def add_message(self, msg):
        label = tk.Label(self.msg_frame, text=f"{msg}", font=("Consolas",12),
                        fg="white", bg="black", wraplength=780, justify="left")
        label.pack(anchor="w", pady=2)
        self.msg_canvas.update_idletasks()
        self.msg_canvas.yview_moveto(1)

    # ---------------- Close Chat Window ----------------
    def close_chat_window(self, event=None):
        self.chat_frame.destroy()

    # ---------------- Date/Time ----------------
    def create_datetime_label(self):
        self.datetime_base_img = Image.open(self.border_path).convert("RGBA").resize((self.minimize_w, self.minimize_h))
        self.datetime_img = ImageTk.PhotoImage(self.datetime_base_img)
        self.datetime_label = tk.Label(self.root, image=self.datetime_img, bg="black")
        self.datetime_label.place(x=self.root.winfo_screenwidth() - self.minimize_w - 20, y=15)
        self.update_datetime()

    def update_datetime(self):
        img = self.datetime_base_img.copy()
        draw = ImageDraw.Draw(img)
        now = datetime.now()
        date_str = now.strftime("%d %b %Y")
        time_str = now.strftime("%I:%M:%S %p")
        bbox_date = draw.textbbox((0,0), date_str, font=self.datetime_font)
        bbox_time = draw.textbbox((0,0), time_str, font=self.datetime_font)
        draw.text(((img.width - (bbox_date[2]-bbox_date[0]))//2, 15), date_str,
                  font=self.datetime_font, fill=(255,255,255,255))
        draw.text(((img.width - (bbox_time[2]-bbox_time[0]))//2, 30), time_str,
                  font=self.datetime_font, fill=(255,255,255,255))
        self.datetime_img = ImageTk.PhotoImage(img)
        self.datetime_label.configure(image=self.datetime_img)
        self.root.after(1000, self.update_datetime)

    # ---------------- GIF Animation ----------------
    def load_gif_frames(self):
        gif = Image.open(self.gif_path)
        self.gif_frames = []
        for frame in ImageSequence.Iterator(gif):
            f = frame.convert("RGBA").resize((self.gif_w, self.gif_h))
            draw = ImageDraw.Draw(f)
            bbox = draw.textbbox((0, 0), "J.A.R.V.I.S", font=self.gif_font)
            draw.text(((self.gif_w - (bbox[2]-bbox[0]))//2, (self.gif_h - (bbox[3]-bbox[1]))//2),
                      "J.A.R.V.I.S", font=self.gif_font, fill=(255,255,255,255))
            self.gif_frames.append(ImageTk.PhotoImage(f))
        self.gif_frame_count = len(self.gif_frames)

    def animate_gif(self, index):
        self.gif_label.configure(image=self.gif_frames[index])
        index = (index + 1) % self.gif_frame_count
        self.root.after(30, self.animate_gif, index)

    # ---------------- Pre-render numbers ----------------
    def pre_render_numbers(self):
        self.number_images = {}
        self.number_width, self.number_height = 50, 30
        for i in range(0, 101):
            img = Image.new("RGBA", (self.number_width, self.number_height), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            draw.text((0,0), f"{i:02d}%", font=self.usage_font, fill=(255,255,255,255))
            self.number_images[i] = ImageTk.PhotoImage(img)

    def pre_render_text(self, text, max_width=180):
        img = Image.new("RGBA", (max_width, 20), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.text((0,0), text, font=self.network_font, fill=(255,255,255,255))
        return ImageTk.PhotoImage(img)

    # ---------------- Usage Panel ----------------
    def create_usage_panel(self, width=380, height=200):
        base_img = Image.open(self.usage_border_path).convert("RGBA").resize((width, height))
        self.usage_base_img = ImageTk.PhotoImage(base_img)
        self.usage_canvas = tk.Canvas(self.root, width=width, height=height, bg="black", highlightthickness=0)
        screen_height = self.root.winfo_screenheight()
        self.usage_canvas.place(x=0, y=screen_height - height - 10)
        self.usage_canvas.create_image(0, 0, anchor="nw", image=self.usage_base_img)

        self.cpu_img_id = self.usage_canvas.create_image(120, 70, anchor="center", image=self.number_images[0])
        self.disk_img_id = self.usage_canvas.create_image(275, 70, anchor="center", image=self.number_images[0])
        self.ram_img_id = self.usage_canvas.create_image(115, 150, anchor="center", image=self.number_images[0])

        ssid = self.get_ssid()
        self.ssid_img = self.pre_render_text(f"{ssid}")
        self.ssid_img_id = self.usage_canvas.create_image(285, 140, anchor="center", image=self.ssid_img)

        ip = self.get_ip()
        self.ip_img = self.pre_render_text(f"{ip}")
        self.ip_img_id = self.usage_canvas.create_image(310, 155, anchor="center", image=self.ip_img)

        self.update_usage()

    def get_ssid(self):
        try:
            result = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], shell=True).decode("utf-8")
            for line in result.split("\n"):
                if "SSID" in line and "BSSID" not in line:
                    return line.split(":", 1)[1].strip()
        except:
            return "N/A"
        return "N/A"

    def get_ip(self):
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "N/A"

    def update_usage(self):
        cpu = int(psutil.cpu_percent())
        ram = int(psutil.virtual_memory().percent)
        disk = int(psutil.disk_usage('/').percent)

        self.usage_canvas.itemconfigure(self.cpu_img_id, image=self.number_images[cpu])
        self.usage_canvas.itemconfigure(self.disk_img_id, image=self.number_images[disk])
        self.usage_canvas.itemconfigure(self.ram_img_id, image=self.number_images[ram])

        self.root.after(1000, self.update_usage)

    # ---------------- IronMan Hologram ----------------
    def create_video_panel(self, width=600, height=320):
        base_path = os.path.dirname(__file__)
        self.video_path = os.path.join(base_path, ".", "Graphics", "IronMan.mp4")
        self.video_path = os.path.abspath(self.video_path)

        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            print("Error: Cannot open video file:", self.video_path)
            return

        self.video_canvas = tk.Canvas(self.root, width=width, height=height, bg="black", highlightthickness=0)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.video_canvas.place(x=screen_width - width - -150, y=screen_height - height)

        # Create initial image
        self.video_img = ImageTk.PhotoImage(Image.new("RGB", (width, height)))
        self.video_img_id = self.video_canvas.create_image(0, 0, anchor="nw", image=self.video_img)

        # Delay update to allow canvas to render properly
        self.root.after(50, self.update_video_frame)

    def update_video_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret:
                return  # Could not read video

        # Resize to canvas size
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        canvas_width = self.video_canvas.winfo_width()
        canvas_height = self.video_canvas.winfo_height()
        frame = cv2.resize(frame, (canvas_width, canvas_height))

        self.video_img = ImageTk.PhotoImage(Image.fromarray(frame))
        self.video_canvas.itemconfigure(self.video_img_id, image=self.video_img)

        self.root.after(30, self.update_video_frame)

def GraphicalUserInterface():
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()

if __name__ == "__main__":
    GraphicalUserInterface()
