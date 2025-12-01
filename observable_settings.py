from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.event import EventDispatcher

class ObservableSettings(EventDispatcher):
    # Shake
    shake_enabled = BooleanProperty(False)
    shake_sensitivity = NumericProperty(5)

    # Voice
    voice_enabled = BooleanProperty(False)
    voice_phrase = StringProperty("help me")
    voice_sensitivity = NumericProperty(5)

    # Floating button
    floating_enabled = BooleanProperty(True)
    button_size = NumericProperty(50)

    # Lock screen
    lock_screen = BooleanProperty(False)

    # Countdown
    countdown_enabled = BooleanProperty(True)
    countdown_seconds = NumericProperty(5)
