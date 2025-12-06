# Copyright (c) 2025 contralious
# Licensed under the GNU General Public License v3.0
# See the LICENSE file for details.

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageGrab
import pytesseract
import cv2
import numpy as np
import requests
import threading
import re
import json
import time
import os
import sys
import random
import math
from io import BytesIO


DISCORD_WEBHOOK_URL = "x" 
CONFIG_FILE = "config.json"


def get_tesseract_cmd():
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, "Tesseract-OCR", "tesseract.exe")
    
    local_tess = os.path.join(os.getcwd(), "Tesseract-OCR", "tesseract.exe")
    if os.path.exists(local_tess):
        return local_tess
        
    paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        os.path.join(os.getenv('LOCALAPPDATA'), 'Tesseract-OCR', 'tesseract.exe')
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

pytesseract.pytesseract.tesseract_cmd = get_tesseract_cmd()

def load_webhook():
    global DISCORD_WEBHOOK_URL
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                val = data.get("webhook", "")
                if val: DISCORD_WEBHOOK_URL = val
        except: pass

def save_webhook(url):
    global DISCORD_WEBHOOK_URL
    DISCORD_WEBHOOK_URL = url
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"webhook": url}, f)
    except: pass

load_webhook()

COLORS = {
    "bg": "#18181b",
    "card": "#18181b",
    "panel": "#27272a",
    "text": "#f4f4f5",
    "subtext": "#a1a1aa",
    "accent": "#fafafa",
    "accent_hover": "#d4d4d8",
    "border": "#3f3f46",
    "danger": "#f87171",
    "success": "#4ade80",
    "transparent": "#000001"
}

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class SnippingTool(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.attributes('-fullscreen', True)
        self.attributes('-alpha', 0.3)
        self.attributes('-topmost', True)
        self.configure(bg='black', cursor="crosshair")
        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.start_x = None; self.start_y = None; self.rect = None
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Escape>", lambda e: self.destroy())

    def on_press(self, event):
        self.start_x = event.x; self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="white", width=2)

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        x1 = min(self.start_x, event.x); y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x); y2 = max(self.start_y, event.y)
        if abs(x2-x1) < 5 or abs(y2-y1) < 5: self.destroy(); return
        self.destroy()
        self.parent.withdraw()
        time.sleep(0.2)
        try:
            img = ImageGrab.grab((x1, y1, x2, y2))
            self.parent.deiconify()
            self.callback(img)
        except: self.parent.deiconify()

class StormOverlay(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VORTEX")
        self.width = 360
        self.height = 240
        self.geometry(f"{self.width}x{self.height}")
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.configure(fg_color=COLORS["transparent"])
        self.attributes('-transparentcolor', COLORS["transparent"])
        self.attributes('-alpha', 0.0)

        self.thermo_img = None
        self.comp_img = None
        self.extracted_data = {}
        self.report_box = None # Initialize placeholder

        self.canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.stars = []
        self.comets = []
        self.mouse_x = -500
        self.mouse_y = -500

        for _ in range(120):
            x = random.randint(0, 500)
            y = random.randint(0, 800)
            size = random.uniform(0.5, 2.0)
            alpha = random.uniform(0.2, 0.9)
            pulse_speed = random.uniform(0.005, 0.02) * random.choice([-1, 1])
            color = self._hex(int(30 + (alpha * 225)))
            sid = self.canvas.create_oval(x, y, x+size, y+size, fill=color, outline="", tags="star")
            self.stars.append([sid, alpha, pulse_speed])

        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)

        self.animate()
        self.show_landing()
        self.animate_fade_in()
        self.after(1000, self.check_webhook)

    def _hex(self, val):
        val = max(0, min(255, int(val)))
        return f"#{val:02x}{val:02x}{val:02x}"

    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def animate(self):
        # Safety check if widget destroyed
        try:
            w = self.winfo_width()
            h = self.winfo_height()
        except: return 

        self.canvas.delete("bg_anim")

        radius = 25
        steps = 5
        base = 39
        for i in range(steps):
            r = radius * (1 - (i/steps))
            intensity = base + (50 * (i/steps))
            col = self._hex(intensity)
            self.canvas.create_oval(
                self.mouse_x - r, self.mouse_y - r,
                self.mouse_x + r, self.mouse_y + r,
                fill=col, outline="", tags="bg_anim"
            )

        for s in self.stars:
            sid, alpha, speed = s
            alpha += speed
            if alpha >= 1.0:
                alpha = 1.0
                speed = -abs(speed)
            elif alpha <= 0.15:
                alpha = 0.15
                speed = abs(speed)
            s[1] = alpha
            s[2] = speed
            val = int(30 + (alpha * 225))
            self.canvas.itemconfig(sid, fill=self._hex(val))
        self.canvas.tag_lower("star")

        if random.random() < 0.015:
            sx = random.choice([0, w])
            sy = random.randint(0, h//2)
            ex = w if sx == 0 else 0
            ey = sy + random.randint(50, 200)
            vx = (ex - sx) / 60; vy = (ey - sy) / 60
            self.comets.append([None, sx, sy, vx, vy, 60])

        for c in self.comets[:]:
            cid, x, y, vx, vy, life = c
            x += vx; y += vy
            self.canvas.create_line(x, y, x-(vx*10), y-(vy*10), fill="#e4e4e7", width=1, tags="bg_anim")
            c[1] = x; c[2] = y; c[5] -= 1
            if c[5] <= 0: self.comets.remove(c)

        self.canvas.tag_lower("bg_anim")
        self.canvas.tag_lower("star")
        self.after(16, self.animate)

    def start_move(self, event): self.x, self.y = event.x, event.y
    def do_move(self, event): self.geometry(f"+{self.winfo_x() + event.x - self.x}+{self.winfo_y() + event.y - self.y}")

    def smooth_transition(self, target_w, target_h):
        cx = self.winfo_x() + (self.width / 2)
        cy = self.winfo_y() + (self.height / 2)
        start_w, start_h = self.width, self.height
        start_time = time.time()
        duration = 0.6
        self.attributes('-alpha', 0.95)

        def _step():
            elapsed = time.time() - start_time
            progress = elapsed / duration
            if progress >= 1:
                self.geometry(f"{target_w}x{target_h}+{int(cx - target_w/2)}+{int(cy - target_h/2)}")
                self.width, self.height = target_w, target_h
                self.attributes('-alpha', 1.0)
                return
            ease = 1 - math.pow(1 - progress, 3)
            new_w = int(start_w + (target_w - start_w) * ease)
            new_h = int(start_h + (target_h - start_h) * ease)
            new_x = int(cx - (new_w / 2))
            new_y = int(cy - (new_h / 2))
            self.geometry(f"{new_w}x{new_h}+{new_x}+{new_y}")
            self.width, self.height = new_w, new_h
            self.after(10, _step)
        _step()

    def run_ocr(self):
        try:
            t_start = time.time()
            txt_t = pytesseract.image_to_string(self.preprocess(self.thermo_img), config='--psm 6')
            txt_c = pytesseract.image_to_string(self.preprocess(self.comp_img), config='--psm 6')
            self.parse_data(txt_t + "\n" + txt_c)
            elapsed = time.time() - t_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            self.after(0, self.show_verify)
        except Exception as e:
            print(e)
            self.after(0, lambda: messagebox.showerror("Error", f"OCR Failed: {e}"))
            self.after(0, lambda: self.btn_go.configure(text="Process", state="normal"))

    def animate_fade_in(self):
        current_alpha = 0.0
        def _fade():
            nonlocal current_alpha
            current_alpha += 0.05
            if current_alpha >= 1.0:
                self.attributes('-alpha', 1.0)
                return
            self.attributes('-alpha', current_alpha)
            self.after(16, _fade)
        _fade()

    def clear_ui(self):
        for child in self.canvas.winfo_children():
            child.destroy()
        self.canvas.delete("ui")

    def check_webhook(self):
        global DISCORD_WEBHOOK_URL
        if not DISCORD_WEBHOOK_URL:
             # Just a console warning if missing, allows running without it
             print("Warning: Webhook not set.")

    def show_landing(self):
        self.clear_ui()
        self.smooth_transition(360, 240)
        self.canvas.create_text(20, 20, text="VORTEX // ENGINE", font=("Helvetica", 10, "bold"), fill=COLORS["subtext"], anchor="nw", tags="ui")
        btn_close = ctk.CTkButton(self.canvas, text="✕", width=20, height=20, corner_radius=10,
                                  fg_color="transparent", text_color=COLORS["subtext"],
                                  hover_color=COLORS["danger"], command=self.destroy)
        self.canvas.create_window(340, 20, window=btn_close, tags="ui")
        self.canvas.create_text(180, 90, text="VORTEX", font=("Helvetica", 28, "bold"), fill="white", anchor="center", tags="ui")
        self.canvas.create_text(180, 118, text="zzzz...", font=("Helvetica", 11), fill=COLORS["subtext"], anchor="center", tags="ui")
        
        # grid
        button_frame = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self.canvas.create_window(180, 155, window=button_frame, tags="ui")
        
        self.btn_t = ctk.CTkButton(button_frame, text="Thermodynamics", width=110, height=35, corner_radius=18,
                                   fg_color="transparent", border_width=1, border_color=COLORS["subtext"], text_color=COLORS["text"],
                                   hover_color=COLORS["panel"], command=lambda: SnippingTool(self, self.handle_thermo))
        self.btn_t.grid(row=0, column=0, padx=5)

        self.btn_c = ctk.CTkButton(button_frame, text="Composites", width=110, height=35, corner_radius=18,
                                   fg_color="transparent", border_width=1, border_color=COLORS["subtext"], text_color=COLORS["text"],
                                   hover_color=COLORS["panel"], command=lambda: SnippingTool(self, self.handle_comp))
        self.btn_c.grid(row=0, column=1, padx=5)

        self.btn_go = ctk.CTkButton(self.canvas, text="PROCESS", width=170, height=40, corner_radius=20,
                                    fg_color=COLORS["accent"], text_color="#1a1a1a", hover_color=COLORS["accent_hover"],
                                    state="disabled", font=("Helvetica", 13, "bold"),
                                    command=self.start_ocr)
        self.canvas.create_window(180, 205, window=self.btn_go, tags="ui")

    def handle_thermo(self, img):
        self.thermo_img = img
        self.btn_t.configure(fg_color=COLORS["accent"], text_color="black", border_color=COLORS["accent"])
        self.check_ready()

    def handle_comp(self, img):
        self.comp_img = img
        self.btn_c.configure(fg_color=COLORS["accent"], text_color="black", border_color=COLORS["accent"])
        self.check_ready()

    def check_ready(self):
        if self.thermo_img and self.comp_img:
            self.btn_go.configure(state="normal", fg_color=COLORS["text"], text_color="black")

    def start_ocr(self):
        self.btn_go.configure(text="PROCESSING...", state="disabled")
        threading.Thread(target=self.run_ocr, daemon=True).start()

    def preprocess(self, pil_img):
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return thresh

    def parse_data(self, text):
        text = text.replace("Q", "0").replace("O", "0").replace("o", "0")
        text = text.replace("@", "0").replace("Ø", "0").replace("D", "0")
        text = text.replace("theta", "0")

        def find(patterns):
            for p in patterns:
                match = re.search(p + r".*?(\d[\d\.]*)", text, re.IGNORECASE)
                if match: return match.group(1).rstrip('.')
            return ""

        raw_pwat = find([r"PWAT"])
        if raw_pwat:
            if re.match(r"^7\.\d+$", raw_pwat): raw_pwat = "1" + raw_pwat[1:]
            try:
                f = float(raw_pwat)
                f = round(f, 1)
                if f > 4.0:
                    if f == 7.0: f = 1.0
                    elif f >= 10: f = f / 10
                    else: f = 1.5
                raw_pwat = str(f)
            except: pass

        self.extracted_data = {
            "temp": find([r"TEMPERATURE", r"TEMP"]),
            "dew": find([r"DEW\s*P[O0Q@ØoD]INT", r"P[O0Q@ØoD]INT", r"DEWPOINT", r"DEW"]),
            "3cape": find([r"3\s*CAPE", r"3CAPE"]),
            "cape": find([r"(?<!3)CAPE"]),
            "lapse": find([r"0-3\s*[Kk]?[Mm]?\s*LAPSE", r"0-3\s*LAPSE", r"0-3"]),
            "srh": find([r"SRH"]),
            "rh": find([r"SURFACE\s*RH", r"SFC\s*RH"]),
            "mid_rh": find([r"MB\s*RH", r"500\s*MB", r"MID\s*RH"]),
            "pwat": raw_pwat,
            "stp": find([r"STP", r"SIP", r"S\.T\.P", r"3TP", r"3\s*T\s*P"]), 
            "vtp": find([r"VTP", r"VIP", r"V\.T\.P", r"3TP", r"3\s*T\s*P"]), 
            "raw": text
        }

    def show_verify(self):
        self.clear_ui()
        self.smooth_transition(400, 680) 
        self.canvas.create_text(20, 20, text="VERIFY", font=("Helvetica", 14, "bold"), fill="white", anchor="nw", tags="ui")
        
        # feedback 
        self.canvas.create_text(20, 50, text="REPORTING", font=("Helvetica", 10, "bold"), fill=COLORS["subtext"], anchor="nw", tags="ui")

        self.report_box = ctk.CTkTextbox(self.canvas, width=360, height=60, corner_radius=8, 
                                         fg_color=COLORS["panel"], text_color=COLORS["text"], 
                                         wrap="word", activate_scrollbars=False)
        self.report_box.insert("0.0", "Describe error (e.g. PWAT was read incorrectly (don't actually send this error, It's known, I'm working on it.))")
        self.canvas.create_window(200, 95, window=self.report_box, tags="ui")

        btn_flag = ctk.CTkButton(self.canvas, text="Flag Error", fg_color="transparent", border_color=COLORS["danger"], border_width=1,
                       text_color=COLORS["danger"], hover_color=COLORS["bg"], width=100, height=24, corner_radius=12,
                       command=self.send_user_report)
        self.canvas.create_window(340, 58, window=btn_flag, tags="ui")

        grid_frame = ctk.CTkFrame(self.canvas, fg_color="transparent", width=360)
        self.canvas.create_window(200, 360, window=grid_frame, tags="ui")
        self.entries = {}
        fields = [
            ("TEMP", "temp"), ("DEW", "dew"), ("CAPE", "cape"), ("3CAPE", "3cape"),
            ("SRH", "srh"), ("LAPSE", "lapse"), ("SFC RH", "rh"), ("MID RH", "mid_rh"),
            ("PWAT", "pwat"), ("STP", "stp"), ("VTP", "vtp"), ("SPEED", "speed")
        ]
        for i, (label, key) in enumerate(fields):
            r = i // 2
            c = i % 2
            row = ctk.CTkFrame(grid_frame, fg_color=COLORS["panel"], corner_radius=8, width=170, height=40)
            row.grid(row=r, column=c, padx=5, pady=5)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=label, font=("Helvetica", 9, "bold"), text_color=COLORS["subtext"]).pack(side="left", padx=10)
            entry = ctk.CTkEntry(row, font=("Helvetica", 14), fg_color="transparent", border_width=0, text_color="white", width=80)
            if key != "speed": entry.insert(0, self.extracted_data.get(key, ""))
            else: entry.configure(placeholder_text="60")
            entry.pack(side="right", padx=5)
            self.entries[key] = entry
        btn_run = ctk.CTkButton(self.canvas, text="Calculate", height=45, width=300, corner_radius=22,
                       fg_color=COLORS["accent"], text_color="black", hover_color=COLORS["accent_hover"],
                       font=("Helvetica", 14, "bold"),
                       command=self.calc)
        self.canvas.create_window(200, 640, window=btn_run, tags="ui")

    def send_user_report(self):
        """Prepares the user message and sends the report."""
        user_message = "No message provided."
        try:
             user_message = self.report_box.get("0.0", "end").strip()
        except: pass
        
        if not messagebox.askyesno("Report", "Send data (images and message)?"): return
        threading.Thread(target=self._send_report_to_webhook, args=(user_message,), daemon=True).start()

    def _send_report_to_webhook(self, message):
        """Actual logic for sending data and message to Discord."""
        try:
            files = {}
            for name, img in [("t.png", self.thermo_img), ("c.png", self.comp_img)]:
                b = BytesIO(); img.save(b, "PNG"); b.seek(0)
                files[name] = (name, b, "image/png")
                
            embeds = [{
                "title": "VORTEX OCR Error Report",
                "description": f"**User Feedback:**\n> {message}\n\n**Raw OCR Data:**\n```\n{self.extracted_data.get('raw', 'N/A')[:1000]}```",
                "color": 16777215 
            }]
            
            payload = {"embeds": embeds}
            requests.post(DISCORD_WEBHOOK_URL, files=files, data={"payload_json": json.dumps(payload)})
            self.after(0, lambda: messagebox.showinfo("Success", "Report Sent."))
        except Exception as e: 
            print(f"Webhook error: {e}")
            self.after(0, lambda: messagebox.showerror("Error", "Failed to send report."))

    def calc(self):
        try:
            def g(k):
                if k not in self.entries: return 0.0
                val = self.entries[k].get().replace(',', '.')
                val = re.sub(r"[^0-9.]", "", val)
                return float(val) if val else 0.0
            v = {k: g(k) for k in self.entries}
            if not self.entries.get("speed") or not self.entries["speed"].get():
                v["speed"] = 60.0
            def sc(val, mn, mx, mp):
                return 0 if val<=mn else mp if val>=mx else ((val-mn)/(mx-mn))*mp
            sh = {"Wedge":10, "Stovepipe":10, "Drillbit":3, "Sidewinder":5, "Cone":10, "Rope":10}
            constriction = sc(v["lapse"], 7.0, 10.0, 1.0)
            if v["rh"] < 45 and v["lapse"] > 10.5:
                dryness_score = sc(45 - v["rh"], 0, 25, 40)
                lapse_score = sc(v["lapse"], 10.5, 12.5, 40)
                sh["Drillbit"] += dryness_score + lapse_score
            sh["Wedge"] += sc(15-(v["temp"]-v["dew"]), 0, 10, 50) + sc(v["rh"], 60, 100, 60)
            if v["mid_rh"] > 60:
                sh["Wedge"] += sc(v["mid_rh"], 60, 95, 30)
            wedgePenalty = sc(v["lapse"], 8.5, 10.0, 15)
            if v["cape"] > 5000: wedgePenalty = 0; sh["Wedge"] += 20
            sh["Wedge"] = max(5, sh["Wedge"] - wedgePenalty)
            sh["Stovepipe"] += (sc(v["lapse"], 6.5, 8.0, 30) - sc(v["lapse"], 9.2, 11.0, 30)) + sc(v["rh"], 50, 85, 40)
            sh["Sidewinder"] += sc(v["vtp"], 1, 6, 50) + (constriction * 25)
            if v["stp"] > 5:
                bst = sc(v["stp"], 5, 25, 40)
                if constriction > 0.7:
                    if sh["Drillbit"] > 0: sh["Drillbit"] += bst*0.8
                    sh["Stovepipe"] += bst*0.4
                else:
                    sh["Wedge"] += bst*0.9
                    sh["Stovepipe"] += bst*0.4
            mv = min(95, 5 + sc(v["srh"], 200, 800, 80) + sc(v["stp"], 5, 25, 20))
            rain = min(100, 10 + sc(v["pwat"], 1.0, 2.5, 70) + sc(v["rh"], 60, 100, 20))
            pwr = ((v["cape"]*v["srh"])/250000) + (v["stp"]*0.7) + (constriction*1.5)
            ef = "EF0"; ef = "EF1" if pwr>1.5 else ef; ef = "EF2" if pwr>3.0 else ef
            ef = "EF3" if pwr>5.0 else ef; ef = "EF4" if pwr>8.0 else ef; ef = "EF5" if pwr>13.0 else ef
            self.show_res(sh, mv, rain, ef)
        except Exception as e:
            messagebox.showerror("Error", f"Crash Reason:\n{e}")

    def show_res(self, sh, mv, rain, ef):
        self.clear_ui()
        self.canvas.create_text(20, 20, text="INTENSITY", font=("Helvetica", 10, "bold"), fill=COLORS["subtext"], anchor="nw", tags="ui")
        self.canvas.create_text(20, 40, text=ef, font=("Helvetica", 64, "bold"), fill="white", anchor="nw", tags="ui")
        btn_reset = ctk.CTkButton(self.canvas, text="Reset", height=30, width=80, corner_radius=15,
                       fg_color="transparent", border_width=1, border_color=COLORS["subtext"],
                       text_color=COLORS["subtext"], hover_color=COLORS["border"],
                       command=self.show_landing)
        self.canvas.create_window(350, 40, window=btn_reset, tags="ui")
        y_start = 160
        x_left = 30
        x_right = 370
        bar_width = x_right - x_left
        tot = sum(sh.values())
        s_sh = sorted([(k, (v/tot)*100) for k,v in sh.items()], key=lambda x: x[1], reverse=True)
        cols = {"Wedge":"#f38ba8", "Stovepipe":"#89b4fa", "Drillbit":"#94e2d5", "Sidewinder":"#a6e3a1", "Cone":"#cba6f7", "Rope":"#6c7086"}
        for n, p in s_sh:
            self.canvas.create_text(x_left, y_start, text=n.upper(), font=("Helvetica", 11, "bold"), fill=COLORS["subtext"], anchor="sw", tags="ui")
            self.canvas.create_text(x_right, y_start, text=f"{p:.1f}%", font=("Helvetica", 11, "bold"), fill="white", anchor="se", tags="ui")
            self.canvas.create_line(x_left, y_start+8, x_right, y_start+8, fill="#313244", width=8, capstyle=tk.ROUND, tags="ui")
            fill_len = max(0.1, (p / 100) * bar_width)
            if p > 0:
                self.canvas.create_line(x_left, y_start+8, x_left + fill_len, y_start+8, fill=cols.get(n, "white"), width=8, capstyle=tk.ROUND, tags="ui")
            y_start += 40
        y_start += 10
        self.canvas.create_text(x_left, y_start, text="CONDITIONS", font=("Helvetica", 11, "bold"), fill=COLORS["subtext"], anchor="sw", tags="ui")
        y_start += 25
        def draw_cond(name, val, color, y):
            self.canvas.create_text(x_left, y, text=name.upper(), font=("Helvetica", 11, "bold"), fill=COLORS["subtext"], anchor="sw", tags="ui")
            self.canvas.create_text(x_right, y, text=f"{val:.1f}%", font=("Helvetica", 11, "bold"), fill="white", anchor="se", tags="ui")
            self.canvas.create_line(x_left, y+8, x_right, y+8, fill="#313244", width=8, capstyle=tk.ROUND, tags="ui")
            fill_len = max(0.1, (val / 100) * bar_width)
            if val > 0:
                self.canvas.create_line(x_left, y+8, x_left + fill_len, y+8, fill=color, width=8, capstyle=tk.ROUND, tags="ui")
        draw_cond("Multi-Vortex", mv, "#fab387", y_start)
        draw_cond("Rain Wrapped", rain, "#f9e2af", y_start + 40)

    def clear_frame(self):
        for w in self.scroll_container.winfo_children(): w.destroy()

if __name__ == "__main__":
    app = StormOverlay()
    app.mainloop()
