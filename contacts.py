from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
import json
import os

from floating_button import enable_floating, send_sms
from shake_voice_handler import SOSHandler

DATA_FILE = "contacts.json"
CATEGORIES = ["THREATS", "ACCIDENTS", "FIRE", "MEDICAL", "ONE TAP EMERGENCY"]

# -------------------- Load Contacts --------------------
def load_contacts_file():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return [c for c in data if isinstance(c, dict) and "name" in c and "phone" in c and "categories" in c]
    except:
        return []

contacts = load_contacts_file()

# -------------------- Send SMS --------------------
def send_sms_to_category(category, message):
    filtered_contacts = [c for c in contacts if category in c.get("categories", [])]
    for c in filtered_contacts:
        send_sms(c["phone"], message)

# -------------------- Contacts Screen --------------------
class ContactsScreen(Screen):
    selected_contact = None

    def on_kv_post(self, base_widget):
        self.category_checks = {}
        self.add_form_categories_dict = {}
        self.inputs_visible = False
        self.setup_category_checkboxes()
        self.load_contacts()

        # Initialize SOSHandler for floating button
        self.sos_handler = SOSHandler(
            app=self.parent,
            settings={
                "shake_enabled": False,
                "voice_enabled": False,
                "floating_enabled": True,
                "countdown_seconds": 5
            },
            contacts=[]
        )

        # Floating button callback
        def floating_callback():
            active_cats = [cat for cat, chk in self.category_checks.items() if chk.active]
            show_all = "ALL" in active_cats
            filtered_contacts = [c for c in contacts if show_all or any(cat in c["categories"] for cat in active_cats)]
            self.sos_handler.contacts = filtered_contacts
            self.sos_handler.on_trigger_detected("Button")

        enable_floating(size=80, callback=floating_callback)

    # -------------------- Category Checkboxes --------------------
    def setup_category_checkboxes(self):
        layout = self.ids.cat_layout
        layout.clear_widgets()

        # ALL checkbox
        all_chk = CheckBox(active=True)
        all_lbl = Label(text="ALL", size_hint_x=None, width=150, color=(1,1,1,1))
        box = BoxLayout(size_hint_y=None, height=30)
        box.add_widget(all_chk)
        box.add_widget(all_lbl)
        layout.add_widget(box)
        all_chk.bind(active=self.on_all_checkbox)
        self.category_checks["ALL"] = all_chk

        # Individual categories
        for cat in CATEGORIES:
            chk = CheckBox(active=True)
            lbl = Label(text=cat, size_hint_x=None, width=150, color=(1,1,1,1))
            box = BoxLayout(size_hint_y=None, height=30)
            box.add_widget(chk)
            box.add_widget(lbl)
            layout.add_widget(box)
            chk.bind(active=self.update_contacts_display)
            self.category_checks[cat] = chk

    # -------------------- Load / Update Contacts --------------------
    def load_contacts(self):
        self.update_contacts_display()

    def update_contacts_display(self, *args):
        grid = self.ids.contacts_grid
        grid.clear_widgets()

        active_cats = [cat for cat, chk in self.category_checks.items() if chk.active]
        show_all = "ALL" in active_cats

        filtered = [c for c in contacts if show_all or any(cat in c["categories"] for cat in active_cats)]
        if not filtered:
            grid.add_widget(Label(text="No contacts to display.", size_hint_y=None, height=30, color=(1,1,1,1)))
            return

        for c in filtered:
            cat_text = ", ".join(c["categories"])
            box = BoxLayout(size_hint_y=None, height=60, spacing=5)

            # Contact info label
            lbl = Label(text=f"{c['name']} ({c['phone']})\n[{cat_text}]", color=(1,1,1,1))
            box.add_widget(lbl)

            # Edit button
            edit_btn = Button(text="Edit", size_hint_x=None, width=60, background_color=(1,0,0,1), color=(1,1,1,1))
            edit_btn.bind(on_release=lambda inst, contact=c: self.edit_contact(contact))
            box.add_widget(edit_btn)

            # Delete button
            del_btn = Button(text="Delete", size_hint_x=None, width=60, background_color=(0.5,0,0,1), color=(1,1,1,1))
            del_btn.bind(on_release=lambda inst, contact=c: self.remove_contact(contact))
            box.add_widget(del_btn)

            # SMS button
            sms_btn = Button(text="SMS", size_hint_x=None, width=60, background_color=(1,0,0,1), color=(1,1,1,1))
            sms_btn.bind(on_release=lambda inst, contact=c: self.send_sms(contact))
            box.add_widget(sms_btn)

            grid.add_widget(box)

    def on_all_checkbox(self, checkbox, value):
        if value:
            for cat, chk in self.category_checks.items():
                if cat != "ALL":
                    chk.active = True
        else:
            if not any(chk.active for cat, chk in self.category_checks.items() if cat != "ALL"):
                checkbox.active = True
        self.update_contacts_display()

    def delete_selected_contact(self):
        # Get the currently selected contact
        if self.selected_contact is None:
            self.show_popup("Error", "No contact selected!")
            return

        contact = contacts[self.selected_contact]
        contacts.remove(contact)
        self.selected_contact = None
        self.save_contacts()
        self.load_contacts()

    # -------------------- Add Contact Form --------------------
    def show_add_form(self):
        self.inputs_visible = not self.inputs_visible
        self.ids.add_form.opacity = 1 if self.inputs_visible else 0
        self.ids.add_form.disabled = not self.inputs_visible
        if self.inputs_visible:
            self.clear_fields()
            self.setup_add_form_categories()

    def setup_add_form_categories(self):
        grid = self.ids.add_cat_grid
        grid.clear_widgets()
        self.add_form_categories_dict = {}

        for cat in CATEGORIES:
            box = BoxLayout(size_hint_y=None, height=30, spacing=5)
            chk = CheckBox(active=False)
            lbl = Label(text=cat, size_hint_x=None, width=150, color=(1,1,1,1))
            box.add_widget(chk)
            box.add_widget(lbl)
            grid.add_widget(box)
            self.add_form_categories_dict[cat] = chk

    def add_or_update_contact(self):
        name = self.ids.name_input.text.strip()
        phone = self.ids.phone_input.text.strip()
        categories = [cat for cat, chk in self.add_form_categories_dict.items() if chk.active]

        if not name or not phone or not categories:
            self.show_popup("Error", "Name, phone, and at least one category required!")
            return

        global contacts
        data = {"name": name, "phone": phone, "categories": categories}

        if self.selected_contact is not None:
            contacts[self.selected_contact] = data
            self.selected_contact = None
        else:
            contacts.append(data)

        self.save_contacts()
        self.clear_fields()
        self.show_add_form()  # hide form
        self.load_contacts()

    def clear_fields(self):
        self.ids.name_input.text = ""
        self.ids.phone_input.text = ""
        self.selected_contact = None
        self.ids.add_contact_btn.text = "+"

    # -------------------- Edit / Remove / Send --------------------
    def edit_contact(self, contact):
        idx = contacts.index(contact)
        self.selected_contact = idx
        self.ids.name_input.text = contact["name"]
        self.ids.phone_input.text = contact["phone"]
        self.show_add_form()
        for cat, chk in self.add_form_categories_dict.items():
            chk.active = cat in contact["categories"]
        self.ids.add_contact_btn.text = "Update"

    def remove_contact(self, contact):
        global contacts
        if contact in contacts:
            contacts.remove(contact)
        self.save_contacts()
        self.load_contacts()

    def send_sms(self, contact):
        message = "This is a test SOS message."  # replace with your message logic
        send_sms(contact["phone"], message)
        self.show_popup("SMS Sent", f"Message sent to {contact['name']}")

    # -------------------- Save / Popup --------------------
    def save_contacts(self):
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(contacts, f, indent=4)
        except Exception as e:
            self.show_popup("Error", f"Failed to save contacts: {e}")

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message, color=(0,0,0,1)), size_hint=(0.7, 0.3))
        popup.open()
