import os
import pymongo
from dotenv import load_dotenv

# Load environment variables (for security)
load_dotenv()

# MongoDB Connection String (Get from MongoDB Atlas)
MONGO_URI = os.getenv("MONGO_URI")  # Store in .env file
DB_NAME = "feline-bot"  # Database name
COLLECTION_NAME = "users"  # Collection name

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

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
