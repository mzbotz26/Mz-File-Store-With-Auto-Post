from pymongo import MongoClient
from cryptography.fernet import Fernet
from config import DB_URI, DB_NAME
import datetime
import json
import os

# ---------- ENCRYPTION KEY ----------
KEY = Fernet.generate_key()  # first time auto generate
cipher = Fernet(KEY)


class Database:
    def __init__(self):
        self.client = MongoClient(DB_URI)
        self.db = self.client[DB_NAME]

        self.files = self.db.files
        self.users = self.db.users
        self.batches = self.db.batches
        self.backups = self.db.backups

    # ---------- ENCRYPT / DECRYPT ----------

    def encrypt(self, text):
        return cipher.encrypt(text.encode()).decode()

    def decrypt(self, text):
        return cipher.decrypt(text.encode()).decode()

    # ---------- USER ----------

    def add_user(self, user_id):
        if not self.users.find_one({"_id": user_id}):
            self.users.insert_one({"_id": user_id})

    # ---------- FILE SAVE WITH DUPLICATE CHECK ----------

    def save_file(self, file_id, message_id, title):
        enc_file = self.encrypt(file_id)

        if self.files.find_one({"file_id": enc_file}):
            return False  # duplicate

        self.files.insert_one({
            "file_id": enc_file,
            "message_id": message_id,
            "title": title
        })
        return True

    def get_file(self, message_id):
        data = self.files.find_one({"message_id": message_id})
        if data:
            data["file_id"] = self.decrypt(data["file_id"])
        return data

    # ---------- BATCH ----------

    def save_batch(self, batch_id, message_ids):
        self.batches.insert_one({
            "batch_id": batch_id,
            "message_ids": message_ids
        })

    def get_batch(self, batch_id):
        return self.batches.find_one({"batch_id": batch_id})

    # ---------- AUTO BACKUP ----------

    def backup_database(self):
        data = {
            "files": list(self.files.find({})),
            "users": list(self.users.find({})),
            "batches": list(self.batches.find({})),
            "time": str(datetime.datetime.now())
        }

        self.backups.insert_one(data)

        with open("db_backup.json", "w", encoding="utf-8") as f:
            json.dump(data, f, default=str, indent=4)

    # ---------- CLOSE ----------

    def close(self):
        self.client.close()
