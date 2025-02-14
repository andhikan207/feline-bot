import os
import pymongo
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# MongoDB Connection String
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "feline-bot"
COLLECTION_NAME = "users"

if not MONGO_URI:
    raise RuntimeError("❌ MONGO_URI is not set. Check your .env file!")

try:
    # Connect to MongoDB
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    raise RuntimeError(f"❌ MongoDB Connection Error: {e}")

def get_user_data(user_id):
    """Fetch user data from MongoDB. Create one if not exists."""
    user = collection.find_one({"_id": user_id})
    if not user:
        user = {"_id": user_id, "timezone": "UTC", "reminders": []}
        collection.insert_one(user)
    return user

def update_timezone(user_id, timezone):
    """Update the user's timezone."""
    collection.update_one({"_id": user_id}, {"$set": {"timezone": timezone}}, upsert=True)

def add_reminder(user_id, reminder_data):
    """Add a reminder to the user's reminders array."""
    collection.update_one({"_id": user_id}, {"$push": {"reminders": reminder_data}}, upsert=True)

def get_reminders(user_id):
    """Retrieve all reminders for a user."""
    user = get_user_data(user_id)
    return user.get("reminders", [])

def remove_reminder(user_id, task):
    """Remove a reminder by task name."""
    collection.update_one({"_id": user_id}, {"$pull": {"reminders": {"task": task}}})
