from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import pandas as pd
import os

from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.ensemble import RandomForestClassifier


# ==================================================
# FLASK CONFIGURATION
# ==================================================

app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static"
)

app.secret_key = "adaptive_aptitude_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE = os.path.join(BASE_DIR, "aptitude.db")

QUESTIONS_FILE = os.path.join(
    BASE_DIR,
    "datasets",
    "questions.csv"
)

STUDENTS_FILE = os.path.join(
    BASE_DIR,
    "datasets",
    "student_performance.csv"
)


# ==================================================
# DATABASE
# ==================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


def init_database():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            level INTEGER DEFAULT 1,
            question_number INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            wrong_answers INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()

    conn.close()


# ==================================================
# LOAD QUESTIONS
# ==================================================

def load_questions():

    df = pd.read_csv(QUESTIONS_FILE)

    # Remove completely empty rows
    df = df.dropna(how="all")

    return df


# ==================================================
# TRAIN AI MODEL
# ==================================================

def train_ai_model():

    students = pd.read_csv(STUDENTS_FILE)

    features = [
        "QuestionsAttempted",
        "CorrectAnswers",
        "WrongAnswers",
        "Accuracy",
        "AverageResponseTime",
        "EasyCorrect",
        "MediumCorrect",
        "HardCorrect",
        "LongestCorrectStreak",
        "ConfidenceScore",
        "FinalScore"
    ]

    X = students[features]

    y = students["SkillLevel"]

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42
    )

    model.fit(X, y)

    return model


# Train model when application starts
ai_model = train_ai_model()


# ==================================================
# LOGIN CHECK
# ==================================================

def login_required():

    return "user_id" in session


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():

    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# ==================================================
# REGISTER
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()

        password = request.form["password"]

        if not username or not password:

            return render_template(
                "register.html",
                error="Username and password are required."
            )

        hashed_password = generate_password_hash(
            password
        )

        conn = get_db()

        try:

            cursor = conn.execute(
                """
                INSERT INTO users
                (username, password)
                VALUES (?, ?)
                """,
                (
                    username,
                    hashed_password
                )
            )

            user_id = cursor.lastrowid

            conn.execute(
                """
                INSERT INTO progress
                (user_id)
                VALUES (?)
                """,
                (user_id,)
            )

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "register.html",
                error="Username already exists."
            )

        conn.close()

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ==================================================
# LOGIN
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()

        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            return redirect(
                url_for("dashboard")
            )

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template(
        "login.html"
    )


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ==================================================
# DASHBOARD
# ==================================================

@app.route("/dashboard")
def dashboard():

    if not login_required():

        return redirect(
            url_for("login")
        )

    conn = get_db()

    progress = conn.execute(
        """
        SELECT *
        FROM progress
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        progress=progress
    )


# ==================================================
# START / CONTINUE QUIZ
# ==================================================

@app.route("/quiz")
def quiz():

    if not login_required():

        return redirect(
            url_for("login")
        )

    conn = get_db()

    progress = conn.execute(
        """
        SELECT *
        FROM progress
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    conn.close()

    questions = load_questions()

    level = progress["level"]

    # ----------------------------------------------
    # LEVEL → DIFFICULTY
    # ----------------------------------------------

    if level == 1:

        difficulty = "Easy"

    elif level == 2:

        difficulty = "Medium"

    else:

        difficulty = "Hard"

    # ----------------------------------------------
    # SELECT QUESTIONS
    # ----------------------------------------------

    level_questions = questions[
        questions["Difficulty"]
        .astype(str)
        .str.lower()
        == difficulty.lower()
    ]

    if len(level_questions) == 0:

        return (
            "No questions available for "
            + difficulty
            + " level."
        )

    # Select up to 30 questions
    selected_questions = level_questions.sample(
    n=min(30, len(level_questions))
).reset_index(drop=True)

    # Store complete question records
    # together in the session
    session["quiz_questions"] = (
        selected_questions
        .to_dict("records")
    )

    session["quiz_index"] = 0

    session["quiz_score"] = 0

    session["quiz_correct"] = 0

    session["quiz_wrong"] = 0

    # No feedback when quiz starts
    session["show_feedback"] = False

    session.pop("last_feedback", None)

    session.pop("last_explanation", None)

    return redirect(
        url_for("question")
    )


# ==================================================
# DISPLAY CURRENT QUESTION
# ==================================================

@app.route("/question", methods=["GET", "POST"])
def question():

    if not login_required():

        return redirect(
            url_for("login")
        )

    quiz_questions = session.get(
        "quiz_questions",
        []
    )

    index = session.get(
        "quiz_index",
        0
    )

    # No active quiz
    if not quiz_questions:

        return redirect(
            url_for("dashboard")
        )

    # Quiz completed
    if index >= len(quiz_questions):

        return redirect(
            url_for("result")
        )

    # ----------------------------------------------
    # GET THE CURRENT QUESTION
    # ----------------------------------------------

    current_question = quiz_questions[index]

    # ----------------------------------------------
    # STUDENT SUBMITS ANSWER
    # ----------------------------------------------

    if request.method == "POST":

        selected_answer = request.form.get(
            "answer"
        )

        correct_answer = str(
            current_question.get(
                "CorrectAnswer",
                ""
            )
        ).strip()

        # ------------------------------------------
        # CORRECT ANSWER
        # ------------------------------------------

        if selected_answer == correct_answer:

            marks = current_question.get(
                "Marks",
                1
            )

            try:
                marks = int(marks)
            except:
                marks = 1

            session["quiz_score"] = (
                session.get("quiz_score", 0)
                + marks
            )

            session["quiz_correct"] = (
                session.get("quiz_correct", 0)
                + 1
            )

            feedback = "Correct!"

        # ------------------------------------------
        # WRONG ANSWER
        # ------------------------------------------

        else:

            session["quiz_wrong"] = (
                session.get("quiz_wrong", 0)
                + 1
            )

            feedback = "Incorrect."

        # ------------------------------------------
        # IMPORTANT:
        # GET EXPLANATION FROM THE SAME ROW
        # ------------------------------------------

        explanation = str(
            current_question.get(
                "Explanation",
                "No explanation available."
            )
        )

        # Store feedback
        session["last_feedback"] = feedback

        session["last_explanation"] = explanation

        # IMPORTANT:
        # DO NOT INCREMENT quiz_index HERE.
        #
        # This keeps the SAME question on screen
        # while showing its explanation.
        # ------------------------------------------

        session["show_feedback"] = True

        return redirect(
            url_for("question")
        )

    # ----------------------------------------------
    # DISPLAY FEEDBACK
    # ----------------------------------------------

    feedback = None

    explanation = None

    show_feedback = session.get(
        "show_feedback",
        False
    )

    if show_feedback:

        feedback = session.pop(
            "last_feedback",
            None
        )

        explanation = session.pop(
            "last_explanation",
            None
        )

    return render_template(
        "quiz.html",
        question=current_question,
        question_number=index + 1,
        total=len(quiz_questions),
        feedback=feedback,
        explanation=explanation,
        show_feedback=show_feedback
    )


# ==================================================
# NEXT QUESTION
# ==================================================

@app.route("/next-question")
def next_question():

    if not login_required():

        return redirect(
            url_for("login")
        )

    quiz_questions = session.get(
        "quiz_questions",
        []
    )

    index = session.get(
        "quiz_index",
        0
    )

    if not quiz_questions:

        return redirect(
            url_for("dashboard")
        )

    # ----------------------------------------------
    # NOW MOVE TO NEXT QUESTION
    # ----------------------------------------------

    session["quiz_index"] = index + 1

    # Clear previous feedback
    session["show_feedback"] = False

    session.pop(
        "last_feedback",
        None
    )

    session.pop(
        "last_explanation",
        None
    )

    # ----------------------------------------------
    # CHECK WHETHER QUIZ IS COMPLETE
    # ----------------------------------------------

    if session["quiz_index"] >= len(
        quiz_questions
    ):

        return redirect(
            url_for("result")
        )

    return redirect(
        url_for("question")
    )


# ==================================================
# RESULT
# ==================================================

@app.route("/result")
def result():

    if not login_required():

        return redirect(
            url_for("login")
        )

    score = session.get(
        "quiz_score",
        0
    )

    correct = session.get(
        "quiz_correct",
        0
    )

    wrong = session.get(
        "quiz_wrong",
        0
    )

    total = correct + wrong

    accuracy = 0

    if total > 0:

        accuracy = round(
            (correct / total) * 100,
            2
        )

    # ----------------------------------------------
    # AI MODEL INPUT
    # ----------------------------------------------

    questions_attempted = total

    average_response_time = 30

    easy_correct = correct

    medium_correct = 0

    hard_correct = 0

    longest_streak = correct

    confidence_score = accuracy

    final_score = score

    input_data = pd.DataFrame(
        [[
            questions_attempted,
            correct,
            wrong,
            accuracy,
            average_response_time,
            easy_correct,
            medium_correct,
            hard_correct,
            longest_streak,
            confidence_score,
            final_score
        ]],
        columns=[
            "QuestionsAttempted",
            "CorrectAnswers",
            "WrongAnswers",
            "Accuracy",
            "AverageResponseTime",
            "EasyCorrect",
            "MediumCorrect",
            "HardCorrect",
            "LongestCorrectStreak",
            "ConfidenceScore",
            "FinalScore"
        ]
    )

    # ----------------------------------------------
    # PREDICT SKILL LEVEL
    # ----------------------------------------------

    predicted_skill = ai_model.predict(
        input_data
    )[0]

    # ----------------------------------------------
    # UPDATE DATABASE
    # ----------------------------------------------

    conn = get_db()

    progress = conn.execute(
        """
        SELECT *
        FROM progress
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    current_level = progress["level"]

    # ----------------------------------------------
    # LEVEL PROGRESSION
    # ----------------------------------------------

    if accuracy >= 70 and current_level < 3:

        new_level = current_level + 1

    else:

        new_level = current_level

    # ----------------------------------------------
    # SAVE PROGRESS
    # ----------------------------------------------

    conn.execute(
        """
        UPDATE progress

        SET
            level = ?,
            question_number = ?,
            score = score + ?,
            correct_answers = correct_answers + ?,
            wrong_answers = wrong_answers + ?

        WHERE user_id = ?
        """,
        (
            new_level,
            0,
            score,
            correct,
            wrong,
            session["user_id"]
        )
    )

    conn.commit()

    conn.close()

    return render_template(
        "result.html",
        score=score,
        correct=correct,
        wrong=wrong,
        accuracy=accuracy,
        predicted_skill=predicted_skill,
        level=current_level,
        new_level=new_level
    )


# ==================================================
# START FLASK
# ==================================================

if __name__ == "__main__":

    init_database()

    app.run(debug=True)