import pandas as pd
import numpy as np


class PredictionEngine:
    def __init__(self, db_manager):
        self.db = db_manager

    def simple_linear_regression(self, x, y):
        n = len(x)

        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)

        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return None, None

        m = (n * sum_xy - sum_x * sum_y) / denominator
        c = (sum_y - m * sum_x) / n

        return m, c

    #getting user progrss from db
    def get_user_progress(self, user_id):
        self.db.cursor.execute("""
            SELECT w.date, e.name, SUM(s.weight * s.reps) AS total_volume
            FROM sets s
            JOIN exercises e ON e.id = s.exercise_id
            JOIN workouts w ON w.id = e.workout_id
            WHERE w.user_id = ?
            GROUP BY w.date, e.name
            ORDER BY w.date ASC
        """, (user_id,))
        rows = self.db.cursor.fetchall()

        if not rows:
            return pd.DataFrame(columns=["date", "exercise", "total_volume"])

        df = pd.DataFrame(rows, columns=["date", "exercise", "total_volume"])
        df["date"] = pd.to_datetime(df["date"])
        return df

    #predicting volume with linear regression
    def predict_next_volume(self, user_id, exercise_name):
        df = self.get_user_progress(user_id)
        exercise_df = df[df["exercise"] == exercise_name].copy()

        if exercise_df.empty or len(exercise_df) < 3:
            print("Not enough data to predict.")
            return None, None

        exercise_df = exercise_df.sort_values("date")
        exercise_df["day_index"] = np.arange(len(exercise_df))

        x = exercise_df["day_index"].to_numpy()
        y = exercise_df["total_volume"].to_numpy()

        m, c = self.simple_linear_regression(x, y)
        if m is None:
            return None, None

        next_x = x[-1] + 1
        predicted_volume = m * next_x + c

        if predicted_volume < y[-1]:
            predicted_volume = y[-1] + abs(m) * 1.5

        return exercise_df, float(predicted_volume)

    #predicting bodyweight with linear regression
    def predict_next_weight(self, user_id):
        self.db.cursor.execute("""
    SELECT date, current_weight AS weight
    FROM user_info_entry
    WHERE user_id = ? AND current_weight IS NOT NULL
    ORDER BY date ASC
""", (user_id,))

        rows = self.db.cursor.fetchall()

        if not rows or len(rows) < 3:
            print("Not enough data to predict.")
            return None, None

        df = pd.DataFrame(rows, columns=["date", "weight"])
        df["date"] = pd.to_datetime(df["date"])
        df["day_index"] = (df["date"] - df["date"].min()).dt.days

        x = df["day_index"].to_numpy()
        y = df["weight"].to_numpy()

        m, c = self.simple_linear_regression(x, y)
        if m is None:
            return None, None

        next_day = x[-1] + 7
        predicted_weight = m * next_day + c

        if predicted_weight > y[-1] and y[-1] < y[0]:
            predicted_weight = y[-1] - abs(m) * 3

        return df, float(predicted_weight)
