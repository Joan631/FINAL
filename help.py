from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.lang import Builder


FAQ_DATA = [
    {"q": "How do I edit my profile information?",
     "a": "Navigate to the Profile screen, tap the 'Edit Profile' button, modify the fields, then tap 'Save Changes'."},
    {"q": "What do the status options mean?",
     "a": "The status options indicate your current availability. Tap the status button to cycle through them."},
    {"q": "How can I log out of the application?",
     "a": "Tap the 'Log Out' button on the Profile screen to end your session."},
    {"q": "How do I enable the Shake feature?",
     "a": "In Settings, toggle the 'Shake to Alert' option. Shaking your device will send an alert to your contacts."},
    {"q": "How do I enable Voice alerts?",
     "a": "In Settings, turn on 'Voice Alerts'. Ensure microphone permissions are granted."},
    {"q": "How do I update my location?",
     "a": "On the Profile screen, tap 'Update Location'. The app will use GPS to update your location automatically."},
    {"q": "How do I add contacts?",
     "a": "Navigate to the Contacts tab, tap '+', enter contact details, and save."},
    {"q": "What happens when I delete a contact?",
     "a": "Deleted contacts are permanently removed. They no longer receive alerts or updates."},
    {"q": "Can I change my profile picture?",
     "a": "Place a new image named 'logo.png.jpg' in the resources folder. The app will display the new image automatically."},
    {"q": "What should I do if the app is not responding?",
     "a": "Close the app completely and reopen it. If the problem persists, restart your device or reinstall the app."},
    {"q": "How do I reset my preferences?",
     "a": "Go to Settings, then tap 'Reset Preferences' to restore default settings."}
]

class HelpScreen(Screen):
    def on_pre_enter(self):
        # Populate FAQs each time screen is shown
        self.populate_faqs(FAQ_DATA)

    def _create_faq_entry(self, question, answer):
        entry = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5), padding=[dp(5), 0])

        question_label = Label(
            text=f"[b]Q: {question}[/b]",
            markup=True,
            halign='left',
            valign='top',
            size_hint_y=None,
            color=get_color_from_hex('#800000'),
            text_size=(self.width - dp(30), None)
        )
        question_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', inst.texture_size[1]))

        answer_label = Label(
            text=f"A: {answer}",
            halign='left',
            valign='top',
            size_hint_y=None,
            color=get_color_from_hex('#800000'),
            text_size=(self.width - dp(30), None)
        )
        answer_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', inst.texture_size[1] + dp(5)))

        entry.bind(width=lambda instance, value: [
            setattr(question_label, 'text_size', (value - dp(30), None)),
            setattr(answer_label, 'text_size', (value - dp(30), None))
        ])

        entry.add_widget(question_label)
        entry.add_widget(answer_label)
        return entry

    def populate_faqs(self, faqs_to_display):
        container = self.ids.faq_list_container
        container.clear_widgets()
        for faq in faqs_to_display:
            container.add_widget(self._create_faq_entry(faq['q'], faq['a']))
        container.add_widget(Label(size_hint_y=None, height=dp(20)))

    def filter_faqs(self, search_text):
        term = search_text.lower().strip()
        if not term:
            self.populate_faqs(FAQ_DATA)
            return
        filtered = [faq for faq in FAQ_DATA if term in faq['q'].lower() or term in faq['a'].lower()]
        self.populate_faqs(filtered)
