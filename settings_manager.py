from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QScrollArea, QMessageBox
)
from PySide6.QtGui import Qt, QCursor
from datetime import date

class SettingsPage(QMainWindow):
    def __init__(self, db, user_id, username):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.username = username

        # window setup
        self.setWindowTitle("GymGrind - Settings & Personal Info")
        self.setFixedSize(400, 550)
        self.setStyleSheet("background-color: #121212; color: white;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none;")

        content = QWidget()
        self.root = QVBoxLayout(content)
        self.root.setContentsMargins(20, 20, 20, 20)
        self.root.setSpacing(15)

        # header with back button
        header = QHBoxLayout()
        header.addStretch()
        self.back_btn = QPushButton("← Back")
        self.back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid #00bcd4;
                border-radius: 6px;
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00bcd4;
                color: black;
            }
        """)
        self.back_btn.clicked.connect(self.go_back)
        header.addWidget(self.back_btn)
        self.root.addLayout(header)

        # title card
        title_frame = QFrame()
        title_frame.setStyleSheet("background-color: #1e1e1e; border-radius: 12px;")
        title_layout = QVBoxLayout(title_frame)
        title_label = QLabel("Profile & Settings")
        title_label.setStyleSheet("color: #00bcd4; font-size: 16pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title_label)
        self.root.addWidget(title_frame)

        # username input 
        self.username_input = self.create_input_card("Username", "Enter new username")
        self.root.addWidget(self.username_input["frame"])

        # target weight input 
        self.target_input = self.create_input_card("Target Weight (kg)", "Enter target weight")
        self.root.addWidget(self.target_input["frame"])

        # current weight input 
        self.current_input = self.create_input_card("Current Weight (kg)", "Enter current weight")
        self.root.addWidget(self.current_input["frame"])

        # save changes button
        save_frame = QFrame()
        save_frame.setStyleSheet("background-color: #1e1e1e; border-radius: 12px;")
        save_layout = QVBoxLayout(save_frame)
        self.save_button = QPushButton("Save Changes")
        self.save_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #00bcd4;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13pt;
                font-weight: bold;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #0097a7;
            }
        """)
        self.save_button.clicked.connect(self.save_changes)
        save_layout.addWidget(self.save_button)
        self.root.addWidget(save_frame)

        self.root.addStretch()
        scroll.setWidget(content)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(scroll)
        self.setCentralWidget(central_widget)

        # load profile data
        self.load_profile_data()

    # create input helper
    def create_input_card(self, label_text, placeholder):
        frame = QFrame()
        frame.setStyleSheet("background-color: #1e1e1e; border-radius: 12px;")
        layout = QVBoxLayout(frame)
        label = QLabel(label_text)
        label.setStyleSheet("color: #00bcd4; font-size: 11pt; font-weight: bold;")
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border: 1px solid #00bcd4;
            }
        """)
        layout.addWidget(label)
        layout.addWidget(input_field)
        return {"frame": frame, "input": input_field}

    # load existing user info
    def load_profile_data(self):
        query = "SELECT username, target_weight, current_weight FROM users LEFT JOIN user_info_entry USING(user_id) WHERE user_id=? ORDER BY date DESC LIMIT 1"
        row = self.db.cursor.execute(query, (self.user_id,)).fetchone()
        if row:
            username, target_weight, current_weight = row
            self.username_input["input"].setText(username or "")
            self.target_input["input"].setText(str(target_weight) if target_weight else "")
            self.current_input["input"].setText(str(current_weight) if current_weight else "")

    # save changes to db
    def save_changes(self):
        new_username = self.username_input["input"].text().strip()
        new_target = self.target_input["input"].text().strip()
        new_current = self.current_input["input"].text().strip()

        if not new_username:
            QMessageBox.warning(self, "input error", "username cannot be empty")
            return

        try:
            self.db.cursor.execute("""
                UPDATE users
                SET username=?, target_weight=?
                WHERE user_id=?
            """, (new_username, new_target or None, self.user_id))

            entry_date = date.today().isoformat() 

            if new_current:
                self.db.cursor.execute("""
                    INSERT INTO user_info_entry (user_id, date, current_weight, calories_consumed)
                    VALUES (?, ?, ?, COALESCE((SELECT calories_consumed FROM user_info_entry WHERE user_id=? AND date=?), 0))
                    ON CONFLICT(user_id, date)
                    DO UPDATE SET
                        current_weight=excluded.current_weight,
                        calories_consumed=COALESCE(excluded.calories_consumed, calories_consumed)
                """, (self.user_id, entry_date, float(new_current), self.user_id, entry_date))


            self.db.conn.commit()
            QMessageBox.information(self, "success", "profile updated successfully")
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                QMessageBox.warning(self, "username error", "that username is already taken")
            else:
                QMessageBox.critical(self, "database error", str(e))


    def go_back(self):
        from dashboard_manager import DashboardWindow
        updated_username = self.username_input["input"].text().strip()

        self.close()
        self.dashboard = DashboardWindow(self.db, self.user_id, updated_username)
        self.dashboard.show()
