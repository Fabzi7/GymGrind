import hashlib

class User:
    def __init__(self, username, password):
        self.username = username
        self.hashed_password = self.hash_password(password)
        self.streak = 0

