from datetime import date
from password_utils import salted_matrix_xor_hash, verify_salted, make_salt
from datetime import datetime

class UserProfileManager:
    def __init__(self, db):
        self.db = db

    def get_profile(self, user_id):
        self.db.cursor.execute("""
            SELECT username, target_weight, streak, last_log_date, date_created, theme, accent_colour, notifications
            FROM users WHERE user_id=?
        """, (user_id,))
        row = self.db.cursor.fetchone()
        if not row:
            return None
        keys = ["username", "target_weight", "streak", "last_log_date", "date_created", "theme", "accent_colour", "notifications"]
        return dict(zip(keys, row))

    def update_profile(self, user_id, username=None, target_weight=None, theme=None, accent_colour=None):
        if username and len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if target_weight is not None and target_weight <= 0:
            raise ValueError("Target weight must be positive")

        self.db.cursor.execute("""
            UPDATE users SET
                username = COALESCE(?, username),
                target_weight = COALESCE(?, target_weight),
                theme = COALESCE(?, theme),
                accent_colour = COALESCE(?, accent_colour)
            WHERE user_id=?
        """, (username, target_weight, theme, accent_colour, user_id))
        self.db.conn.commit()

    def update_streak(self, user_id):
        today = date.today().isoformat()
        self.db.cursor.execute("SELECT last_log_date, streak FROM users WHERE user_id=?", (user_id,))
        row = self.db.cursor.fetchone()
        if not row:
            return
        last_log_date, streak = row
        if not last_log_date:
            streak = 1
        else:
            diff = (datetime.strptime(today, "%Y-%m-%d") - datetime.strptime(last_log_date, "%Y-%m-%d")).days
            streak = streak + 1 if diff <= 3 else 0
        self.db.cursor.execute("UPDATE users SET streak=?, last_log_date=? WHERE user_id=?", (streak, today, user_id))
        self.db.conn.commit()

    def change_password(self, user_id, current_pw, new_pw):
        self.db.cursor.execute("SELECT hashed_password, salt FROM users WHERE user_id=?", (user_id,))
        row = self.db.cursor.fetchone()
        if not row:
            raise ValueError("User not found")
        stored_hash, stored_salt = row
        if not verify_salted(current_pw, stored_salt, stored_hash):
            raise ValueError("Incorrect current password")

        new_salt = make_salt()
        new_hash = salted_matrix_xor_hash(new_pw, new_salt)
        self.db.cursor.execute("UPDATE users SET hashed_password=?, salt=? WHERE user_id=?", (new_hash, new_salt, user_id))
        self.db.conn.commit()
