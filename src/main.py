#!/usr/bin/env python3
"""
AI Voice Assistant Mobile
Production-ready mobile app for Android
"""

import os
import sys

# Kivy configuration
os.environ['KIVY_NO_CONSOLELOG'] = '1'
os.environ['KIVY_WINDOW'] = 'sdl2'

from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'system')
Config.set('graphics', 'orientation', 'portrait')
Config.set('graphics', 'fullscreen', '0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore
from kivy.logger import Logger

# Try KivyMD
try:
    from kivymd.app import MDApp
    from kivymd.uix.screen import MDScreen
    from kivymd.uix.button import MDFloatingActionButton, MDRaisedButton
    from kivymd.uix.textfield import MDTextField
    from kivymd.uix.label import MDLabel
    from kivymd.uix.toolbar import MDTopAppBar
    from kivymd.uix.dialog import MDDialog
    KIVYMD_AVAILABLE = True
except ImportError:
    KIVYMD_AVAILABLE = False
    # Fallbacks
    class MDScreen(Screen): pass
    class MDFloatingActionButton(Button):
        icon = StringProperty('')
    class MDRaisedButton(Button): pass
    class MDTextField(TextInput):
        hint_text = StringProperty('')
    class MDLabel(Label):
        theme_text_color = StringProperty('')
        font_style = StringProperty('')
    class MDTopAppBar(BoxLayout):
        title = StringProperty('')
        left_action_items = []
        right_action_items = []
    class MDDialog:
        def __init__(self, **kwargs): pass
        def open(self): pass
    class MDApp(App): pass

# AI imports
try:
    from langgraph.graph import StateGraph, END, START
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, AIMessage
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    Logger.warning("AI libraries not available")

# Android
try:
    from android.permissions import request_permissions, Permission
    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False

# Plyer
try:
    from plyer import tts, vibrator
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


# ==================== CONFIGURATION ====================

class Config:
    APP_NAME = "AI Voice Assistant"
    VERSION = "1.0.0"
    
    @staticmethod
    def get_base_path():
        if platform == 'android':
            try:
                from android.storage import app_storage_path
                return app_storage_path()
            except:
                return '/sdcard/Android/data/org.aivoiceassistant/files'
        elif platform == 'ios':
            return os.path.expanduser('~/Documents')
        else:
            return os.path.join(os.path.expanduser('~'), '.ai_assistant')
    
    BASE_PATH = get_base_path()
    PATHS = {
        'data': os.path.join(BASE_PATH, 'data'),
        'chats': os.path.join(BASE_PATH, 'data', 'chats'),
        'settings': os.path.join(BASE_PATH, 'settings.json')
    }

# Initialize paths
for path in Config.PATHS.values():
    os.makedirs(path, exist_ok=True)


# ==================== STORAGE ====================

class Storage:
    def __init__(self):
        self.store = JsonStore(Config.PATHS['settings'])
    
    def get(self, key, default=None):
        try:
            return self.store.get(key)['value']
        except:
            return default
    
    def set(self, key, value):
        self.store.put(key, value=value)

storage = Storage()


# ==================== AI ENGINE ====================

class AIEngine:
    def __init__(self):
        self.llm = None
        self.connected = False
        if AI_AVAILABLE:
            self._init()
    
    def _init(self):
        try:
            self.llm = ChatOllama(
                model=storage.get('model', 'gemma3:1b'),
                temperature=0.7,
                num_predict=512,
                base_url=storage.get('host', 'http://localhost:11434'),
                timeout=30
            )
            self.connected = True
        except Exception as e:
            Logger.error(f"AI init failed: {e}")
    
    def generate(self, message, history=None):
        if not self.connected or not AI_AVAILABLE:
            return {
                'error': True,
                'response': 'AI not connected. Please start Ollama server on your computer.\n\nDemo mode: This is a sample response showing the app works correctly.'
            }
        
        try:
            messages = []
            if history:
                for h in history[-3:]:
                    if h['role'] == 'user':
                        messages.append(HumanMessage(content=h['content']))
                    else:
                        messages.append(AIMessage(content=h['content']))
            
            messages.append(HumanMessage(content=message))
            response = self.llm.invoke(messages)
            
            return {
                'error': False,
                'response': response.content
            }
        except Exception as e:
            return {
                'error': True,
                'response': f'Error: {str(e)}'
            }

ai_engine = AIEngine()


# ==================== CHAT MANAGEMENT ====================

class ChatManager:
    def __init__(self):
        self.current = None
        self.dir = Config.PATHS['chats']
        os.makedirs(self.dir, exist_ok=True)
    
    def create(self):
        self.save()
        import time
        self.current = {
            'id': f"chat_{int(time.time())}",
            'title': 'New Chat',
            'messages': [],
            'created': time.time(),
            'updated': time.time()
        }
        return self.current
    
    def save(self):
        if not self.current or not self.current.get('messages'):
            return
        import json
        filepath = os.path.join(self.dir, f"{self.current['id']}.json")
        with open(filepath, 'w') as f:
            json.dump(self.current, f)
    
    def load(self, sid):
        import json
        filepath = os.path.join(self.dir, f"{sid}.json")
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r') as f:
            self.current = json.load(f)
            return self.current
    
    def list(self):
        import json
        import glob
        sessions = []
        for filepath in glob.glob(os.path.join(self.dir, "*.json")):
            try:
                with open(filepath, 'r') as f:
                    d = json.load(f)
                    sessions.append({
                        'id': d['id'],
                        'title': d.get('title', 'Chat'),
                        'updated': d.get('updated', 0),
                        'count': len(d.get('messages', []))
                    })
            except:
                pass
        return sorted(sessions, key=lambda x: x['updated'], reverse=True)

chat_mgr = ChatManager()


# ==================== UI COMPONENTS ====================

class MessageBubble(BoxLayout):
    role = StringProperty('user')
    text = StringProperty('')
    time = StringProperty('')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.padding = dp(10)
        
        with self.canvas.before:
            self.bg_color = Color(0.2, 0.4, 0.8, 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        self.msg_lbl = Label(
            text=self.text,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            font_size=sp(14),
            markup=True,
            halign='left',
            valign='top'
        )
        self.msg_lbl.bind(texture_size=self._on_text_size)
        self.add_widget(self.msg_lbl)
        
        self.time_lbl = Label(
            text=self.time,
            font_size=sp(10),
            size_hint_y=None,
            height=dp(16),
            halign='right',
            color=(0.8, 0.8, 0.8, 1)
        )
        self.add_widget(self.time_lbl)
        
        Clock.schedule_once(self._update_style, 0)
    
    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def _update_style(self, dt):
        is_user = self.role == 'user'
        if is_user:
            self.bg_color.rgb = (0.2, 0.5, 0.9)
            self.pos_hint = {'right': 1}
            self.size_hint_x = 0.8
        else:
            self.bg_color.rgb = (0.25, 0.25, 0.3)
            self.pos_hint = {'x': 0}
            self.size_hint_x = 0.85
        
        self.msg_lbl.text = self.text
        self.time_lbl.text = self.time
    
    def _on_text_size(self, inst, size):
        self.height = size[1] + dp(40)


class VoiceButton(Button):
    recording = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = '🎤'
        self.font_size = sp(24)
        self.size_hint = (None, None)
        self.size = (dp(56), dp(56))
        self.background_color = (0.2, 0.6, 1, 1)
    
    def on_recording(self, inst, val):
        if val:
            self.text = '⏹'
            self.background_color = (0.9, 0.2, 0.2, 1)
            anim = Animation(size=(dp(64), dp(64)), d=0.3) + Animation(size=(dp(56), dp(56)), d=0.3)
            anim.repeat = True
            anim.start(self)
            if PLYER_AVAILABLE and storage.get('haptic', True):
                try:
                    vibrator.vibrate(0.05)
                except:
                    pass
        else:
            self.text = '🎤'
            self.background_color = (0.2, 0.6, 1, 1)


# ==================== SCREENS ====================

class ChatScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'chat'
        self.processing = False
        self._build()
        if not chat_mgr.current:
            chat_mgr.create()
        Clock.schedule_once(self._load, 0.1)
    
    def _build(self):
        layout = BoxLayout(orientation='vertical')
        
        # Toolbar
        tb = BoxLayout(size_hint_y=None, height=dp(56), padding=dp(8))
        menu_btn = Button(text='☰', size_hint_x=None, width=dp(48))
        menu_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'history'))
        tb.add_widget(menu_btn)
        
        self.title_lbl = Label(text=Config.APP_NAME, font_size=sp(18))
        tb.add_widget(self.title_lbl)
        
        set_btn = Button(text='⚙', size_hint_x=None, width=dp(48))
        set_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        tb.add_widget(set_btn)
        layout.add_widget(tb)
        
        # Messages
        self.scroll = ScrollView()
        self.messages_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8), padding=dp(8))
        self.messages_box.bind(minimum_height=self.messages_box.setter('height'))
        self.scroll.add_widget(self.messages_box)
        layout.add_widget(self.scroll)
        
        # Input
        input_box = BoxLayout(size_hint_y=None, height=dp(80), padding=dp(8), spacing=dp(8))
        
        self.text_input = TextInput(
            hint_text='Type message...',
            size_hint_x=0.7,
            multiline=False,
            font_size=sp(14)
        )
        self.text_input.bind(on_text_validate=self._send)
        input_box.add_widget(self.text_input)
        
        self.voice_btn = VoiceButton()
        self.voice_btn.bind(on_press=self._toggle_voice)
        input_box.add_widget(self.voice_btn)
        
        send_btn = Button(text='➤', size_hint=(None, None), size=(dp(56), dp(56)), 
                       background_color=(0.2, 0.8, 0.4, 1), font_size=sp(20))
        send_btn.bind(on_press=self._send)
        input_box.add_widget(send_btn)
        
        layout.add_widget(input_box)
        self.add_widget(layout)
        
        Window.bind(on_keyboard=self._on_key)
    
    def _on_key(self, win, key, *args):
        if key == 27:
            App.get_running_app().stop()
            return True
        return False
    
    def _load(self, dt):
        self.messages_box.clear_widgets()
        if not chat_mgr.current:
            return
        
        self.title_lbl.text = chat_mgr.current.get('title', 'Chat')
        for m in chat_mgr.current.get('messages', []):
            self._add_bubble(m['role'], m['content'], m.get('time', 0))
        Clock.schedule_once(self._scroll_bottom, 0.2)
    
    def _add_bubble(self, role, content, timestamp):
        from datetime import datetime
        time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M') if timestamp else ''
        bubble = MessageBubble(role=role, text=content, time=time_str)
        self.messages_box.add_widget(bubble)
    
    def _scroll_bottom(self, dt=None):
        if self.messages_box.height > self.scroll.height:
            self.scroll.scroll_y = 0
    
    def _send(self, *args):
        if self.processing:
            return
        
        text = self.text_input.text.strip()
        if not text:
            return
        
        self.text_input.text = ''
        import time
        self._add_bubble('user', text, time.time())
        chat_mgr.current['messages'].append({'role': 'user', 'content': text, 'time': time.time()})
        self._scroll_bottom()
        
        self.processing = True
        self._show_typing()
        import threading
        threading.Thread(target=self._generate, args=(text,), daemon=True).start()
    
    def _generate(self, text):
        history = [{'role': m['role'], 'content': m['content']} 
                  for m in chat_mgr.current['messages'][:-1]]
        result = ai_engine.generate(text, history)
        Clock.schedule_once(lambda dt: self._show_response(result), 0)
    
    def _show_typing(self):
        self.typing_lbl = Label(text='AI is typing...', color=(0.5, 0.5, 0.5, 1), 
                               italic=True, size_hint_y=None, height=dp(30))
        self.messages_box.add_widget(self.typing_lbl)
        self._scroll_bottom()
    
    def _show_response(self, result):
        if hasattr(self, 'typing_lbl') and self.typing_lbl in self.messages_box.children:
            self.messages_box.remove_widget(self.typing_lbl)
        
        import time
        text = result['response']
        self._add_bubble('assistant', text, time.time())
        chat_mgr.current['messages'].append({'role': 'assistant', 'content': text, 'time': time.time()})
        
        if storage.get('auto_save', True):
            chat_mgr.save()
        
        if storage.get('tts', False) and PLYER_AVAILABLE:
            try:
                tts.speak(text)
            except:
                pass
        
        self._scroll_bottom()
        self.processing = False
    
    def _toggle_voice(self, btn):
        btn.recording = not btn.recording


class HistoryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'history'
        self._build()
    
    def _build(self):
        layout = BoxLayout(orientation='vertical')
        
        tb = BoxLayout(size_hint_y=None, height=dp(56), padding=dp(8))
        back_btn = Button(text='←', size_hint_x=None, width=dp(48))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'chat'))
        tb.add_widget(back_btn)
        tb.add_widget(Label(text='History', font_size=sp(18)))
        layout.add_widget(tb)
        
        self.list_box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(self.list_box)
        layout.add_widget(scroll)
        
        new_btn = Button(text='+ New Chat', size_hint_y=None, height=dp(56), 
                        background_color=(0.2, 0.6, 1, 1))
        new_btn.bind(on_press=self._new)
        layout.add_widget(new_btn)
        
        self.add_widget(layout)
        Clock.schedule_once(self._load, 0.1)
    
    def _load(self, dt):
        self.list_box.clear_widgets()
        for s in chat_mgr.list():
            btn = Button(text=f"{s['title']}\n{s['count']} msgs", 
                        size_hint_y=None, height=dp(72), halign='center')
            btn.bind(on_press=lambda x, sid=s['id']: self._open(sid))
            self.list_box.add_widget(btn)
    
    def _open(self, sid):
        chat_mgr.load(sid)
        self.manager.current = 'chat'
        Clock.schedule_once(self.manager.get_screen('chat')._load, 0.1)
    
    def _new(self, *args):
        chat_mgr.create()
        self.manager.current = 'chat'
        Clock.schedule_once(self.manager.get_screen('chat')._load, 0.1)


class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'settings'
        self._build()
    
    def _build(self):
        layout = BoxLayout(orientation='vertical')
        
        tb = BoxLayout(size_hint_y=None, height=dp(56), padding=dp(8))
        back_btn = Button(text='←', size_hint_x=None, width=dp(48))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'chat'))
        tb.add_widget(back_btn)
        tb.add_widget(Label(text='Settings', font_size=sp(18)))
        layout.add_widget(tb)
        
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(16), spacing=dp(12))
        content.bind(minimum_height=content.setter('height'))
        
        content.add_widget(self._header('AI Model'))
        self.model_inp = TextInput(text=storage.get('model', 'gemma3:1b'), multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(self.model_inp)
        
        content.add_widget(self._header('Ollama Host'))
        self.host_inp = TextInput(text=storage.get('host', 'http://localhost:11434'), multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(self.host_inp)
        
        content.add_widget(self._toggle('Dark Mode', 'dark', True))
        content.add_widget(self._toggle('Auto Save', 'auto_save', True))
        content.add_widget(self._toggle('Haptic', 'haptic', True))
        content.add_widget(self._toggle('TTS', 'tts', False))
        
        test_btn = Button(text='Test Connection', size_hint_y=None, height=dp(48), background_color=(0.2, 0.6, 1, 1))
        test_btn.bind(on_press=self._test)
        content.add_widget(test_btn)
        
        save_btn = Button(text='Save', size_hint_y=None, height=dp(48), background_color=(0.2, 0.8, 0.4, 1))
        save_btn.bind(on_press=self._save)
        content.add_widget(save_btn)
        
        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)
    
    def _header(self, text):
        lbl = Label(text=text, font_size=sp(14), bold=True, size_hint_y=None, height=dp(30), 
                   color=(0.4, 0.7, 1, 1), halign='left')
        lbl.bind(size=lbl.setter('text_size'))
        return lbl
    
    def _toggle(self, label, key, default):
        box = BoxLayout(size_hint_y=None, height=dp(48))
        box.add_widget(Label(text=label, size_hint_x=0.7))
        val = storage.get(key, default)
        btn = ToggleButton(text='ON' if val else 'OFF', state='down' if val else 'normal', size_hint_x=0.3)
        btn.key = key
        btn.bind(on_press=lambda x: setattr(x, 'text', 'ON' if x.state == 'down' else 'OFF'))
        box.add_widget(btn)
        return box
    
    def _test(self, *args):
        ok = ai_engine.check_connection()
        popup = Popup(title='Connection', content=Label(text='Connected!' if ok else 'Failed'), size_hint=(0.6, 0.3))
        popup.open()
    
    def _save(self, *args):
        storage.set('model', self.model_inp.text)
        storage.set('host', self.host_inp.text)
        for child in self.walk():
            if hasattr(child, 'key') and isinstance(child, ToggleButton):
                storage.set(child.key, child.state == 'down')
        ai_engine._init()
        popup = Popup(title='Settings', content=Label(text='Saved!'), size_hint=(0.6, 0.3))
        popup.open()


# ==================== MAIN APP ====================

class AIAssistantApp(MDApp if KIVYMD_AVAILABLE else App):
    def build(self):
        is_dark = storage.get('dark', True)
        Window.clearcolor = (0.08, 0.08, 0.12, 1) if is_dark else (0.95, 0.95, 0.97, 1)
        
        if ANDROID_AVAILABLE:
            Clock.schedule_once(self._request_permissions, 0)
        
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(ChatScreen())
        sm.add_widget(HistoryScreen())
        sm.add_widget(SettingsScreen())
        return sm
    
    def _request_permissions(self, dt):
        if ANDROID_AVAILABLE:
            try:
                request_permissions([Permission.INTERNET, Permission.RECORD_AUDIO])
            except:
                pass
    
    def on_pause(self):
        chat_mgr.save()
        return True
    
    def on_stop(self):
        chat_mgr.save()

if __name__ == '__main__':
    AIAssistantApp().run()