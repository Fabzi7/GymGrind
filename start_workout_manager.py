from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QFrame, QScrollArea, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QIntValidator, QDoubleValidator


class StartWorkoutPage(QWidget):
    def __init__(self, db, userId, username):
        super().__init__()
        self.db = db
        self.userId = userId
        self.username = username
        self.currentWorkoutId = None
        self.exerciseCards = {}

        self.setWindowTitle("GymGrind - Start Workout")
        self.setFixedSize(400, 550)
        self.setStyleSheet("""
            QWidget { background-color: #121212; color: #E8E8E8; font-family: 'Bebas Neue';}
            QLabel { color: #E8E8E8; }
            QLineEdit {
                background: #1e1e1e; color: #E8E8E8; border: 1px solid #2f2f2f;
                padding: 6px; border-radius: 6px;
            }
            QListWidget { background: #161616; border: 1px solid #2f2f2f; border-radius: 6px; }
            QPushButton {
                background-color: #00bcd4; color: #04121A; font-weight: bold; border-radius: 8px; padding: 6px 8px;
            }
            QPushButton:hover { background-color: #00bcd4; }
        """) 

        self.buildUi()
        self.wireEvents()

    # creating the ui
    def buildUi(self):
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(12, 12, 12, 12)
        rootLayout.setSpacing(8)

        headerLayout = QHBoxLayout()
        titleLabel = QLabel("Start a Workout")
        titleLabel.setStyleSheet("font-size:15pt; font-weight:700; color:#00bcd4;")
        headerLayout.addWidget(titleLabel)
        headerLayout.addStretch()

        self.finishButton = QPushButton("Finish")
        self.finishButton.setEnabled(False)
        headerLayout.addWidget(self.finishButton)

        self.backButton = QPushButton("Back")
        headerLayout.addWidget(self.backButton)
        rootLayout.addLayout(headerLayout)

        nameRow = QHBoxLayout()
        self.workoutNameInput = QLineEdit()
        self.workoutNameInput.setPlaceholderText("Workout name (e.g. Push Day)")
        nameRow.addWidget(self.workoutNameInput)

        self.startButton = QPushButton("Start Workout")
        nameRow.addWidget(self.startButton)
        rootLayout.addLayout(nameRow)

        # shown before a workout has started
        self.emptyState = QTextEdit()
        self.emptyState.setReadOnly(True)
        self.emptyState.setTextInteractionFlags(Qt.NoTextInteraction)
        self.emptyState.setStyleSheet("""
            QTextEdit {
                background-color: #141414;
                border: 1px dashed #2f2f2f;
                border-radius: 10px;
                color: #9e9e9e;
                padding: 12px;
                font-size: 10.5pt;
            }
        """)
        self.emptyState.setText(
            "Welcome, athlete!\n\n"
            "Start your next workout by naming it above and pressing "
            "'Start Workout'. Once you begin, you’ll be able to:\n\n"
            "• Search for common exercises\n"
            "• Add your own custom exercises\n"
            "• Log sets and weights to track progress"
        )
        rootLayout.addWidget(self.emptyState)

        # main workout ui
        self.searchArea = QFrame()
        searchLayout = QVBoxLayout(self.searchArea)
        searchLayout.setSpacing(8)

        self.searchInput = QLineEdit()
        self.searchInput.setPlaceholderText("Search exercises (type to search)...")
        searchLayout.addWidget(self.searchInput)

        self.resultsList = QListWidget()
        self.resultsList.setFixedHeight(120)
        searchLayout.addWidget(self.resultsList)

        addRow = QHBoxLayout()
        self.addSelectedButton = QPushButton("Add Selected")
        self.addSelectedButton.setEnabled(False)
        addRow.addWidget(self.addSelectedButton)

        self.customExerciseInput = QLineEdit()
        self.customExerciseInput.setPlaceholderText("Custom exercise name")
        addRow.addWidget(self.customExerciseInput)

        self.addCustomButton = QPushButton("Add Custom")
        addRow.addWidget(self.addCustomButton)
        searchLayout.addLayout(addRow)

        self.cardScroll = QScrollArea()
        self.cardScroll.setWidgetResizable(True)
        containerWidget = QWidget()
        self.cardsLayout = QVBoxLayout(containerWidget)
        self.cardsLayout.setContentsMargins(0, 0, 0, 0)
        self.cardsLayout.setSpacing(8)
        self.cardScroll.setWidget(containerWidget)
        self.cardScroll.setFixedHeight(280)
        searchLayout.addWidget(self.cardScroll)

        self.searchArea.hide()
        rootLayout.addWidget(self.searchArea)

    #connecting buttons to function
    def wireEvents(self):
        self.startButton.clicked.connect(self.onStart)
        self.backButton.clicked.connect(self.onBack)
        self.finishButton.clicked.connect(self.onFinish)
        self.searchInput.textChanged.connect(self.onSearchText)
        self.resultsList.itemSelectionChanged.connect(self.onResultSelected)
        self.addSelectedButton.clicked.connect(self.onAddSelected)
        self.addCustomButton.clicked.connect(self.onAddCustom)

    def onStart(self):
        name = self.workoutNameInput.text().strip()
        if not name:
            QMessageBox.warning(self, "Name required", "Enter a workout name to start.")
            return

        self.currentWorkoutId = self.db.add_workout(self.userId, name, None)
        self.workoutNameInput.setDisabled(True)
        self.startButton.setDisabled(True)
        self.finishButton.setEnabled(True)
        self.emptyState.hide()
        self.searchArea.show()
        self.populateResults()

    #returning back to dashboard
    def onBack(self):
        try:
            from dashboard_manager import DashboardWindow
            self.hide()
            self.dashboard = DashboardWindow(self.db, self.userId, self.username)
            self.dashboard.show()
        except Exception as error:
            print("Error returning to dashboard:", error)
            QMessageBox.warning(self, "Error", "Could not return to dashboard.")

    def onFinish(self):
        try:
            self.db.update_workout_streak(self.userId)

            QMessageBox.information(
                self,
                "Saved",
                "Workout saved."
            )
            self.onBack()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Workout saved, but streak could not be updated:\n{e}"
            )
            self.onBack()


    #allows user to search through the workouts
    def onSearchText(self):
        query = self.searchInput.text().strip()
        try:
            results = self.db.search_default_workouts(query)
        except Exception:
            likeQuery = f"%{query}%"
            self.db.cursor.execute("SELECT name FROM default_workouts WHERE name LIKE ?", (likeQuery,))
            results = [row[0] for row in self.db.cursor.fetchall()]

        sortedResults = self.mergeSort(results)
        self.resultsList.clear()

        if not sortedResults:
            self.resultsList.addItem(QListWidgetItem("No matches — use 'Add Custom'"))
            return

        for name in sortedResults:
            self.resultsList.addItem(QListWidgetItem(name))

    #getting default workouts from the file
    def populateResults(self, query=""):
        try:
            if query:
                results = self.db.search_default_workouts(query)
            else:
                results = self.db.get_default_workouts()
        except Exception:
            if query:
                likeQuery = f"%{query}%"
                self.db.cursor.execute("SELECT name FROM default_workouts WHERE name LIKE ?", (likeQuery,))
            else:
                self.db.cursor.execute("SELECT name FROM default_workouts")
            results = [row[0] for row in self.db.cursor.fetchall()]

        sortedResults = self.mergeSort(results)
        self.resultsList.clear()
        for name in sortedResults:
            self.resultsList.addItem(QListWidgetItem(name))

    def onResultSelected(self):
        self.addSelectedButton.setEnabled(bool(self.resultsList.selectedItems()))

    def onAddSelected(self):
        if not self.currentWorkoutId:
            return

        item = self.resultsList.currentItem()
        if not item:
            return

        name = item.text()
        key = name.lower()
        if key in self.exerciseCards or name.startswith("No matches"):
            return

        exerciseId = self.db.add_exercise(self.currentWorkoutId, name)
        self.createExerciseCard(exerciseId, name)

    def onAddCustom(self):
        if not self.currentWorkoutId:
            return

        name = self.customExerciseInput.text().strip()
        if not name:
            return

        key = name.lower()
        if key in self.exerciseCards:
            QMessageBox.warning(self, "Duplicate", f"{name} already added.")
            return

        exerciseId = self.db.add_exercise(self.currentWorkoutId, name)
        self.customExerciseInput.clear()
        self.createExerciseCard(exerciseId, name)

    def createExerciseCard(self, exerciseId, name):
        card = QFrame()
        card.setStyleSheet(
            "background-color: #1c1c1c; border: 1px solid #2f2f2f; border-radius: 10px;"
        )
        card.setFixedWidth(360)

        cardLayout = QVBoxLayout(card)
        cardLayout.setContentsMargins(10, 8, 10, 10)
        cardLayout.setSpacing(8)

        title = QLabel(name)
        title.setStyleSheet("font-weight: 600; color: #00bcd4; font-size: 12pt;")
        cardLayout.addWidget(title)

        inputRow = QHBoxLayout()
        repsInput = QLineEdit()
        repsInput.setPlaceholderText("Reps")
        repsInput.setValidator(QIntValidator(1, 100))
        repsInput.setFixedWidth(70)

        weightInput = QLineEdit()
        weightInput.setPlaceholderText("Weight (kg)")
        weightInput.setValidator(QDoubleValidator(0.0, 999.9, 1))
        weightInput.setFixedWidth(100)

        saveButton = QPushButton("Save Set")
        saveButton.setCursor(QCursor(Qt.PointingHandCursor))

        inputRow.addWidget(repsInput)
        inputRow.addWidget(weightInput)
        inputRow.addWidget(saveButton)
        cardLayout.addLayout(inputRow)

        savedSetsList = QListWidget()
        savedSetsList.setFixedHeight(100)
        cardLayout.addWidget(savedSetsList)

        #saving sets to db
        def saveSet():
            if not repsInput.text() or not weightInput.text():
                return

            reps = int(repsInput.text())
            weight = float(weightInput.text())
            self.db.add_set(exerciseId, reps, weight)
            self.db.update_total_volume(exerciseId)
            savedSetsList.addItem(f"{reps} reps × {weight} kg")
            repsInput.clear()
            weightInput.clear()

        saveButton.clicked.connect(saveSet)

        self.cardsLayout.addWidget(card)
        self.exerciseCards[name.lower()] = card
        self.cardScroll.ensureWidgetVisible(card)

    #sorting algorithm
    def mergeSort(self, items):
        if len(items) <= 1:
            return items[:]

        mid = len(items) // 2
        left = self.mergeSort(items[:mid])
        right = self.mergeSort(items[mid:])
        return self.merge(left, right)
    
    def merge(self, left, right):
        i = j = 0
        merged = []

        while i < len(left) and j < len(right):
            if left[i].lower() <= right[j].lower():
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1

        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged
