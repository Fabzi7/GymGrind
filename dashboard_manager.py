from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QScrollArea,
    QPushButton, QFrame, QMessageBox, QMainWindow
)
from PySide6.QtGui import Qt, QCursor
import random
from datetime import date


class DashboardWindow(QMainWindow):
    def __init__(self, db, user_id, username):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.username = username
        
        
        #initalising the UI
        self.weight_data = self.get_weight_data()
        self.streak = self.get_streak(self.user_id)
        self.calorie_data = self.get_calorie_data()

        self.setWindowTitle("GymGrind - Dashboard")
        self.setFixedSize(400, 550)
        self.setStyleSheet("background-color: #121212; color: white;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none;")

        content = QWidget()
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        #initialising the buttons for each menu
        self.add_greeting_card()
        self.add_summary_card()
        self.add_big_button("Start New Workout", "#26c6da", self.start_workout)
        self.add_big_button("Past Workouts", "#1976d2", self.show_past_workouts)
        self.add_big_button("Log Nutrition", "#26c6da", self.log_nutrition)
        self.add_big_button("View Advanced Data", "#1976d2", self.open_advanced_data)
        self.add_big_button("Settings", "#26c6da", self.open_settings)

        self.layout.addStretch()
        scroll.setWidget(content)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(scroll)
        self.setCentralWidget(central_widget)

    #list of different greetings for user
    def add_greeting_card(self):
        frame = QFrame()
        frame.setStyleSheet("background-color: #1e1e1e; border-radius: 12px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)

        greetings = [
            "Welcome back", "Good to see you", "Let’s get stronger", "Time to smash it",
            "Ready to crush your goals?", "Let’s make today count", "Push past your limits",
            "You’ve got this!", "Strong mind, strong body", "Let’s build greatness",
            "Every rep counts", "Time to level up", "Feel the burn, love the results",
            "Consistency is power", "Let’s turn sweat into strength", "No excuses, just results",
            "Train like a beast", "Let’s raise the bar", "Your future self will thank you",
            "Time to dominate", "Let’s fuel the fire", "Progress starts now", "Let’s break boundaries",
            "Let’s chase excellence", "You’re unstoppable", "Let’s make gains", "Time to transform",
            "Let’s conquer today", "Stronger every session", "LETS GET PUUUUUUUUUMPED"
        ]
        greeting = random.choice(greetings)

        greeting_label = QLabel(f"{greeting},")
        greeting_label.setStyleSheet("color: white; font-size: 16pt; font-weight: bold;")
        greeting_name = QLabel(self.username)
        greeting_name.setStyleSheet("color: white; font-size: 16pt; font-weight: bold;")

        if self.streak == 1:
            streak_label = QLabel(f"Streak: {self.streak} day")
        else:
            streak_label = QLabel(f"Streak: {self.streak} days")
        streak_label.setStyleSheet("color: #00c853; font-size: 12pt; font-weight: bold;")

        layout.addWidget(greeting_label)
        layout.addWidget(greeting_name)
        layout.addWidget(streak_label)
        self.layout.addWidget(frame)

    #summary card showing most recent weigh-in and calories tracked
    def add_summary_card(self):
        frame = QFrame()
        frame.setStyleSheet("background-color: #1e1e1e; border-radius: 12px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        today = date.today().isoformat()

        title = QLabel("Quick Summary")
        title.setStyleSheet("color: #00bcd4; font-size: 13pt; font-weight: bold;")

        #weight
        weight = self.db.get_latest_weight(self.user_id)
        if weight is not None:
            weight_label = QLabel(f"Current Weight: {weight:.1f} kg")
        else:
            weight_label = QLabel("Current Weight: --")

        # calories
        totals = self.db.get_daily_totals(self.user_id, today)
        calories = totals["calories"]
        if calories is not None:
            cal_label = QLabel(f"Calories Logged: {round(calories)} kcal")
        else:
            cal_label = QLabel("Calories Logged: --")
        

        for lbl in (weight_label, cal_label):
            lbl.setStyleSheet("color: white; font-size: 11pt;")

        layout.addWidget(title)
        layout.addWidget(weight_label)
        layout.addWidget(cal_label)
        self.layout.addWidget(frame)    

    #blueprint to creating a button
    def add_big_button(self, text, color, callback):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: #1e1e1e; border: 2px solid {color}; border-radius: 12px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        btn = QPushButton(text)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                padding: 20px;
                border: none;
                text-align: center;
            }}
            QPushButton:hover {{
                color: {color};
                background-color: #0a0a0a;
            }}
        """)
        btn.clicked.connect(callback)
        layout.addWidget(btn)
        self.layout.addWidget(frame)

    #getting user's weight, calorie and streak data from db
    def get_weight_data(self):
        self.db.cursor.execute("""
            SELECT weight FROM workouts
            WHERE user_id=? AND weight IS NOT NULL
            ORDER BY date ASC
        """, (self.user_id,))
        data = self.db.cursor.fetchall()
        return data
    

    def get_calorie_data(self):
        self.db.cursor.execute("""
        SELECT calories FROM workouts
        WHERE user_id=? AND calories IS NOT NULL
        ORDER BY date ASC
""", (self.user_id,))
        data = self.db.cursor.fetchall()
        return data
    
    def get_streak(self, user_id):
        self.db.cursor.execute(
            "SELECT streak FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = self.db.cursor.fetchone()
        return row["streak"] if row else 0


    #functions mapping to buttons that takes user to each menu
    def start_workout(self):
        from start_workout_manager import StartWorkoutPage
        self.close()
        self.workout_window = StartWorkoutPage(self.db, self.user_id, self.username)
        self.workout_window.show()

    def show_past_workouts(self):
        from view_workouts_manager import ViewWorkoutsPage
        self.close()
        self.view_window = ViewWorkoutsPage(self.db, self.user_id, self.username)
        self.view_window.show()

    def log_nutrition(self):
        from log_nutrition_manager import LogNutritionPage
        self.close()
        self.nutrition_window = LogNutritionPage(self.db, self.user_id, self.username)
        self.nutrition_window.show()

    def open_advanced_data(self):
        from advanced_data_manager import AdvancedDataPage
        self.close()
        self.data_window = AdvancedDataPage(self.db, self.user_id, self.username)
        self.data_window.show()

    def open_settings(self):
        from settings_manager import SettingsPage
        self.close()
        self.settings_window = SettingsPage(self.db, self.user_id, self.username)
        self.settings_window.show()

