# database_manager.py
import sqlite3
import random
from datetime import date, timedelta
from password_utils import make_salt, salted_matrix_xor_hash, verify_salted
from default_workouts import get_default_workouts
from default_foods import get_default_foods



class DatabaseManager:
    def __init__(self, db_name="gymgrind.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name, check_same_thread=True)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        
        self.create_tables()
        self.ensure_exercise_has_muscle_group()
        self.populate_default_workouts()
        self.populate_default_foods()
        self.backfill_muscle_groups()

    def create_tables(self):
        # users
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                salt BLOB,
                target_weight REAL DEFAULT NULL,
                streak INTEGER DEFAULT 0,
                date_created TEXT DEFAULT (date('now')),
                theme TEXT DEFAULT 'dark',
                accent_colour TEXT DEFAULT '#00c853',
                notifications INTEGER DEFAULT 1,
                last_workout_date TEXT DEFAULT NULL
            )
    """)

        # workouts
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                muscle_group TEXT,
                date TEXT NOT NULL,
                total_volume REAL DEFAULT 0,
                weight REAL DEFAULT NULL,
                calories INTEGER DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
                    """)

        # exercises
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                sets INTEGER DEFAULT 0,
                total_volume REAL DEFAULT 0,
                muscle_group TEXT,
                FOREIGN KEY (workout_id) REFERENCES workouts(id)
        )
                """)

        # sets
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_id INTEGER NOT NULL,
                workout_id INTEGER, 
                reps INTEGER NOT NULL,
                weight REAL NOT NULL,
                FOREIGN KEY (exercise_id) REFERENCES exercises(id),
                FOREIGN KEY (workout_id) REFERENCES workouts(id)
                    
                )
                """)

        # default workouts
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS default_workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                muscle_group TEXT NOT NULL
                )
                    """)

        #default foods
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS foods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                calories REAL NOT NULL,
                protein REAL NOT NULL,
                carbs REAL NOT NULL,
                fats REAL NOT NULL,
                notes TEXT DEFAULT NULL
                )
        """)

        # daily_nutrition - manual daily totals override (optional)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS food_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                food_name TEXT NOT NULL,
                calories REAL NOT NULL,
                protein REAL NOT NULL,
                carbs REAL NOT NULL,
                fats REAL NOT NULL,
                UNIQUE(user_id, date, food_name),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )

        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_info_entry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                current_weight REAL,  
                calories_consumed INTEGER,
                UNIQUE(user_id, date),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                            )
                        """)
    
        
        

        self.conn.commit()

    #filling tables up 
    def ensure_exercise_has_muscle_group(self):
        self.cursor.execute("PRAGMA table_info(exercises)")
        cols = [r[1] for r in self.cursor.fetchall()]
        if "muscle_group" not in cols:
            try:
                self.cursor.execute("ALTER TABLE exercises ADD COLUMN muscle_group TEXT")
                self.conn.commit()
            except Exception:
                pass

    def populate_default_workouts(self):
        default = get_default_workouts()
        if default:
            self.cursor.executemany(
                "INSERT OR IGNORE INTO default_workouts (name, muscle_group) VALUES (?, ?)",
                default
            )
            self.conn.commit()

    def populate_default_foods(self):
        foods = get_default_foods()
        if not foods:
            return

        self.cursor.executemany("""
            INSERT OR IGNORE INTO foods
            (name, calories, protein, carbs, fats)
            VALUES (?, ?, ?, ?, ?)
        """, foods)

        self.conn.commit()


    def backfill_muscle_groups(self):
        try:
            self.cursor.execute("SELECT name, muscle_group FROM default_workouts")
            mapping = dict(self.cursor.fetchall())
            self.cursor.execute(
                "SELECT id, name FROM exercises WHERE muscle_group IS NULL OR TRIM(muscle_group) = ''"
            )
            missing = self.cursor.fetchall()
            for ex in missing:
                ex_id = ex[0]
                ex_name = ex[1]
                mg = mapping.get(ex_name)
                if mg:
                    self.cursor.execute("UPDATE exercises SET muscle_group = ? WHERE id = ?", (mg, ex_id))
            self.conn.commit()
        except Exception:
            pass

    def get_latest_weight(self, user_id):
        self.cursor.execute("""
            SELECT current_weight
            FROM user_info_entry
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT 1
        """, (user_id,))
        row = self.cursor.fetchone()
        return row["current_weight"] if row else None

    #user management and authorisation
    def add_user(self, username: str, password: str) -> bool:
        try:
            salt = make_salt()
            hashed = salted_matrix_xor_hash(password, salt)
            self.cursor.execute(
                "INSERT INTO users (username, hashed_password, salt) VALUES (?, ?, ?)",
                (username, hashed, salt)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def validate_user(self, username: str, password: str) -> bool:
        self.cursor.execute("SELECT hashed_password, salt FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()
        if not row:
            return False
        stored_hash = row["hashed_password"]
        stored_salt = row["salt"]
        return verify_salted(password, stored_salt, stored_hash)

    def get_user_id(self, username: str):
        self.cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()
        return row["user_id"] if row else None
    
    def get_weight_data(self, user_id):
        pass
        #self.cursor.execute("SELECT ")

    #testing predictions engine


    def insert_fake_weight_data(self, user_id, trend, days=30, start_weight=80):

        for i in range(days):
            if trend == "up":
                day = date.today() - timedelta(days=days - i)
                weight = start_weight + i*3 + random.uniform(-2,2)  # small trend + randomness
                self.cursor.execute("""
                    INSERT OR REPLACE INTO user_info_entry (user_id, date, current_weight, calories_consumed)
                    VALUES (?, ?, ?, COALESCE(
                        (SELECT calories_consumed FROM user_info_entry WHERE user_id=? AND date=?),
                        2000
                    ))
                """, (user_id, day.isoformat(), round(weight,1), user_id, day.isoformat()))
            elif trend == "down":
                day = date.today() - timedelta(days=days - i)
                weight = start_weight + i*-0.2 + random.uniform(-3,3)  # small trend + randomness
                self.cursor.execute("""
                    INSERT OR REPLACE INTO user_info_entry (user_id, date, current_weight, calories_consumed)
                    VALUES (?, ?, ?, COALESCE(
                        (SELECT calories_consumed FROM user_info_entry WHERE user_id=? AND date=?),
                        2000
                    ))
                """, (user_id, day.isoformat(), round(weight,1), user_id, day.isoformat()))

        self.conn.commit()




    def insert_fake_workout_data(self, user_id, days=30, trend="up"):
        try:
            print("INSERT FAKE DATA CALLED")
            # Pick existing exercises
            self.cursor.execute("SELECT id FROM exercises")
            exercise_ids = [row[0] for row in self.cursor.fetchall()]
            if not exercise_ids:
                raise ValueError("No exercises found in database")

            base_weight = 40.0
            base_reps = 8

            for day_offset in range(0, days, 3):  # workout every 3 days
                workout_date = date.today() - timedelta(days=days - day_offset)
                workout_name = f"Workout {workout_date.isoformat()}"

                # Insert workout
                self.cursor.execute("""
                    INSERT INTO workouts (user_id, name, date)
                    VALUES (?, ?, ?)
                """, (user_id, workout_name, workout_date.isoformat()))
                workout_id = self.cursor.lastrowid

                progression = day_offset / days
                if trend == "down":
                    progression *= -1

                # Randomly pick 3 exercises per workout
                for exercise_id in random.sample(exercise_ids, k=min(3, len(exercise_ids))):
                    weight = base_weight + progression * 20 + random.uniform(-2, 2)
                    reps = max(5, base_reps + int(progression * 4) + random.randint(-1, 1))

                    for _ in range(3):
                        self.cursor.execute("""
                            INSERT INTO sets (workout_id, exercise_id, weight, reps)
                            VALUES (?, ?, ?, ?)
                        """, (workout_id, exercise_id, round(weight, 1), reps))

                    self.cursor.execute("""
                        UPDATE exercises
                        SET total_volume = (SELECT SUM(reps * weight) FROM sets WHERE exercise_id = ?),
                            sets = (SELECT COUNT(*) FROM sets WHERE exercise_id = ?)
                        WHERE id = ?
                    """, (exercise_id, exercise_id, exercise_id))

                self.cursor.execute("""
                    UPDATE workouts
                    SET total_volume = (SELECT COALESCE(SUM(total_volume), 0) FROM exercises WHERE workout_id = workouts.id)
                    WHERE id = ?
                """, (workout_id,))

            print("Fake data commited")

            self.conn.commit()

        except Exception as e:
            print("Fake data error: ", e)


    #workout management
    def add_workout(self, user_id, name, muscle_group=None):
        today = date.today().isoformat()
        self.cursor.execute("""
            INSERT INTO workouts (user_id, name, muscle_group, date, total_volume)
            VALUES (?, ?, ?, ?, 0)
        """, (user_id, name, muscle_group, today))
        self.conn.commit()
        return self.cursor.lastrowid

    def add_exercise(self, workout_id, name):
        self.cursor.execute(
            "SELECT muscle_group FROM default_workouts WHERE LOWER(name) = LOWER(?)",
            (name,)
        )
        row = self.cursor.fetchone()
        muscle_group = row[0] if row else None
        self.cursor.execute("""
            INSERT INTO exercises (workout_id, name, sets, total_volume, muscle_group)
            VALUES (?, ?, 0, 0, ?)
        """, (workout_id, name, muscle_group))
        self.conn.commit()
        return self.cursor.lastrowid

    def add_set(self, exercise_id, reps, weight):
        self.cursor.execute(
            "INSERT INTO sets (exercise_id, reps, weight) VALUES (?, ?, ?)",
            (exercise_id, reps, weight)
        )
        self.conn.commit()
        self.update_total_volume(exercise_id)
        return self.cursor.lastrowid

    def update_total_volume(self, exercise_id):
        self.cursor.execute("SELECT SUM(reps * weight) FROM sets WHERE exercise_id = ?", (exercise_id,))
        volume = self.cursor.fetchone()[0] or 0.0
        self.cursor.execute("""
            UPDATE exercises
            SET total_volume = ?, sets = (SELECT COUNT(*) FROM sets WHERE exercise_id = ?)
            WHERE id = ?
        """, (volume, exercise_id, exercise_id))
        self.cursor.execute("""
            UPDATE workouts
            SET total_volume = (
                SELECT COALESCE(SUM(total_volume), 0) FROM exercises WHERE workout_id = workouts.id
            )
            WHERE id = (SELECT workout_id FROM exercises WHERE id = ?)
        """, (exercise_id,))
        self.conn.commit()

    #food management

    def search_foods_by_name(self, query: str, limit=20):
        like = f"%{query}%"
        self.cursor.execute("""
            SELECT id, name, calories, protein, carbs, fats
            FROM foods
            WHERE name LIKE ?
            ORDER BY name
            LIMIT ?
        """, (like, limit))
        return [dict(r) for r in self.cursor.fetchall()]
    
    def get_food_by_name(self, name: str):
        self.cursor.execute("""
            SELECT id, name, calories, protein, carbs, fats
            FROM foods
            WHERE name = ?
        """, (name,))
        row = self.cursor.fetchone()
        return dict(row) if row else None


    def add_food(self, name: str, calories: float, protein: float, carbs: float, fats: float, notes: str = None):
        try:
            self.cursor.execute("""
                INSERT INTO foods (name, calories, protein, carbs, fats, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name.strip(), float(calories), float(protein), float(carbs), float(fats), notes))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def update_food(self, food_id: int, name: str = None, calories: float = None,
                    protein: float = None, carbs: float = None, fats: float = None, notes: str = None):
        fields = []
        params = []
        if name is not None:
            fields.append("name = ?"); params.append(name.strip())
        if calories is not None:
            fields.append("calories = ?"); params.append(float(calories))
        if protein is not None:
            fields.append("protein = ?"); params.append(float(protein))
        if carbs is not None:
            fields.append("carbs = ?"); params.append(float(carbs))
        if fats is not None:
            fields.append("fats = ?"); params.append(float(fats))
        if notes is not None:
            fields.append("notes = ?"); params.append(notes)
        if not fields:
            return False
        params.append(food_id)
        sql = "UPDATE foods SET " + ", ".join(fields) + " WHERE id = ?"
        self.cursor.execute(sql, tuple(params))
        self.conn.commit()
        return True

    def delete_food(self, food_id: int):
        self.cursor.execute("DELETE FROM foods WHERE id = ?", (food_id,))
        self.conn.commit()

    def search_foods(self, query: str, limit: int = 50):
        like = f"%{query}%"
        self.cursor.execute("SELECT id, name, calories, protein, carbs, fats FROM foods WHERE name LIKE ? ORDER BY name LIMIT ?",
                            (like, limit))
        return [dict(r) for r in self.cursor.fetchall()]

    # Food logging 
    def log_food(self, user_id: int, food_id: int, date_iso: str, servings: float = 1.0, notes: str = None):
        self.cursor.execute("""
            INSERT INTO food_log (user_id, food_id, date, servings, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, food_id, date_iso, float(servings), notes))
        self.conn.commit()
        return self.cursor.lastrowid

    def delete_food_log(self, log_id: int):
        self.cursor.execute("DELETE FROM food_log WHERE id = ?", (log_id,))
        self.conn.commit()

    def get_food_log_for_day(self, user_id, date_iso):
        self.cursor.execute("""
            SELECT food_name, calories, protein, carbs, fats
            FROM food_log
            WHERE user_id = ? AND date = ?
            ORDER BY food_name
        """, (user_id, date_iso))
        return self.cursor.fetchall()

    #retrieving data
    def get_daily_totals_from_foods(self, user_id: int, date_iso: str):
        self.cursor.execute("""
            SELECT
                COALESCE(SUM(f.calories * fl.servings), 0) AS calories,
                COALESCE(SUM(f.protein * fl.servings), 0) AS protein,
                COALESCE(SUM(f.carbs * fl.servings), 0) AS carbs,
                COALESCE(SUM(f.fats * fl.servings), 0) AS fats
            FROM food_log fl
            JOIN foods f ON fl.food_id = f.id
            WHERE fl.user_id = ? AND fl.date = ?
        """, (user_id, date_iso))
        row = self.cursor.fetchone()
        return dict(row) if row else {"calories": 0, "protein": 0, "carbs": 0, "fats": 0}
    
    def upsert_daily_totals(self, user_id, date_iso, calories, protein, carbs, fats):
        self.cursor.execute("""
            INSERT INTO daily_totals
            (user_id, date, calories, protein, carbs, fats)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date)
            DO UPDATE SET
                calories = excluded.calories,
                protein  = excluded.protein,
                carbs    = excluded.carbs,
                fats     = excluded.fats
        """, (user_id, date_iso, calories, protein, carbs, fats))
        self.conn.commit()

    def upsert_manual_daily_totals(self, user_id: int, date_iso: str, calories=None, protein=None, carbs=None, fats=None):
        self.cursor.execute("SELECT id FROM daily_nutrition WHERE user_id = ? AND date = ?", (user_id, date_iso))
        row = self.cursor.fetchone()
        if row:
            fields = []
            params = []
            if calories is not None: fields.append("calories = ?"); params.append(float(calories))
            if protein is not None: fields.append("protein = ?"); params.append(float(protein))
            if carbs is not None: fields.append("carbs = ?"); params.append(float(carbs))
            if fats is not None: fields.append("fats = ?"); params.append(float(fats))
            if not fields:
                return False
            params.append(user_id); params.append(date_iso)
            sql = "UPDATE daily_nutrition SET " + ", ".join(fields) + " WHERE user_id = ? AND date = ?"
            self.cursor.execute(sql, tuple(params))
        else:
            self.cursor.execute("""
                INSERT INTO daily_nutrition (user_id, date, calories, protein, carbs, fats)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, date_iso, calories, protein, carbs, fats))
        self.conn.commit()
        return True

    
    def upsert_food_log(self, user_id, date_iso, food_name, calories, protein, carbs, fats):
        self.cursor.execute("""
            INSERT INTO food_log
            (user_id, date, food_name, calories, protein, carbs, fats)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date, food_name)
            DO UPDATE SET
                calories = excluded.calories,
                protein  = excluded.protein,
                carbs    = excluded.carbs,
                fats     = excluded.fats

        """, (user_id, date_iso, food_name, calories, protein, carbs, fats))
        self.conn.commit()



    def get_manual_daily_totals(self, user_id: int, date_iso: str):
        self.cursor.execute("SELECT calories, protein, carbs, fats FROM daily_nutrition WHERE user_id = ? AND date = ?", (user_id, date_iso))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_combined_daily_totals(self, user_id: int, date_iso: str):
        manual = self.get_manual_daily_totals(user_id, date_iso)
        if manual:
            return manual
        return self.get_daily_totals_from_foods(user_id, date_iso)
    
    def add_user_info(self, user_id, current_weight, calories, date_iso):
        self.cursor.execute("""INSERT INTO user_info_entry(user_id, current_weight, calories, date)
                            VALUES (?, ?, ?, ?)""", (user_id, current_weight, calories, date_iso))
        self.conn.commit()

    def get_user_info(self, user_id):
        self.cursor.execute("SELECT current_weight, calories, date FROM user_info_entry WHERE user_id = ?", (user_id,))
        rows = self.cursor.fetchall()
        return rows
    
    def get_daily_totals(self, user_id, date_iso):
        self.cursor.execute("""
            SELECT
                COALESCE(SUM(calories), 0) AS calories,
                COALESCE(SUM(protein), 0)  AS protein,
                COALESCE(SUM(carbs), 0)    AS carbs,
                COALESCE(SUM(fats), 0)     AS fats
            FROM food_log
            WHERE user_id = ? AND date = ?
        """, (user_id, date_iso))
        return dict(self.cursor.fetchone())

    #streak management
    def update_workout_streak(self, user_id):
        today = date.today()

        self.cursor.execute("""
            SELECT streak, last_workout_date
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        row = self.cursor.fetchone()

        if not row:
            return

        streak = row["streak"] or 0
        last_date_str = row["last_workout_date"]


        if not last_date_str:
            self.cursor.execute("""
                UPDATE users
                SET streak = 1, last_workout_date = ?
                WHERE user_id = ?
            """, (today.isoformat(), user_id))
            self.conn.commit()
            return

        last_date = date.fromisoformat(last_date_str)
        gap = (today - last_date).days

        if gap == 0:
            return

        # if user misses over 2 days, then their streak is gone
        if gap > 3:
            streak = 0
        else:
            streak += 1

        self.cursor.execute("""
            UPDATE users
            SET streak = ?, last_workout_date = ?
            WHERE user_id = ?
        """, (streak, today.isoformat(), user_id))

        self.conn.commit()

    def close(self):
        self.conn.close()
