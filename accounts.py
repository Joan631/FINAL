# accounts.py
import json

ACCOUNTS_FILE = "accounts.json"

def load_accounts():
    try:
        with open(ACCOUNTS_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                new_data = {}
                for user in data:
                    if 'username' in user:
                        new_data[user['username']] = {
                            'name': user.get('name', ''),
                            'lastname': user.get('lastname', ''),
                            'email': user.get('email', ''),
                            'contact_number': user.get('contact_number', ''),
                            'location': user.get('location', ''),
                            'password': user.get('password', '')
                        }
                return new_data
            elif isinstance(data, dict):
                return data
            else:
                return {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=4)
