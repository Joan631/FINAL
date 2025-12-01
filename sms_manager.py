import json
from datetime import datetime
from kivy.utils import platform
from kivy.clock import Clock

# -------------------------------------------------------
# PLATFORM CHECK
# -------------------------------------------------------
IS_ANDROID = platform == "android"

if IS_ANDROID:
    from jnius import autoclass, PythonJavaClass, java_method

    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    IntentFilter = autoclass('android.content.IntentFilter')
    SmsMessage = autoclass('android.telephony.SmsMessage')

else:
    PythonJavaClass = object

    def java_method(*args, **kwargs):
        def wrapper(func):
            return func
        return wrapper

    PythonActivity = None
    SmsMessage = None


# -------------------------------------------------------
# LOCAL DATABASE (WORKS ON BOTH WIN + ANDROID)
# -------------------------------------------------------
DB_FILE = "spam_messages.json"


def init_db():
    try:
        with open(DB_FILE, "r") as f:
            json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(DB_FILE, "w") as f:
            json.dump({"messages": []}, f, indent=4)


def load_spam():
    """Load stored spam + threat messages."""
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f).get("messages", [])
    except:
        return []


def save_spam(messages):
    """Append new spam messages to database."""
    all_msgs = load_spam()
    all_msgs.extend(messages)

    with open(DB_FILE, "w") as f:
        json.dump({"messages": all_msgs}, f, indent=4)


def get_grouped_spam():
    """Return dict for UI: all, spam count, threat count."""
    all_msgs = load_spam()
    spam = sum(1 for m in all_msgs if m["category"] == "spam")
    threat = sum(1 for m in all_msgs if m["category"] == "threat")

    return {"all": all_msgs, "spam": spam, "threat": threat}


# -------------------------------------------------------
# SPAM / THREAT CLASSIFICATION RULES
# -------------------------------------------------------
SPAM_KEYWORDS = ["free", "win", "prize", "claim", "₱", "lottery"]
THREAT_KEYWORDS = ["kill", "hurt", "attack", "bomb", "shoot"]


def classify_message(message):
    text = message.lower()
    if any(word in text for word in THREAT_KEYWORDS):
        return "threat"
    elif any(word in text for word in SPAM_KEYWORDS):
        return "spam"
    return "normal"


def filter_messages(messages):
    """Filter inbox messages into spam/threat entries."""
    filtered = []
    for msg in messages:
        category = classify_message(msg["body"])
        if category != "normal":
            filtered.append({
                "address": msg["address"],
                "message": msg["body"],
                "date": msg.get("date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                "category": category
            })
    return filtered


# -------------------------------------------------------
# READ SMS INBOX (ANDROID ONLY)
# -------------------------------------------------------
def read_sms_inbox():
    """Returns SMS inbox messages. Works only on Android."""
    if not IS_ANDROID:
        print("read_sms_inbox() called on PC — returning empty list.")
        return []

    activity = PythonActivity.mActivity
    cr = activity.getContentResolver()
    Uri = autoclass('android.net.Uri')
    sms_uri = Uri.parse("content://sms/inbox")

    cursor = cr.query(sms_uri, None, None, None, None)
    messages = []

    if cursor and cursor.moveToFirst():
        while True:
            address = cursor.getString(cursor.getColumnIndex("address"))
            body = cursor.getString(cursor.getColumnIndex("body"))
            timestamp = cursor.getLong(cursor.getColumnIndex("date"))

            date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

            messages.append({
                "address": address,
                "body": body,
                "date": date,
            })

            if not cursor.moveToNext():
                break

    if cursor:
        cursor.close()

    return messages

# -------------------------------------------------------
# BLOCK SPAM FUNCTION
# -------------------------------------------------------
BLOCKED_SMS_FILE = "blocked_messages.json"

def load_blocked_sms():
    """Load blocked messages (for local app storage)."""
    try:
        with open(BLOCKED_SMS_FILE, "r") as f:
            return json.load(f).get("messages", [])
    except:
        return []

def save_blocked_sms(messages):
    """Save blocked messages locally."""
    all_msgs = load_blocked_sms()
    all_msgs.extend(messages)
    with open(BLOCKED_SMS_FILE, "w") as f:
        json.dump({"messages": all_msgs}, f, indent=4)

def block_sms(message_dict):
    """
    Save a spam message to blocked messages.
    message_dict should contain: address, message, date, category
    """
    save_blocked_sms([message_dict])

# -------------------------------------------------------
# REAL-TIME SMS RECEIVER (ANDROID ONLY)
# -------------------------------------------------------
class SMSReceiver(PythonJavaClass if IS_ANDROID else object):
    if IS_ANDROID:
        __javainterfaces__ = ['android/content/BroadcastReceiver']
        __javacontext__ = 'app'

    def __init__(self, update_callback=None):
        if IS_ANDROID:
            super().__init__()
        self.update_callback = update_callback

    # Only implemented on Android
    if IS_ANDROID:
        @java_method('(Landroid/content/Context;Landroid/content/Intent;)V')
        def onReceive(self, context, intent):
            extras = intent.getExtras()
            if extras and extras.containsKey("pdus"):
                pdus = extras.get("pdus")
                new_msgs = []

                for pdu in pdus:
                    sms = SmsMessage.createFromPdu(pdu)
                    body = sms.getMessageBody()
                    sender = sms.getOriginatingAddress()

                    category = classify_message(body)

                    if category != "normal":
                        new_msgs.append({
                            "address": sender,
                            "message": body,
                            "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "category": category
                        })
                    
                if new_msgs:
                    save_spam(new_msgs)
                    if self.update_callback:
                        Clock.schedule_once(lambda dt: self.update_callback())