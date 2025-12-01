from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, NumericProperty, BooleanProperty
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from datetime import datetime

from sms_manager import load_spam, save_spam, get_grouped_spam, block_sms


class SpamDetailScreen(Screen):
    # Stored spam + threat messages
    spam_messages = ListProperty([])
    spam_count = NumericProperty(0)
    threat_count = NumericProperty(0)

    # User-defined spam keywords
    spam_keywords = ListProperty(["free", "win", "prize", "claim", "₱", "lottery"])

    # Spam blocking toggle
    block_enabled = BooleanProperty(False)

    # ---------------------------------------------
    # Screen loading
    # ---------------------------------------------
    def on_pre_enter(self):
        """Load spam/threat messages before entering screen."""
        data = get_grouped_spam()

        self.spam_messages = data["all"]
        self.spam_count = data["spam"]
        self.threat_count = data["threat"]

        self.load_list()

    def load_list(self):
        """Fill spam list UI."""
        container = self.ids.spam_container
        container.clear_widgets()

        for msg in self.spam_messages:
            text = msg["message"]
            category = msg["category"]

            color = (1, 0.9, 0, 1) if category == "spam" else (1, 0.3, 0.3, 1)

            btn = Button(
                text=text,
                size_hint_y=None,
                height=50,
                background_normal="",
                background_color=(0.18, 0.18, 0.18, 1),
                color=color
            )

            # pass captured variables safely with default arguments
            btn.bind(on_release=lambda b, t=text, c=category: self.open_popup(t, c))

            container.add_widget(btn)

    # ---------------------------------------------
    # Message Popup
    # ---------------------------------------------
    def open_popup(self, message, category):
        """Show message details popup."""
        color = (1, 0.9, 0, 1) if category == "spam" else (1, 0.3, 0.3, 1)

        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        lbl = Label(text=message, color=color)
        close_btn = Button(text="Close", size_hint_y=None, height=40)

        popup = Popup(
            title=f"Message ({category.upper()})",
            content=layout,
            size_hint=(0.8, 0.5),
            auto_dismiss=False
        )

        close_btn.bind(on_release=popup.dismiss)

        layout.add_widget(lbl)
        layout.add_widget(close_btn)
        popup.open()

    # ---------------------------------------------
    # Spam Keyword Management
    # ---------------------------------------------
    def show_keywords_popup(self, instance=None):
        """Popup for adding/removing keywords."""
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        keyword_input = TextInput(hint_text="Add keyword", size_hint_y=None, height=40)

        add_btn = Button(text="Add Keyword", size_hint_y=None, height=40)
        clear_btn = Button(text="Clear All Keywords", size_hint_y=None, height=40)
        close_btn = Button(text="Close", size_hint_y=None, height=40)

        layout.add_widget(keyword_input)
        layout.add_widget(add_btn)
        layout.add_widget(clear_btn)
        layout.add_widget(close_btn)

        popup = Popup(
            title="Spam Keywords",
            content=layout,
            size_hint=(0.8, 0.55),
            auto_dismiss=False
        )

        def add_keyword(_):
            kw = keyword_input.text.strip().lower()
            if kw and kw not in self.spam_keywords:
                self.spam_keywords.append(kw)
            keyword_input.text = ""

        def clear_keywords(_):
            self.spam_keywords.clear()

        add_btn.bind(on_release=add_keyword)
        clear_btn.bind(on_release=clear_keywords)
        close_btn.bind(on_release=popup.dismiss)

        popup.open()

    # ---------------------------------------------
    # Toggle blocking
    # ---------------------------------------------
    def toggle_block(self, instance):
        """Toggle blocking of detected spam."""
        self.block_enabled = not self.block_enabled
        instance.text = f"Block Spam: {'ON' if self.block_enabled else 'OFF'}"

    # ---------------------------------------------
    # Spam Detection + Blocking
    # ---------------------------------------------
    def detect_and_block(self, message, sender="Unknown"):
        """
        Check if SMS contains any spam keyword.
        Save to spam DB and block if enabled.
        """
        msg_lower = message.lower()

        for kw in self.spam_keywords:
            if kw in msg_lower:

                # Store entry properly (append instead of overwrite)
                existing = load_spam()

                new_entry = {
                    "address": sender,
                    "message": message,
                    "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "category": "spam"
                }

                existing.append(new_entry)
                save_spam(existing)

                # Refresh display
                self.on_pre_enter()

                # Block if enabled
                if self.block_enabled:
                    block_sms(new_entry)

                break
