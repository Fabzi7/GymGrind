from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QListWidget, QDoubleSpinBox, QFrame, QDateEdit, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, QDate, QTimer
from datetime import datetime

class LogNutritionPage(QWidget):

    def __init__(self, db, user_id, username):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.username = username

        # window setup
        self.setWindowTitle("GymGrind - Log Nutrition")
        self.setFixedSize(620, 840)
        self.setStyleSheet("""
            QWidget { background-color: #121212; color: #E8E8E8; }
            QLabel { color: #E8E8E8; font-weight: bold; }
            QListWidget { background: #161616; border: 1px solid #2f2f2f; border-radius: 6px; }
            QLineEdit, QDoubleSpinBox, QDateEdit, QPushButton {
                background-color: #1e1e1e; color: #E8E8E8; border: 2px solid #00bcd4; border-radius: 6px; padding: 4px;
            }
            QPushButton:hover { background-color: #00bcd4; color: white; }
            QFrame { background-color: #1e1e1e; border-radius: 8px; padding: 8px; }
        """)

        # scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        main_content = QWidget()
        scroll.setWidget(main_content)
        root_layout = QVBoxLayout(main_content)
        root_layout.setContentsMargins(15, 15, 15, 60)
        root_layout.setSpacing(10)

        # header
        header = QHBoxLayout()
        header.addWidget(QLabel(f"Log Nutrition - {username}"))
        header.addStretch()
        self.back_btn = QPushButton("Back")
        header.addWidget(self.back_btn)
        root_layout.addLayout(header)

        # date selector
        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        date_row.addWidget(self.date_edit)
        self.refresh_btn = QPushButton("Show Day")
        date_row.addWidget(self.refresh_btn)
        root_layout.addLayout(date_row)

        # food search
        

        food_card = QFrame()
        food_layout = QVBoxLayout(food_card)
        food_layout.addWidget(QLabel("Select food:"))

        # search input
        self.food_input = QLineEdit()
        self.food_input.setPlaceholderText("Type to search...")
        food_layout.addWidget(self.food_input)

        self.food_suggestions = QListWidget()
        self.food_suggestions.setVisible(False)
        food_layout.addWidget(self.food_suggestions)

        grams_row = QHBoxLayout()
        grams_row.addWidget(QLabel("Amount (g):"))
        self.grams_input = QDoubleSpinBox()
        self.grams_input.setRange(1, 5000)
        self.grams_input.setDecimals(1)
        self.grams_input.setValue(100)
        grams_row.addWidget(self.grams_input)
        self.log_btn = QPushButton("Log Food")
        grams_row.addWidget(self.log_btn)
        food_layout.addLayout(grams_row)

        # manual save button
        self.save_cal_btn = QPushButton("Save Current Calories")
        food_layout.addWidget(self.save_cal_btn)
        root_layout.addWidget(food_card)


        log_card = QFrame()
        log_layout = QVBoxLayout(log_card)
        log_layout.addWidget(QLabel("Entries for the day:"))
        self.day_list = QListWidget()
        log_layout.addWidget(self.day_list)
        root_layout.addWidget(log_card)


        self.totals_label = QLabel("Totals — kcal:0 | Protein:0g | Carbs:0g | Fats:0g")
        root_layout.addWidget(self.totals_label)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

        
        self.back_btn.clicked.connect(self.go_back)
        self.refresh_btn.clicked.connect(self.refresh_day_view)
        self.save_cal_btn.clicked.connect(self.save_current_calories)

        self.food_input.textChanged.connect(self.update_suggestions)
        self.food_suggestions.itemClicked.connect(self.select_suggestion)
        self.log_btn.clicked.connect(self.log_food)

        # autosave at end of day
        self.timer = QTimer()
        self.timer.timeout.connect(self.autosave_if_needed)
        self.timer.start(60000)  # every 60s

        self.refresh_day_view()

    def update_suggestions(self, text):
        self.food_suggestions.clear()

        if not text.strip():
            self.food_suggestions.setVisible(False)
            return

        results = self.db.search_foods_by_name(text)

        for food in results:
            self.food_suggestions.addItem(food["name"])

        self.food_suggestions.setVisible(bool(results))


    def select_suggestion(self, item):
        self.food_input.setText(item.text())
        self.food_suggestions.setVisible(False)

    # food logging
    def log_food(self):
        food_name = self.food_input.text().strip()
        if not food_name:
            QMessageBox.warning(self, "Error", "Please select a food.")
            return

        food = self.db.get_food_by_name(food_name)
        if not food:
            QMessageBox.warning(self, "Error", "Please select a valid food from the list.")
            return

        grams = self.grams_input.value()
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")

        calories = food["calories"] * grams / 100
        protein  = food["protein"]  * grams / 100
        carbs    = food["carbs"]    * grams / 100
        fats     = food["fats"]     * grams / 100

        try:
            self.db.upsert_food_log(
                self.user_id,
                selected_date,
                food["name"],
                calories,
                protein,
                carbs,
                fats
            )
            self.refresh_day_view()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not log food: {e}")



    def go_back(self):
        from dashboard_manager import DashboardWindow
        self.close()
        self.dashboard = DashboardWindow(self.db, self.user_id, self.username)
        self.dashboard.show()

    def refresh_day_view(self):
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")
        self.day_list.clear()

        rows = self.db.get_food_log_for_day(self.user_id, selected_date)

        for r in rows:
            name, cal, pro, carb, fat = r
            self.day_list.addItem(
                f"{name} — {round(cal)} kcal | Protein:{round(pro)} Carbs:{round(carb)} Fats:{round(fat)}"
            )

        totals = self.db.get_daily_totals(self.user_id, selected_date)

        self.totals_label.setText(
            f"Totals — kcal:{round(totals['calories'])} | "
            f"Protein:{round(totals['protein'])}g | "
            f"Carbs:{round(totals['carbs'])}g | "
            f"Fats:{round(totals['fats'])}g"
        )

    def parse_macro(self, text):
        return float(text.split(":")[1].replace("g", "").strip())

    #saves calories to db
    def save_current_calories(self):
        food_name = self.food_input.text().strip()
        food = self.db.get_food_by_name(food_name)

        if not food:
            QMessageBox.warning(self, "Error", "Please select a valid food from the list.")
            return

        selected_date = self.date_edit.date().toString("yyyy-MM-dd")
        try:
            parts = self.totals_label.text().split("|")
            cal   = float(parts[0].split(":")[1])
            pro   = self.parse_macro(parts[1])
            carbs = self.parse_macro(parts[2])
            fats  = self.parse_macro(parts[3])

            self.db.upsert_food_log(
                self.user_id,
                selected_date,
                food["name"],
                cal,
                pro,
                carbs,
                fats
            )
            QMessageBox.information(self, "Food log", "Successfully logged food.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save totals: {e}")

    #autosaves calories right before midnight
    def autosave_if_needed(self):
        now = datetime.now()
        if now.hour == 23 and now.minute == 59:
            self.save_current_calories()
