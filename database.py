from pymongo import MongoClient
from cryptography.fernet import Fernet
from config import DB_URI, DB_NAME, LOGGER
import datetime, json, os, time

# ---------- ENCRYPTION KEY ----------
KEY_FILE = "secret.key"

if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "wb") as f:
        f.write(Fernet.generate_key())

with open(KEY_FILE, "rb") as f:
    KEY = f.read()

cipher = Fernet(KEY)

# ---------- AUTO DELETE SETTINGS ----------
AUTO_DELETE_DAYS = 7   # yahan days change kar sakte ho

# =========================================

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.files = None
        self.users = None
        self.batches = None
        self.backups = None
        self.connect()
        self.auto_delete_old_files()

    # ---------- CONNECT ----------
    def connect(self):
        try:
            self.client = MongoClient(DB_URI, serverSelectionTimeoutMS=5000)
            self.client.server_info()

            self.db = self.client[DB_NAME]
            self.files = self.db.files
            self.users = self.db.users
            self.batches = self.db.batches
            self.backups = self.db.backups

            LOGGER(__name__).info("MongoDB Connected Successfully")

        except Exception as e:
            LOGGER(__name__).error(f"MongoDB Error: {e}")
            self.client = None

    def check(self):
        if not self.client:
            self.connect()

    # ---------- ENCRYPT / DECRYPT ----------
    def encrypt(self, text):
        return cipher.encrypt(text.encode()).decode()

    def decrypt(self, text):
        return cipher.decrypt(text.encode()).decode()

    # ---------- USER ----------
    def add_user(self, user_id):
        self.check()
        try:
            if not self.users.find_one({"_id": user_id}):
                self.users.insert_one({"_id": user_id, "time": time.time()})
        except Exception as e:
            LOGGER(__name__).error(e)

    def total_users(self):
        self.check()
        try:
            return self.users.count_documents({})
        except:
            return 0

    # ---------- FILE SAVE WITH DUPLICATE CHECK ----------
    def save_file(self, file_id, message_id, title):
        self.check()
        enc_file = self.encrypt(file_id)

        if self.files.find_one({"file_id": enc_file}):
            return False

        self.files.insert_one({
            "file_id": enc_file,
            "message_id": message_id,
            "title": title,
            "time": time.time()
        })
        return True

    def get_file(self, message_id):
        self.check()
        data = self.files.find_one({"message_id": message_id})
        if data:
            data["file_id"] = self.decrypt(data["file_id"])
        return data

    # ---------- BATCH ----------
    def save_batch(self, batch_id, message_ids):
        self.check()
        if not self.batches.find_one({"batch_id": batch_id}):
            self.batches.insert_one({
                "batch_id": batch_id,
                "message_ids": message_ids,
                "time": time.time()
            })

    def get_batch(self, batch_id):
        self.check()
        return self.batches.find_one({"batch_id": batch_id})

    # ---------- AUTO DELETE OLD FILES ----------
    def auto_delete_old_files(self):
        self.check()
        try:
            limit = time.time() - (AUTO_DELETE_DAYS * 86400)
            deleted = self.files.delete_many({"time": {"$lt": limit}})
            if deleted.deleted_count:
                LOGGER(__name__).info(f"Auto Deleted {deleted.deleted_count} old files from DB")
        except Exception as e:
            LOGGER(__name__).error(f"Auto delete error: {e}")

    # ---------- AUTO BACKUP ----------
    def backup_database(self):
        self.check()
        data = {
            "files": list(self.files.find({})),
            "users": list(self.users.find({})),
            "batches": list(self.batches.find({})),
            "time": str(datetime.datetime.now())
        }

        self.backups.insert_one(data)

        with open("db_backup.json", "w", encoding="utf-8") as f:
            json.dump(data, f, default=str, indent=4)

    # ---------- MANUAL CLEAN ----------
    def clear_files(self):
        self.check()
        self.files.delete_many({})

    # ---------- CLOSE ----------
    def close(self):
        if self.client:
            self.client.close()
