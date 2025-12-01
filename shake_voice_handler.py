import os, json, math, platform, threading, queue
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button

# Optional modules for mobile/desktop
try:
    from plyer import gps, notification, accelerometer, microphone
except ImportError:
    gps = notification = accelerometer = microphone = None

# Vosk for desktop
try:
    import pyaudio
    from vosk import Model, KaldiRecognizer
except ImportError:
    pyaudio = Model = KaldiRecognizer = None

from floating_button import enable_floating, disable_floating, send_sos_message

VOICE_PHRASE_FILE = os.path.join(os.getcwd(), "phrase.json")
DEFAULT_PHRASE = "help me"
IS_ANDROID = platform.system() == "Linux" and "ANDROID_ARGUMENT" in os.sys.argv


class SOSHandler:
    """
    Handles SOS triggers: shake, voice, floating button.
    Sends SOS messages with countdown and location support.
    """

    def __init__(self, app=None, settings=None, contacts=None):
        self.app = app
        self.settings = settings or {
            "shake_enabled": False,
            "voice_enabled": False,
            "floating_enabled": False,
            "countdown_seconds": 5,
            "shake_sensitivity": 5,
            "button_size": 80
        }

        # Contacts
        if contacts is None:
            self.contacts = []
        elif isinstance(contacts, (list, tuple)):
            self.contacts = list(contacts)
        else:
            print("[WARNING] contacts must be a list or tuple. Resetting to empty list.")
            self.contacts = []

        # Shake variables
        self.last_x = self.last_y = self.last_z = None
        self.shake_threshold = 10
        self._shake_count = 0
        self._required_consecutive = 2
        self._shake_event = None

        # Voice recognition variables
        self.is_listening = False
        self.vosk_initialized = False
        self.voice_model = None
        self.recognizer = None
        self.audio_stream = None
        self._voice_thread = None
        self._voice_event = None
        self._voice_queue = queue.Queue()
        self.voice_phrase = self.load_voice_phrase()

        # GPS / Location
        self.current_location = {"lat": None, "lon": None}
        self.start_gps()

        # Countdown
        self.countdown_popup = None
        self._countdown_event = None
        self._remaining_seconds = 0

        self.apply_settings()

    # -------------------- Voice Phrase --------------------
    def load_voice_phrase(self):
        if os.path.exists(VOICE_PHRASE_FILE):
            try:
                with open(VOICE_PHRASE_FILE, "r") as f:
                    return json.load(f).get("voice_phrase", DEFAULT_PHRASE).lower()
            except Exception:
                return DEFAULT_PHRASE
        return DEFAULT_PHRASE

    def save_voice_phrase(self, phrase):
        self.voice_phrase = phrase.lower()
        try:
            with open(VOICE_PHRASE_FILE, "w") as f:
                json.dump({"voice_phrase": self.voice_phrase}, f)
        except Exception as e:
            print("[ERROR] Failed to save voice phrase:", e)

    # -------------------- GPS / Location --------------------
    def start_gps(self):
        if IS_ANDROID and gps:
            try:
                gps.configure(on_location=self.on_location_update)
                gps.start(minTime=1000, minDistance=0)
            except Exception as e:
                print("[GPS] Android error:", e)
                self.current_location = {"lat": 14.5995, "lon": 120.9842}
        else:
            try:
                import geocoder
                g = geocoder.ip("me")
                if g.ok:
                    self.current_location = {"lat": g.latlng[0], "lon": g.latlng[1]}
                else:
                    self.current_location = {"lat": 14.5995, "lon": 120.9842}
            except Exception:
                self.current_location = {"lat": 14.5995, "lon": 120.9842}

    def on_location_update(self, **kwargs):
        self.current_location["lat"] = kwargs.get("lat")
        self.current_location["lon"] = kwargs.get("lon")

    # -------------------- Shake Detection --------------------
    def start_shake_monitoring(self):
        if not accelerometer:
            print("[DEBUG] Shake monitoring not available on this platform.")
            return
        try:
            accelerometer.enable()
        except Exception:
            print("[DEBUG] Accelerometer could not be enabled.")
            return
        self._shake_count = 0
        self.last_x = self.last_y = self.last_z = None
        if self._shake_event:
            self._shake_event.cancel()
        self._shake_event = Clock.schedule_interval(self.check_shake, 0.1)

    def check_shake(self, dt):
        try:
            val = accelerometer.acceleration
            if not val or any(v is None for v in val[:3]):
                return
            x, y, z = val[:3]
            if self.last_x is None:
                self.last_x, self.last_y, self.last_z = x, y, z
                return
            dx, dy, dz = x - self.last_x, y - self.last_y, z - self.last_z
            magnitude = math.sqrt(dx**2 + dy**2 + dz**2)
            if magnitude > self.shake_threshold:
                self._shake_count += 1
                if self._shake_count >= self._required_consecutive:
                    self.on_trigger_detected("Shake")
                    self._shake_count = 0
            else:
                self._shake_count = 0
            self.last_x, self.last_y, self.last_z = x, y, z
        except Exception as e:
            print("[ERROR] Shake error:", e)

    def stop_shake_monitoring(self):
        if self._shake_event:
            try:
                self._shake_event.cancel()
            except Exception:
                pass

    # -------------------- Voice Recognition --------------------
    def init_vosk(self, model_path):
        if not os.path.exists(model_path):
            print(f"[DEBUG] Vosk model missing at: {model_path}")
            return

        self.voice_model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.voice_model, 16000)
        self._voice_queue = queue.Queue()
        self.is_listening = True

        if pyaudio:
            # Desktop
            self.audio_stream = pyaudio.PyAudio().open(
                format=pyaudio.paInt16, channels=1, rate=16000,
                input=True, frames_per_buffer=8192
            )
            self.audio_stream.start_stream()
            self._voice_thread = threading.Thread(target=self._desktop_voice_loop, daemon=True)
        elif IS_ANDROID and microphone:
            # Android
            self._voice_thread = threading.Thread(target=self._android_voice_loop, daemon=True)
        else:
            print("[DEBUG] No audio input available.")
            return

        self._voice_thread.start()
        self._voice_event = Clock.schedule_interval(self._process_voice_queue, 0.1)
        self.vosk_initialized = True
        print("[DEBUG] Vosk initialized and listening.")

    def _desktop_voice_loop(self):
        try:
            while self.is_listening:
                data = self.audio_stream.read(4096, exception_on_overflow=False)
                if self.recognizer.AcceptWaveform(data):
                    text = json.loads(self.recognizer.Result()).get("text", "").lower()
                    if text:
                        self._voice_queue.put(text)
                else:
                    partial = json.loads(self.recognizer.PartialResult()).get("partial", "").lower()
                    if partial:
                        self._voice_queue.put(partial)
        except Exception as e:
            print("[ERROR] Desktop voice loop error:", e)

    def _android_voice_loop(self):
        try:
            def callback(data):
                if not self.is_listening:
                    return
                if self.recognizer.AcceptWaveform(data):
                    text = json.loads(self.recognizer.Result()).get("text", "").lower()
                    if text:
                        self._voice_queue.put(text)
                else:
                    partial = json.loads(self.recognizer.PartialResult()).get("partial", "").lower()
                    if partial:
                        self._voice_queue.put(partial)

            microphone.start(callback)
            while self.is_listening:
                pass
            microphone.stop()
        except Exception as e:
            print("[ERROR] Android voice loop error:", e)

    def _process_voice_queue(self, dt):
        while not self._voice_queue.empty():
            phrase = self._voice_queue.get()
            if self.voice_phrase in phrase:
                self.on_trigger_detected("Voice")

    def stop_voice_listening(self):
        self.is_listening = False
        if self._voice_event:
            Clock.unschedule(self._voice_event)
            self._voice_event = None

        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except Exception:
                pass
            self.audio_stream = None

        if self._voice_thread:
            self._voice_thread.join(timeout=1)
            self._voice_thread = None

        if IS_ANDROID and microphone:
            try:
                microphone.stop()
            except Exception:
                pass

        print("[DEBUG] Voice listening stopped.")

    # -------------------- Trigger & Countdown --------------------
    def on_trigger_detected(self, trigger):
        print(f"[DEBUG] {trigger} detected. Starting countdown...")
        if self._countdown_event:
            return
        self._remaining_seconds = self.settings.get("countdown_seconds", 5)
        self.show_countdown_popup(trigger)
        self._countdown_event = Clock.schedule_interval(lambda dt: self._countdown_tick(trigger), 1)

    def _countdown_tick(self, trigger):
        self._remaining_seconds -= 1
        if self.countdown_popup:
            self.countdown_popup.content.children[1].text = f"Sending {trigger} alert in {self._remaining_seconds} sec"
        if self._remaining_seconds <= 0:
            self.cancel_countdown()
            self.send_alert(trigger)

    def cancel_countdown(self, *args):
        if self._countdown_event:
            Clock.unschedule(self._countdown_event)
            self._countdown_event = None
        if self.countdown_popup:
            self.countdown_popup.dismiss()
            self.countdown_popup = None

    def show_countdown_popup(self, trigger):
        if self.countdown_popup:
            return
        layout = BoxLayout(orientation="vertical", spacing=10)
        countdown_label = Label(text=f"Sending {trigger} alert in {self._remaining_seconds} sec")
        layout.add_widget(countdown_label)
        cancel_btn = Button(text="Cancel", size_hint_y=None, height=40)
        cancel_btn.bind(on_release=self.cancel_countdown)
        layout.add_widget(cancel_btn)
        self.countdown_popup = Popup(title=f"{trigger} SOS Countdown", content=layout, size_hint=(0.8, 0.4))
        self.countdown_popup.open()

    # -------------------- Send SOS --------------------
    def send_alert(self, trigger="Unknown"):
        lat, lon = self.current_location.get("lat"), self.current_location.get("lon")
        location_url = f"https://maps.google.com/?q={lat},{lon}" if lat and lon else "Location unknown"
        message = f"EMERGENCY! Trigger: {trigger}. Location: {location_url}"

        if not isinstance(self.contacts, (list, tuple)):
            print("[WARNING] contacts is not iterable. Skipping SMS sending.")
            self.contacts = []

        for contact in self.contacts:
            if isinstance(contact, dict) and "phone" in contact:
                try:
                    send_sos_message(contact, message)
                    print(f"[INFO] SOS sent to {contact['phone']}")
                except Exception as e:
                    print(f"[ERROR] Failed to send SOS to {contact}: {e}")
            else:
                print(f"[WARNING] Invalid contact skipped: {contact}")

        if notification:
            try:
                notification.notify(title=f"{trigger} SOS Alert", message="Alert sent to contacts", timeout=5)
            except Exception:
                pass

    # -------------------- Settings --------------------
    def apply_settings(self):
        # Shake
        if self.settings.get("shake_enabled"):
            self.start_shake_monitoring()
        else:
            self.stop_shake_monitoring()
        self.shake_threshold = max(2.0, 15.0 - (self.settings.get("shake_sensitivity", 5) * 1.2))

        # Voice
        if self.settings.get("voice_enabled") and not self.vosk_initialized:
            model_path = os.path.join(os.getcwd(), "vosk-model", "vosk-model-small-en-us-0.15")
            self.init_vosk(model_path)
        else:
            self.stop_voice_listening()

        # Floating button
        if self.settings.get("floating_enabled"):
            enable_floating(size=self.settings.get("button_size", 80),
                            callback=lambda: self.on_trigger_detected("Button"))
        else:
            disable_floating()

    def update_settings(self, new_settings):
        self.settings.update(new_settings)
        self.apply_settings()
