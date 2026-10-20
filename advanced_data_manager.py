from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QFrame, QMessageBox, QLineEdit, QScrollArea
)
from PySide6.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.dates import DateFormatter
from datetime import datetime
from predictions import PredictionEngine
import pandas as pd


class AdvancedDataPage(QWidget):
    def __init__(self, db, user_id, username):
        super().__init__()
        self.db = db
        self.userId = user_id
        self.userName = username
        self.predictor = PredictionEngine(self.db)

        # window setup
        self.setWindowTitle("GymGrind - Advanced Data")
        self.resize(900, 700)
        self.setStyleSheet("""
            QWidget { background-color: #121212; color: #E8E8E8;  }
            QLabel { color: #E8E8E8; }
            QPushButton {
                background-color: #00bcd4;
                color: #04121A;
                font-weight: bold;
                border-radius: 8px;
                padding: 4px 8px;
            }
            QPushButton:hover { background-color: #019fbf; }
            QFrame.card {
                background: #1e1e1e;
                border-radius: 10px;
                padding: 8px;
            }
            QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #00bcd4;
                color: #E8E8E8;
                border-radius: 6px;
                padding: 3px 6px;
            }
            QComboBox::drop-down { border: none; }
        """)

        # initialise UI
        self.init_ui()
        self.connect_signals()
        self.load_summary()
        self.load_exercise_list()
        self.refresh_chart()

    def init_ui(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.setSpacing(6)

        # header
        headerLayout = QHBoxLayout()
        title = QLabel("Advanced Data & Progress")
        title.setStyleSheet("font-size:14pt; font-weight:700; color:#00bcd4;")
        headerLayout.addWidget(title)
        headerLayout.addStretch()

        self.backButton = QPushButton("Back")
        self.backButton.setCursor(Qt.PointingHandCursor)
        headerLayout.addWidget(self.backButton)
        mainLayout.addLayout(headerLayout)

        # subtitle
        userLabel = QLabel(f"Logged in as {self.userName}")
        userLabel.setStyleSheet("font-size:9pt; color:#999; margin-bottom:4px;")
        mainLayout.addWidget(userLabel)

        # summary
        summaryCard = QFrame()
        summaryCard.setProperty("class", "card")
        summaryLayout = QVBoxLayout(summaryCard)

        self.workoutCountLabel = QLabel("Total Workouts: —")
        self.totalVolumeLabel = QLabel("Total Volume Lifted: —")
        self.avgSetsLabel = QLabel("Average Sets per Exercise: —")
        self.topExerciseLabel = QLabel("Most Trained Exercise: —")

        for lbl in [
            self.workoutCountLabel,
            self.totalVolumeLabel,
            self.avgSetsLabel,
            self.topExerciseLabel,
        ]:
            lbl.setStyleSheet("font-size:10pt; color:#E8E8E8;")
            summaryLayout.addWidget(lbl)

        mainLayout.addWidget(summaryCard)

        # graph selector
        selectorLayout = QHBoxLayout()
        self.graphDropdown = QComboBox()
        self.graphDropdown.addItems([
            "Total Volume Over Time",
            "Weight Over Time",
            #"Calories Over Time",
            "Volume by Muscle Group",
            "Predicted Progress"
        ])
        selectorLayout.addWidget(QLabel("Select Graph:"))
        selectorLayout.addWidget(self.graphDropdown)
        mainLayout.addLayout(selectorLayout)

        # scroll area
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setStyleSheet("QScrollArea { border: none; }")

        scrollContainer = QWidget()
        scrollLayout = QVBoxLayout(scrollContainer)

        # chart
        self.chartCard = QFrame()
        self.chartCard.setProperty("class", "card")
        self.chartLayout = QVBoxLayout(self.chartCard)

        self.chartTitle = QLabel()
        self.chartTitle.setStyleSheet("font-size:12pt; font-weight:600; color:#00bcd4; margin-bottom:2px;")
        self.chartTitle.setAlignment(Qt.AlignCenter)
        self.chartLayout.addWidget(self.chartTitle)

        self.figure = Figure(figsize=(6.5, 6.0), facecolor="#1e1e1e")
        self.canvas = FigureCanvas(self.figure)
        self.axis = self.figure.add_subplot(111)
        self.style_axis(self.axis)
        self.chartLayout.addWidget(self.canvas)

        scrollLayout.addWidget(self.chartCard)
        scrollArea.setWidget(scrollContainer)
        mainLayout.addWidget(scrollArea)

        # prediction controls
        self.predictionLabel = QLabel("Prediction Mode:")
        self.predictionLabel.hide()

        self.modeDropdown = QComboBox()
        self.modeDropdown.addItems(["Predict Weight", "Predict Exercise Volume"])
        self.modeDropdown.currentTextChanged.connect(self.on_mode_change)
        self.modeDropdown.hide()

        controlLayout = QHBoxLayout()
        controlLayout.addWidget(self.predictionLabel)
        controlLayout.addWidget(self.modeDropdown)
        mainLayout.addLayout(controlLayout)

        self.exerciseDropdown = QComboBox()
        self.exerciseDropdown.hide()
        self.exerciseDropdown.setStyleSheet("""
            QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #00bcd4;
                color: #E8E8E8;
                border-radius: 6px;
                padding: 3px 6px;
            }
        """)
        self.exerciseDropdown.currentTextChanged.connect(self.on_exercise_change)
        mainLayout.addWidget(self.exerciseDropdown)

    def connect_signals(self):
        self.backButton.clicked.connect(lambda: self.close())
        self.graphDropdown.currentTextChanged.connect(self.refresh_chart)

    def style_axis(self, ax):
        ax.set_facecolor("#121212")
        for side in ['bottom', 'top', 'right', 'left']:
            ax.spines[side].set_color('white')
        ax.tick_params(colors="white")
        ax.grid(True, color="#333")

    def close(self):
        from dashboard_manager import DashboardWindow
        self.dashboard = DashboardWindow(self.db, self.userId, self.userName)
        self.dashboard.show()
        super().close()

    #getting exercises from db
    def load_exercise_list(self):
        try:
            self.db.cursor.execute("""
                SELECT DISTINCT e.name 
                FROM exercises e
                JOIN workouts w ON e.workout_id = w.id
                WHERE w.user_id = ?
                ORDER BY e.name ASC
            """, (self.userId,))
            exercises = [row[0] for row in self.db.cursor.fetchall()]
            self.exerciseDropdown.clear()
            self.exerciseDropdown.addItems(exercises)
        except Exception as e:
            print("Error loading exercise list:", e)

    #changing graph for different exercises
    def on_exercise_change(self):
        if self.graphDropdown.currentText() == "Predicted Progress" and "Exercise" in self.modeDropdown.currentText():
            self.refresh_chart()


    def refresh_chart(self):
        chartType = self.graphDropdown.currentText()
        self.axis.clear()
        self.style_axis(self.axis)
        self.chartTitle.setText(chartType)

        if "Predicted" in chartType:
            self.predictionLabel.show()
            self.modeDropdown.show()
            if "Exercise" in self.modeDropdown.currentText():
                self.exerciseDropdown.show()
            else:
                self.exerciseDropdown.hide()
        else:
            self.predictionLabel.hide()
            self.modeDropdown.hide()
            self.exerciseDropdown.hide()

        if "Total Volume" in chartType:
            self.plot_total_volume()
        elif "Weight" in chartType and "Predicted" not in chartType:
            self.plot_weight()
        elif "Calories" in chartType:
            self.plot_calories()
        elif "Muscle Group" in chartType:
            self.plot_muscle_groups()
        elif "Predicted" in chartType:
            self.plot_prediction()

        self.figure.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.25)
        self.canvas.draw()

    def on_mode_change(self, mode):
        self.refresh_chart()

    #plotting data
    def plot_total_volume(self):
        self.db.cursor.execute("""
            SELECT w.date, SUM(s.reps * s.weight)
            FROM workouts w
            JOIN exercises e ON e.workout_id = w.id
            JOIN sets s ON s.exercise_id = e.id
            WHERE w.user_id = ?
            GROUP BY w.date
            ORDER BY w.date ASC
        """, (self.userId,))
        data = self.db.cursor.fetchall()

        if not data:
            self.axis.text(0.5, 0.5, "No data available", ha='center', va='center', color='white')
            return

        dates, volumes = zip(*data)
        dates = [datetime.strptime(str(d), "%Y-%m-%d") for d in dates]
        self.axis.plot(dates, volumes, marker='o', color="#00bcd4", linewidth=2)
        self.axis.set_ylabel("Volume (kg)", color="white")
        self.axis.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
        self.figure.autofmt_xdate(rotation=30)

    def plot_weight(self):
        self.db.cursor.execute("""
            SELECT date, current_weight
            FROM user_info_entry
            WHERE user_id = ? AND current_weight IS NOT NULL
            ORDER BY date ASC
        """, (self.userId,))
        data = self.db.cursor.fetchall()

        if not data:
            self.axis.text(0.5, 0.5, "No weight data", ha='center', va='center', color='white')
            return

        dates, weights = zip(*data)
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
        self.axis.plot(dates, weights, marker='o', linewidth=2)
        self.axis.set_ylabel("Weight (kg)")
        self.axis.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
        self.figure.autofmt_xdate(rotation=30)

    def plot_calories(self):
        self.db.cursor.execute("""
            SELECT date, calories
            FROM food_log
            WHERE user_id = ? AND calories IS NOT NULL
            ORDER BY date ASC
        """, (self.userId,))
        data = self.db.cursor.fetchall()

        if not data:
            self.axis.text(0.5, 0.5, "No calorie data", ha='center', va='center', color='white')
            return

        dates, cals = zip(*data)
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
        self.axis.plot(dates, cals, marker='o', linewidth=2)
        self.axis.set_ylabel("Calories (kcal)")
        self.axis.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
        self.figure.autofmt_xdate(rotation=30)

    def plot_muscle_groups(self):
        try:
            self.db.cursor.execute("""
                SELECT 
                    CASE 
                        WHEN e.muscle_group IS NULL OR TRIM(e.muscle_group) = '' THEN 'Unknown'
                        ELSE e.muscle_group 
                    END AS group_name,
                    SUM(s.reps * s.weight)
                FROM exercises e
                JOIN sets s ON s.exercise_id = e.id
                JOIN workouts w ON e.workout_id = w.id
                WHERE w.user_id = ?
                GROUP BY group_name
                ORDER BY SUM(s.reps * s.weight) DESC
            """, (self.userId,))
            rows = self.db.cursor.fetchall()
            if not rows:
                self.axis.text(0.5, 0.5, "No data available", ha='center', va='center', color='white')
                return

            muscles, totals = zip(*rows)
            self.axis.bar(muscles, totals, color="#00bcd4")
            self.axis.set_title("Total Volume by Muscle Group", color='white', fontsize=11)
            self.axis.tick_params(axis='x', rotation=45, colors='white')
            self.axis.tick_params(axis='y', colors='white')

        except Exception as e:
            print("Error plotting muscle groups:", e)

    def plot_prediction(self):
        mode = self.modeDropdown.currentText()
        if "Weight" in mode:
            self.plot_predicted_weight()
        else:
            exercise = self.exerciseDropdown.currentText().strip()
            if not exercise:
                self.axis.text(0.5, 0.5, "Select an exercise to predict", ha='center', va='center', color='white')
                return
            self.plot_predicted_volume(exercise)

    def plot_predicted_weight(self):
        df, nextWeight = self.predictor.predict_next_weight(self.userId)
        if df is None or df.empty:
            self.axis.text(0.5, 0.5, "Not enough data to predict", ha='center', va='center', color='white')
            return

        self.axis.plot(df["date"], df["weight"], 'o-', color="#00bcd4", label="Actual")
        nextDate = df["date"].iloc[-1] + pd.Timedelta(days=7)
        self.axis.plot(
            [df["date"].iloc[-1], nextDate],
            [df["weight"].iloc[-1], nextWeight],
            'r--', linewidth=2, label="Predicted"
        )
        self.axis.legend(facecolor="#ffffff", edgecolor='white')
        self.axis.set_title("Predicted Weight (Next Week)", color="white", fontsize=11)

        self.axis.set_xlim(df["date"].min(), nextDate + pd.Timedelta(days=2))
        self.figure.autofmt_xdate(rotation=30)


        df, nextWeight = self.predictor.predict_next_weight(self.userId)


    def plot_predicted_volume(self, exerciseName):
        df, nextVolume = self.predictor.predict_next_volume(self.userId, exerciseName)
        if df is None or df.empty:
            self.axis.text(0.5, 0.5, f"No data for '{exerciseName}'", ha='center', va='center', color='white')
            return

        df = df.rename(columns={"total_volume": "volume"})
        self.axis.plot(df["date"], df["volume"], 'o-', color="#4caf50", label=exerciseName)
        nextDate = df["date"].iloc[-1] + pd.Timedelta(days=7)
        self.axis.plot(
            [df["date"].iloc[-1], nextDate],
            [df["volume"].iloc[-1], nextVolume],
            'r--', linewidth=2, label="Predicted"
        )
        self.axis.legend(facecolor="#ffffff", edgecolor='white')
        self.axis.set_title(f"Predicted Volume for {exerciseName}", color="white", fontsize=11)
        self.axis.set_xlim(df["date"].min(), nextDate + pd.Timedelta(days=2))
        self.figure.autofmt_xdate(rotation=30)


    def load_summary(self):
        try:
            self.db.cursor.execute("SELECT COUNT(*) FROM workouts WHERE user_id=?", (self.userId,))
            totalWorkouts = self.db.cursor.fetchone()[0] or 0

            self.db.cursor.execute("""
                SELECT SUM(s.reps * s.weight)
                FROM sets s
                JOIN exercises e ON s.exercise_id = e.id
                JOIN workouts w ON e.workout_id = w.id
                WHERE w.user_id = ?
            """, (self.userId,))
            totalVolume = self.db.cursor.fetchone()[0] or 0

            self.db.cursor.execute("""
                SELECT AVG(sets) FROM exercises
                WHERE workout_id IN (SELECT id FROM workouts WHERE user_id=?)
            """, (self.userId,))
            avgSets = self.db.cursor.fetchone()[0] or 0

            self.db.cursor.execute("""
                SELECT e.name, COUNT(*) AS count
                FROM exercises e
                JOIN workouts w ON e.workout_id = w.id
                WHERE w.user_id = ?
                GROUP BY e.name
                ORDER BY count DESC
                LIMIT 1
            """, (self.userId,))
            topExercise = self.db.cursor.fetchone()
            topExercise = topExercise[0] if topExercise else "None"

            self.workoutCountLabel.setText(f"Total Workouts: {totalWorkouts}")
            self.totalVolumeLabel.setText(f"Total Volume: {int(totalVolume)} kg·reps")
            self.avgSetsLabel.setText(f"Average Sets per Exercise: {avgSets:.1f}")
            self.topExerciseLabel.setText(f"Most Trained Exercise: {topExercise}")

        except Exception as e:
            print("Error loading summary:", e)
