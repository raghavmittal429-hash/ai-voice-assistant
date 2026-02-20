#!/usr/bin/env python3
"""
AI Voice Assistant Mobile
Stable Correct Version - FIXED
"""

import os
import json
import time
import glob

# ================= KIVY CONFIG =================

os.environ["KIVY_NO_CONSOLELOG"] = "1"
os.environ["KIVY_WINDOW"] = "sdl2"

from kivy.config import Config as KivyConfig
KivyConfig.set("kivy", "keyboard_mode", "system")
KivyConfig.set("graphics", "orientation", "portrait")
KivyConfig.set("graphics", "fullscreen", "0")

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore
from kivy.logger import Logger

# ================= OPTIONAL AI =================

try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, AIMessage
    AI_AVAILABLE = True
except Exception:
    AI_AVAILABLE = False
    Logger.warning("AI libraries not available — running in demo mode.")

# ================= PATH SETUP =================

def get_base_path():
    if platform == "android":
        try:
            from android.storage import app_storage_path
            return app_storage_path()
        except Exception:
            return os.path.expanduser("~")
    return os.path.join(os.path.expanduser("~"), ".ai_assistant")

BASE_PATH = get_base_path()

PATHS = {
    "data": os.path.join(BASE_PATH, "data"),
    "chats": os.path.join(BASE_PATH, "data", "chats"),
    "settings": os.path.join(BASE_PATH, "settings.json"),
}

os.makedirs(PATHS["data"], exist_ok=True)
os.makedirs(PATHS["chats"], exist_ok=True)

# ================= STORAGE =================

class Storage:
    def __init__(self):
        if not os.path.exists(PATHS["settings"]):
            with open(PATHS["settings"], "w") as f:
                json.dump({}, f)
        self.store = JsonStore(PATHS["settings"])

    def get(self, key, default=None):
        try:
            return self.store.get(key)["value"]
        except Exception:
            return default

    def set(self, key, value):
        self.store.put(key, value=value)

storage = Storage()

# ================= AI ENGINE =================

class AIEngine:
    def __init__(self):
        self.llm = None
        self.connected = False
        if AI_AVAILABLE:
            self.initialize()

    def initialize(self):
        try:
            self.llm = ChatOllama(
                model=storage.get("model", "gemma:2b"),
                temperature=0.7,
                base_url=storage.get("host", "http://localhost:11434"),
            )
            self.connected = True
        except Exception as e:
            Logger.error(f"AI init failed: {e}")
            self.connected = False

    def generate(self, message, history=None):
        if not self.connected or not AI_AVAILABLE:
            return "AI not connected.\n\nDemo response: App is working."

        try:
            messages = []

            if history:
                for h in history[-3:]:
                    if h["role"] == "user":
                        messages.append(HumanMessage(content=h["content"]))
                    else:
                        messages.append(AIMessage(content=h["content"]))

            messages.append(HumanMessage(content=message))
            response = self.llm.invoke(messages)

            return response.content

        except Exception as e:
            return f"Error: {str(e)}"

ai_engine = AIEngine()

# ================= CHAT MANAGER =================

class ChatManager:
    def __init__(self):
        self.current = None
        self.dir = PATHS["chats"]

    def create(self):
        self.current = {
            "id": f"chat_{int(time.time())}",
            "messages": [],
        }
        return self.current

    def save(self):
        if not self.current:
            return
        filepath = os.path.join(self.dir, f"{self.current['id']}.json")
        with open(filepath, "w") as f:
            json.dump(self.current, f)

chat_mgr = ChatManager()

# ================= MESSAGE BUBBLE =================

class MessageBubble(BoxLayout):
    def __init__(self, role, text, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            padding=dp(5),
            **kwargs
        )

        self.role = role

        self.label = Label(
            text=text,
            size_hint=(0.75, None),
            text_size=(None, None),
            halign="left",
            valign="middle",
            color=(1,1,1,1)
        )

        self.label.bind(texture_size=self.update_height)

        if role == "user":
            self.add_widget(BoxLayout())
            self.add_widget(self.label)
        else:
            self.add_widget(self.label)
            self.add_widget(BoxLayout())

        with self.canvas.before:
            if role == "user":
                Color(0.2, 0.5, 0.9, 1)
            else:
                Color(0.3, 0.3, 0.3, 1)
            self.rect = RoundedRectangle(radius=[dp(12)])

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_height(self, instance, size):
        self.label.height = size[1] + dp(20)
        self.height = self.label.height

    def update_rect(self, *args):
        self.rect.pos = self.label.pos
        self.rect.size = self.label.size

# ================= CHAT SCREEN =================

class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name="chat", **kwargs)
        self.build_ui()

        if not chat_mgr.current:
            chat_mgr.create()

    def build_ui(self):
        layout = BoxLayout(orientation="vertical")

        self.scroll = ScrollView()
        self.messages_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=dp(8),
        )
        self.messages_box.bind(minimum_height=self.messages_box.setter("height"))
        self.scroll.add_widget(self.messages_box)
        layout.add_widget(self.scroll)

        input_box = BoxLayout(size_hint_y=None, height=dp(60))

        self.text_input = TextInput(multiline=False)
        self.text_input.bind(on_text_validate=self.send)
        input_box.add_widget(self.text_input)

        send_btn = Button(text="Send", size_hint_x=0.3)
        send_btn.bind(on_press=self.send)
        input_box.add_widget(send_btn)

        layout.add_widget(input_box)
        self.add_widget(layout)

    def add_bubble(self, role, text):
        bubble = MessageBubble(role, text)
        self.messages_box.add_widget(bubble)
        Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0))

    def send(self, *args):
        text = self.text_input.text.strip()
        if not text:
            return

        self.text_input.text = ""
        self.add_bubble("user", text)

        chat_mgr.current["messages"].append({
            "role": "user",
            "content": text,
        })

        Clock.schedule_once(lambda dt: self.generate(text))

    def generate(self, text):
        history = chat_mgr.current["messages"][:-1]
        response = ai_engine.generate(text, history)

        self.add_bubble("assistant", response)

        chat_mgr.current["messages"].append({
            "role": "assistant",
            "content": response,
        })

        chat_mgr.save()

# ================= MAIN APP =================

class AIAssistantApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(ChatScreen())
        return sm

    def on_stop(self):
        chat_mgr.save()

if __name__ == "__main__":
    AIAssistantApp().run()