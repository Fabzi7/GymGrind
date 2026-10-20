from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QFrame, QScrollArea, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve


class ViewWorkoutsPage(QWidget):
    def __init__(self, db, user_id, username):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.username = username

        self.setWindowTitle("GymGrind - Past Workouts")
        self.setFixedSize(420, 580)
        self.setStyleSheet("""
            QWidget { background-color: #121212; color: #E8E8E8; }
            QLabel { color: #E8E8E8; }
            QListWidget {
                background: #161616;
                border: 1px solid #2f2f2f;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #00bcd4; color: #04121A; font-weight: bold;
                border-radius: 8px; padding: 6px 10px;
            }
            QPushButton:hover { background-color: #019fbf; }
            QFrame.card {
                background: #1e1e1e;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        # Initialising
        self.build_ui()
        self.populate_workouts()
        self.wire_events()

    
    def build_ui(self):
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(14, 14, 14, 14)
        self.root.setSpacing(10)

        # Header
        header = QHBoxLayout()
        title = QLabel("Past Workouts")
        title.setStyleSheet("font-size:16pt; font-weight:700; color:#00bcd4;")
        header.addWidget(title)
        header.addStretch()

        self.back_btn = QPushButton("Back")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.back_btn)
        self.root.addLayout(header)

        # Subtitle
        self.subtitle = QLabel(f"Logged in as {self.username}")
        self.subtitle.setStyleSheet("font-size:10pt; color:#999; margin-bottom:6px;")
        self.root.addWidget(self.subtitle)

        # Workout list
        self.workout_list = QListWidget()
        self.workout_list.setSelectionMode(QListWidget.SingleSelection)
        self.root.addWidget(self.workout_list)

        # Workout counter label
        self.counter_label = QLabel("")
        self.counter_label.setStyleSheet("font-size:9pt; color:#888; margin-top:4px;")
        self.root.addWidget(self.counter_label)

        # Buttons
        self.view_details_btn = QPushButton("View Details")
        self.view_details_btn.setEnabled(False)
        self.root.addWidget(self.view_details_btn)

        self.root.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Details frame 
        self.detail_frame = QFrame()
        self.detail_layout = QVBoxLayout(self.detail_frame)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_frame.hide()
        self.root.addWidget(self.detail_frame)

        # Scroll area for exercises
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_container = QWidget()
        self.detail_vbox = QVBoxLayout(self.detail_container)
        self.detail_vbox.setContentsMargins(6, 6, 6, 6)
        self.detail_vbox.setSpacing(8)
        self.detail_scroll.setWidget(self.detail_container)
        self.detail_layout.addWidget(self.detail_scroll)

        self.back_to_list_btn = QPushButton("Back to List")
        self.detail_layout.addWidget(self.back_to_list_btn)


    def wire_events(self):
        self.workout_list.itemSelectionChanged.connect(self.on_select_workout)
        self.view_details_btn.clicked.connect(self.on_view_details)
        self.back_to_list_btn.clicked.connect(self.on_back_to_list)
        self.back_btn.clicked.connect(self.on_back_dashboard)

    def populate_workouts(self):
        self.workout_list.clear()
        try:
            self.db.cursor.execute(
                "SELECT id, name, date FROM workouts WHERE user_id = ? ORDER BY date DESC",
                (self.user_id,)
            )
            workouts = self.db.cursor.fetchall()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load workouts:\n{e}")
            print("DB ERROR (load workouts):", e)
            return

        if not workouts:
            self.workout_list.addItem("No past workouts found.")
            self.workout_list.setEnabled(False)
            self.counter_label.setText("No workouts logged yet.")
            return

        self.workout_list.setEnabled(True)
        for w_id, name, date in workouts:
            item = QListWidgetItem(f"{name}  ({date})")
            item.setData(Qt.UserRole, w_id)
            self.workout_list.addItem(item)

        self.counter_label.setText(f"Total workouts: {len(workouts)}")

    def on_select_workout(self):
        has_selection = bool(self.workout_list.selectedItems())
        self.view_details_btn.setEnabled(has_selection)

    # details of workout
    def clear_detail_vbox(self):
        while self.detail_vbox.count():
            item = self.detail_vbox.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def on_view_details(self):
        selected = self.workout_list.currentItem()
        if not selected:
            return

        workout_id = selected.data(Qt.UserRole)
        workout_name = selected.text().split("  (")[0]

        # Hide list and button
        self.view_details_btn.hide()
        self.animate_transition(self.workout_list, self.detail_frame)

        self.clear_detail_vbox()

        # Title
        title_label = QLabel(f"{workout_name}")
        title_label.setStyleSheet("font-size:13pt; font-weight:600; color:#00bcd4;")
        self.detail_vbox.addWidget(title_label)

        # get exercises
        try:
            self.db.cursor.execute(
                "SELECT id, name FROM exercises WHERE workout_id = ?", (workout_id,)
            )
            exercises = self.db.cursor.fetchall()
        except Exception as e:
            print("DB ERROR (load exercises):", e)
            QMessageBox.warning(self, "Error", f"Could not load exercises:\n{e}")
            return

        if not exercises:
            no_ex = QLabel("No exercises logged for this workout.")
            no_ex.setStyleSheet("color:#aaa;")
            self.detail_vbox.addWidget(no_ex)
            return
        
        #creating frame for each exercise added
        for ex_id, ex_name in exercises:
            ex_card = QFrame()
            ex_card.setProperty("class", "card")
            ex_layout = QVBoxLayout(ex_card)
            ex_layout.setContentsMargins(6, 6, 6, 6)
            ex_layout.setSpacing(4)

            ex_label = QLabel(ex_name)
            ex_label.setStyleSheet("font-weight:600; font-size:11pt; color:#00bcd4;")
            ex_layout.addWidget(ex_label)

            try:
                self.db.cursor.execute(
                    "SELECT reps, weight FROM sets WHERE exercise_id = ?", (ex_id,)
                )
                sets = self.db.cursor.fetchall()
            except Exception as e:
                print("DB ERROR (load sets):", e)
                sets = []
                ex_layout.addWidget(QLabel("  (error loading sets)"))

            if sets:
                for r, w in sets:
                    set_label = QLabel(f"  • {r} reps × {w} kg")
                    ex_layout.addWidget(set_label)
            else:
                ex_layout.addWidget(QLabel("  (no sets logged)"))

            self.detail_vbox.addWidget(ex_card)

    def animate_transition(self, hide_widget, show_widget):
        hide_widget.hide()
        show_widget.show()

        anim = QPropertyAnimation(show_widget, b"windowOpacity")
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.start()
        self.anim = anim 

    def on_back_to_list(self):
        self.animate_transition(self.detail_frame, self.workout_list)
        self.detail_frame.hide()
        self.view_details_btn.show()

    def on_back_dashboard(self):
        from dashboard_manager import DashboardWindow  
        self.close()
        self.dashboard = DashboardWindow(self.db, self.user_id, self.username)
        self.dashboard.show()
