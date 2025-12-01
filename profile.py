import json
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDTextButton, MDRaisedButton
from accounts import load_accounts, save_accounts

class ProfileScreen(Screen):
    user_data = {}

    def on_pre_enter(self):
        """Fetch latest app-level user data and populate fields."""
        app = MDApp.get_running_app()
        self.user_data = app.current_user_data or {}
        self.populate_fields()

    def populate_fields(self):
        self.ids.profile_name.text = self.user_data.get("full name", "")
        self.ids.profile_contact.text = self.user_data.get("contact_number", "")
        self.ids.profile_location.text = self.user_data.get("location", "")

    # ---------------- Editing ----------------
    def ask_edit(self, field, key):
        """Make a field editable."""
        field.readonly = False

    def ask_save(self, field, key):
        """Save edited value back to user data and storage."""
        value = field.text.strip()
        if value:
            self.user_data[key] = value
            self.update_user_data()
        field.readonly = True

    def update_user_data(self):
        """Sync local user_data with app-level data and save."""
        app = MDApp.get_running_app()
        app.current_user_data = self.user_data

        # Persist changes in accounts file
        accounts = load_accounts()
        username = None
        for uname, data in accounts.items():
            if data.get("contact_number") == self.user_data.get("contact_number"):
                username = uname
                break

        if username:
            accounts[username] = self.user_data
            save_accounts(accounts)

    # ---------------- Logout ----------------
    def go_to_login(self):
        """Logs out the current user."""
        app = MDApp.get_running_app()
        app.current_user_data = None
        self.user_data = {}
        self.manager.current = "login"

    # ---------------- Delete Account ----------------
    def delete_account(self):
        """Ask confirmation before deleting account and remove from storage."""
        def cancel_delete(instance):
            dialog.dismiss()

        def confirm_delete(instance):
            app = MDApp.get_running_app()
            accounts = load_accounts()
            username_to_delete = None
            for uname, udata in accounts.items():
                if udata == app.current_user_data:
                    username_to_delete = uname
                    break

            if username_to_delete:
                del accounts[username_to_delete]
                save_accounts(accounts)
                self.show_message("Account deleted successfully.")
            app.current_user_data = None
            self.user_data = {}
            dialog.dismiss()
            self.manager.current = "login"

        dialog = MDDialog(
            title="Confirm Delete",
            text="Are you sure you want to delete your account? This action cannot be undone.",
            buttons=[
                MDTextButton(text="CANCEL", on_release=cancel_delete),
                MDRaisedButton(
                    text="DELETE",
                    md_bg_color=MDApp.get_running_app().MAROON_COLOR,
                    on_release=confirm_delete
                )
            ]
        )
        dialog.open()

    # ---------------- Helper ----------------
    def show_message(self, message):
        """Show a simple dialog message."""
        dialog = MDDialog(text=message, size_hint=(0.8, None), height=150)
        dialog.open()
