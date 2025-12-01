from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.slider import MDSlider
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.button import MDRaisedButton
from kivy.uix.popup import Popup
from kivy.uix.label import Label

import floating_button
import contacts
from shake_voice_handler import SOSHandler

BUTTON_SETTINGS = {
    "shake_enabled": False,
    "shake_sensitivity": 5,
    "voice_enabled": False,
    "voice_phrase": "help me",
    "voice_sensitivity": 5,
    "floating_enabled": True,
    "button_size": 50,
    "countdown_enabled": True,
    "countdown_seconds": 5
}


class SettingsScreen(Screen):
    def on_kv_post(self, base_widget):
        self.app = MDApp.get_running_app()

        # Initialize SOS handler if not already
        if not hasattr(self.app, "shake_voice_handler"):
            self.app.shake_voice_handler = SOSHandler(
                app=self.app,
                settings=BUTTON_SETTINGS.copy(),
                contacts=contacts
            )

        layout = self.ids.settings_layout
        layout.clear_widgets()

        # ---------------- Shake Panel ----------------
        self._create_shake_panel(layout)

        # ---------------- Voice Panel ----------------
        self._create_voice_panel(layout)

        # ---------------- Floating Panel ----------------
        self._create_floating_panel(layout)

        # ---------------- Countdown Panel ----------------
        self._create_countdown_panel(layout)

        # ---------------- Save Button ----------------
        save_btn = MDRaisedButton(
            text="Save Settings",
            md_bg_color=(1, 0, 0, 1),
            size_hint_y=None,
            height=55
        )
        save_btn.bind(on_release=lambda x: self.save_settings())
        layout.add_widget(save_btn)

        # Initialize floating button
        self._update_floating_button()

    # ---------------- Panel Builders ----------------
    def _create_shake_panel(self, parent):
        parent.add_widget(MDLabel(text="Shake Activation", bold=True, font_style="H6", size_hint_y=None, height=30))
        box = MDBoxLayout(orientation="vertical", spacing=10, padding=(20, 10), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))

        # Enable checkbox
        row = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        row.add_widget(MDLabel(text="Enable", halign="left"))
        self.shake_chk = MDCheckbox(active=BUTTON_SETTINGS["shake_enabled"])
        self.shake_chk.bind(active=self.toggle_shake_settings)
        row.add_widget(self.shake_chk)
        box.add_widget(row)

        # Intensity slider
        box.add_widget(MDLabel(text="Intensity", halign="left", theme_text_color="Secondary"))
        self.shake_slider = MDSlider(min=1, max=10, step=1,
                                     value=BUTTON_SETTINGS["shake_sensitivity"],
                                     size_hint_y=None, height=40)
        self.shake_slider.bind(value=self.update_shake_sensitivity)
        self.shake_slider.disabled = not BUTTON_SETTINGS["shake_enabled"]
        box.add_widget(self.shake_slider)
        parent.add_widget(box)

    def _create_voice_panel(self, parent):
        parent.add_widget(MDLabel(text="Voice Activation", bold=True, font_style="H6", size_hint_y=None, height=30))
        box = MDBoxLayout(orientation="vertical", spacing=10, padding=(20, 10), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))

        # Enable checkbox
        row = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        row.add_widget(MDLabel(text="Enable", halign="left"))
        self.voice_chk = MDCheckbox(active=BUTTON_SETTINGS["voice_enabled"])
        self.voice_chk.bind(active=self.toggle_voice_settings)
        row.add_widget(self.voice_chk)
        box.add_widget(row)

        # Activation phrase
        phrase_row = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=50)
        phrase_row.add_widget(MDLabel(text="Activation Phrase", size_hint_x=0.5, halign="left"))
        self.voice_input = MDTextField(text=BUTTON_SETTINGS["voice_phrase"], multiline=False, size_hint_x=0.5)
        self.voice_input.bind(text=self.update_voice_phrase)
        phrase_row.add_widget(self.voice_input)
        box.add_widget(phrase_row)

        # Sensitivity
        box.add_widget(MDLabel(text="Sensitivity", halign="left", theme_text_color="Secondary"))
        self.voice_slider = MDSlider(min=1, max=10, step=1,
                                     value=BUTTON_SETTINGS["voice_sensitivity"],
                                     size_hint_y=None, height=40)
        self.voice_slider.bind(value=self.update_voice_sensitivity)
        box.add_widget(self.voice_slider)

        self.voice_input.disabled = not BUTTON_SETTINGS["voice_enabled"]
        self.voice_slider.disabled = not BUTTON_SETTINGS["voice_enabled"]

        parent.add_widget(box)

    def _create_floating_panel(self, parent):
        parent.add_widget(MDLabel(text="Floating Button", bold=True, font_style="H6", size_hint_y=None, height=30))
        box = MDBoxLayout(orientation="vertical", spacing=10, padding=(20, 10), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))

        # Enable checkbox
        row = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        row.add_widget(MDLabel(text="Enable", halign="left"))
        self.floating_chk = MDCheckbox(active=BUTTON_SETTINGS["floating_enabled"])
        self.floating_chk.bind(active=self.toggle_floating_settings)
        row.add_widget(self.floating_chk)
        box.add_widget(row)

        # Button size
        size_row = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=50)
        size_row.add_widget(MDLabel(text="Button Size", size_hint_x=0.6, halign="left"))
        self.size_input = MDTextField(text=str(BUTTON_SETTINGS["button_size"]), multiline=False, size_hint_x=0.4)
        self.size_input.bind(text=self.update_floating_size)
        size_row.add_widget(self.size_input)
        box.add_widget(size_row)

        self.size_input.disabled = not BUTTON_SETTINGS["floating_enabled"]
        parent.add_widget(box)

    def _create_countdown_panel(self, parent):
        parent.add_widget(MDLabel(text="Countdown", bold=True, font_style="H6", size_hint_y=None, height=30))
        box = MDBoxLayout(orientation="vertical", spacing=10, padding=(20, 10), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))

        # Enable checkbox
        row = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        row.add_widget(MDLabel(text="Enable", halign="left"))
        self.countdown_chk = MDCheckbox(active=BUTTON_SETTINGS["countdown_enabled"])
        self.countdown_chk.bind(active=self.toggle_countdown_settings)
        row.add_widget(self.countdown_chk)
        box.add_widget(row)

        # Seconds
        seconds_row = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=50)
        seconds_row.add_widget(MDLabel(text="Countdown Seconds", size_hint_x=0.6, halign="left"))
        self.countdown_input = MDTextField(text=str(BUTTON_SETTINGS["countdown_seconds"]), multiline=False, size_hint_x=0.4)
        self.countdown_input.bind(text=self.update_countdown_seconds)
        seconds_row.add_widget(self.countdown_input)
        box.add_widget(seconds_row)

        self.countdown_input.disabled = not BUTTON_SETTINGS["countdown_enabled"]
        parent.add_widget(box)

    # ---------------- Toggle / Update Methods ----------------
    def toggle_shake_settings(self, instance, value):
        BUTTON_SETTINGS["shake_enabled"] = value
        self.shake_slider.disabled = not value
        self.app.shake_voice_handler.update_settings(BUTTON_SETTINGS)

    def update_shake_sensitivity(self, instance, value):
        BUTTON_SETTINGS["shake_sensitivity"] = int(value)
        self.app.shake_voice_handler.update_settings(BUTTON_SETTINGS)

    def toggle_voice_settings(self, instance, value):
        BUTTON_SETTINGS["voice_enabled"] = value
        self.voice_input.disabled = not value
        self.voice_slider.disabled = not value
        self.app.shake_voice_handler.update_settings(BUTTON_SETTINGS)

    def update_voice_phrase(self, instance, value):
        BUTTON_SETTINGS["voice_phrase"] = value
        self.app.shake_voice_handler.save_voice_phrase(value)

    def update_voice_sensitivity(self, instance, value):
        BUTTON_SETTINGS["voice_sensitivity"] = int(value)
        self.app.shake_voice_handler.update_settings(BUTTON_SETTINGS)

    def toggle_floating_settings(self, instance, value):
        BUTTON_SETTINGS["floating_enabled"] = value
        self.size_input.disabled = not value
        self._update_floating_button()

    def update_floating_size(self, instance, text):
        try:
            size = max(20, min(120, int(text)))
            BUTTON_SETTINGS["button_size"] = size
            if BUTTON_SETTINGS["floating_enabled"]:
                floating_button.set_button_size(size)
        except ValueError:
            pass

    def toggle_countdown_settings(self, instance, value):
        BUTTON_SETTINGS["countdown_enabled"] = value
        self.countdown_input.disabled = not value
        if not value:
            self.app.shake_voice_handler.cancel_countdown()
        else:
            BUTTON_SETTINGS["countdown_seconds"] = max(1, int(self.countdown_input.text or 5))

    def update_countdown_seconds(self, instance, text):
        try:
            BUTTON_SETTINGS["countdown_seconds"] = max(1, int(text))
        except ValueError:
            pass

    # ---------------- Save & Apply ----------------
    def save_settings(self):
        try:
            BUTTON_SETTINGS["button_size"] = max(20, min(120, int(self.size_input.text)))
        except ValueError:
            BUTTON_SETTINGS["button_size"] = 50

        try:
            BUTTON_SETTINGS["countdown_seconds"] = max(1, int(self.countdown_input.text))
        except ValueError:
            BUTTON_SETTINGS["countdown_seconds"] = 5

        self.app.shake_voice_handler.update_settings(BUTTON_SETTINGS)
        self._update_floating_button()

        Popup(
            title="Saved",
            content=Label(text="Settings saved successfully."),
            size_hint=(0.6, 0.3)
        ).open()

    def _update_floating_button(self):
        if BUTTON_SETTINGS["floating_enabled"]:
            floating_button.enable_floating(callback=lambda: self.app.shake_voice_handler.send_alert("Button"))
            floating_button.set_button_size(BUTTON_SETTINGS["button_size"])
        else:
            floating_button.disable_floating()
