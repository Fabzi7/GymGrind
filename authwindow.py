from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QCheckBox, QStackedLayout, QMessageBox
)
from PySide6.QtGui import QPixmap, Qt, QFont, QCursor
import sys

from dashboard_manager import DashboardWindow
from database_manager import DatabaseManager


class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GymGrind")
        self.setFixedSize(400, 550)
        self.setStyleSheet("background-color: #1e1e1e;")

        self.db = DatabaseManager()

        self.stacked_layout = QStackedLayout(self)
        self.setLayout(self.stacked_layout)

        self.login_page = self.create_login_page()
        self.signup_page = self.create_signup_page()

        self.stacked_layout.addWidget(self.login_page)
        self.stacked_layout.addWidget(self.signup_page)

        self.stacked_layout.setCurrentWidget(self.login_page)

    def create_logo_title(self):
        logo_label = QLabel()
        pixmap = QPixmap("Logo.png")
        if not pixmap.isNull():
            scaled = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled)
        else:
            logo_label.setText("[Logo]")
        logo_label.setAlignment(Qt.AlignCenter)

        title = QLabel("GymGrind")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; font-size: 22pt; font-weight: bold;")

        vbox = QVBoxLayout()
        vbox.addWidget(logo_label)
        vbox.addWidget(title)
        return vbox

    def create_input(self, placeholder, password=False):
        box = QLineEdit()
        box.setPlaceholderText(placeholder)
        if password:
            box.setEchoMode(QLineEdit.Password)
        box.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 6px;
                background: #2c2c2c;
                color: white;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #00c853;
                background: #333;
            }
        """)
        return box

    def create_button(self, text, primary=False):
        btn = QPushButton(text)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        if primary:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #00c853;
                    color: white;
                    font-size: 11pt;
                    padding: 10px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #00e676;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #333;
                    color: white;
                    font-size: 11pt;
                    padding: 10px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #444;
                }
            """)
        return btn

    def create_login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)

        layout.addLayout(self.create_logo_title())

        self.username_input = self.create_input("Email or Username")
        self.password_input = self.create_input("Password", password=True)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)

        login_button = self.create_button("Log in", primary=True)
        login_button.clicked.connect(self.handle_login) 
        layout.addWidget(login_button)

        signup_prompt = QLabel("Don't have an account? <a href='#'>Sign up</a>")
        signup_prompt.setStyleSheet("color: white; font-size: 10pt;")
        signup_prompt.setAlignment(Qt.AlignCenter)
        signup_prompt.setOpenExternalLinks(False)
        signup_prompt.linkActivated.connect(lambda: self.stacked_layout.setCurrentWidget(self.signup_page))
        layout.addWidget(signup_prompt)

        layout.addStretch()
        return page

    def create_signup_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)

        layout.addLayout(self.create_logo_title())

        self.new_username = self.create_input("Email or Username")
        self.new_password = self.create_input("Password", password=True)
        self.confirm_password = self.create_input("Confirm Password", password=True)

        layout.addWidget(self.new_username)
        layout.addWidget(self.new_password)
        layout.addWidget(self.confirm_password)

        create_button = self.create_button("Create Account", primary=True)
        create_button.clicked.connect(self.handle_signup) 
        layout.addWidget(create_button)

        back_prompt = QLabel("Already have an account? <a href='#'>Log in</a>")
        back_prompt.setStyleSheet("color: white; font-size: 10pt;")
        back_prompt.setAlignment(Qt.AlignCenter)
        back_prompt.setOpenExternalLinks(False)
        back_prompt.linkActivated.connect(lambda: self.stacked_layout.setCurrentWidget(self.login_page))
        layout.addWidget(back_prompt)

        layout.addStretch()
        return page

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if self.db.validate_user(username, password):
            user_id = self.db.get_user_id(username)

            if user_id is not None:
                self.dashboard = DashboardWindow(self.db, user_id, username)
                self.dashboard.show()

                self.close()
            else:
                QMessageBox.warning(self, "Error", "Could not find user ID.")
        else:
            QMessageBox.warning(self, "Error", "Invalid username or password")


    def handle_signup(self):
        username = self.new_username.text()
        password = self.new_password.text()
        confirm = self.confirm_password.text()

        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        if self.db.add_user(username, password):
            QMessageBox.information(self, "Success", "Account created! You can log in now.")
            self.stacked_layout.setCurrentWidget(self.login_page)
        else:
            QMessageBox.warning(self, "Error", "Username already exists")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AuthWindow()
    window.show()
    sys.exit(app.exec())
