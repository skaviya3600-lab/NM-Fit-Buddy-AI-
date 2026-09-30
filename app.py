from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import hashlib
import hmac
import secrets
import sqlite3
import json
from pathlib import Path
from functools import wraps
from datetime import date

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"
DATA_PATH = BASE_DIR / "data" / "fitness_data.json"

app = Flask(__name__)
app.secret_key = "fitbuddy-ai-nm-project-secret-key-change-in-production"


def generate_password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
    return f"pbkdf2:sha256:120000${salt}${digest}"


def check_password_hash(stored, password):
    try:
        method, salt, digest = stored.split("$", 2)
        _, algorithm, rounds = method.split(":")
        candidate = hashlib.pbkdf2_hmac(algorithm, password.encode("utf-8"), salt.encode("utf-8"), int(rounds)).hex()
        return hmac.compare_digest(candidate, digest)
    except (ValueError, TypeError):
        return False


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def load_fitness_data():
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            height REAL NOT NULL,
            weight REAL NOT NULL,
            goal TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            entry_date TEXT NOT NULL,
            weight REAL NOT NULL,
            notes TEXT DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


def get_current_user():
    if "user_id" not in session:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return user


def calculate_bmi(height_cm, weight_kg):
    height_m = height_cm / 100
    if height_m <= 0:
        return 0
    return round(weight_kg / (height_m ** 2), 2)


def bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obesity"


def calculate_calories(age, gender, height, weight, activity=1.375):
    # Mifflin-St Jeor equation (basic estimate).
    if gender.lower() == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    return round(bmr * activity)


def get_water_liters(weight):
    return round(weight * 0.033, 1)


def get_recommendations(user):
    data = load_fitness_data()
    bmi = calculate_bmi(user["height"], user["weight"])
    goal = user["goal"].lower()

    if goal == "weight loss":
        goal_tips = [
            "Choose a moderate calorie deficit and avoid crash diets.",
            "Aim for regular walking/cardio plus strength training.",
            "Include vegetables, fruits, whole grains and protein-rich foods."
        ]
    elif goal == "muscle gain":
        goal_tips = [
            "Include progressive strength training 3–4 days per week.",
            "Eat enough protein and overall calories to support training.",
            "Prioritize sleep and recovery between workouts."
        ]
    else:
        goal_tips = [
            "Maintain a balanced diet and regular physical activity.",
            "Combine cardio, strength and flexibility exercises.",
            "Track habits consistently rather than focusing only on weight."
        ]

    if bmi < 18.5:
        bmi_tip = "Your BMI is in the underweight range. Focus on nutritious, energy-dense meals and consider professional guidance."
    elif bmi < 25:
        bmi_tip = "Your BMI is in the normal range. Continue balanced nutrition and regular activity."
    elif bmi < 30:
        bmi_tip = "Your BMI is in the overweight range. Gradual activity and balanced eating can support healthy progress."
    else:
        bmi_tip = "Your BMI is in the obesity range. Gradual lifestyle changes and professional guidance may be helpful."

    return {
        "bmi": bmi,
        "bmi_category": bmi_category(bmi),
        "calories": calculate_calories(user["age"], user["gender"], user["height"], user["weight"]),
        "water": get_water_liters(user["weight"]),
        "goal_tips": goal_tips,
        "bmi_tip": bmi_tip,
        "workouts": data["workouts"].get(user["goal"], data["workouts"]["General Fitness"]),
        "foods": data["foods"].get(user["goal"], data["foods"]["General Fitness"]),
    }


@app.route("/")
def index():
    return render_template("index.html", user=get_current_user())


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        age = int(request.form["age"])
        gender = request.form["gender"]
        height = float(request.form["height"])
        weight = float(request.form["weight"])
        goal = request.form["goal"]

        if not name or not email or len(password) < 6:
            flash("Enter valid details. Password must contain at least 6 characters.", "danger")
            return render_template("register.html")

        if age < 13 or age > 100 or height <= 0 or weight <= 0:
            flash("Please enter realistic profile values.", "danger")
            return render_template("register.html")

        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO users (name, email, password, age, gender, height, weight, goal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, email, generate_password_hash(password), age,
                gender, height, weight, goal
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            flash("An account with this email already exists.", "danger")
            return render_template("register.html")
        conn.close()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            flash("Welcome back to FitBuddy AI!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    rec = get_recommendations(user)
    return render_template("dashboard.html", user=user, rec=rec)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = get_current_user()

    if request.method == "POST":
        name = request.form["name"].strip()
        age = int(request.form["age"])
        gender = request.form["gender"]
        height = float(request.form["height"])
        weight = float(request.form["weight"])
        goal = request.form["goal"]

        conn = get_db()
        conn.execute("""
            UPDATE users
            SET name=?, age=?, gender=?, height=?, weight=?, goal=?
            WHERE id=?
        """, (name, age, gender, height, weight, goal, session["user_id"]))
        conn.commit()
        conn.close()

        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)


@app.route("/bmi")
@login_required
def bmi():
    user = get_current_user()
    rec = get_recommendations(user)
    return render_template("bmi.html", user=user, rec=rec)


@app.route("/workout")
@login_required
def workout():
    user = get_current_user()
    rec = get_recommendations(user)
    return render_template("workout.html", user=user, rec=rec)


@app.route("/diet")
@login_required
def diet():
    user = get_current_user()
    rec = get_recommendations(user)
    return render_template("diet.html", user=user, rec=rec)


@app.route("/progress", methods=["GET", "POST"])
@login_required
def progress():
    if request.method == "POST":
        weight = float(request.form["weight"])
        notes = request.form.get("notes", "").strip()
        entry_date = request.form.get("entry_date") or date.today().isoformat()

        if weight <= 0:
            flash("Weight must be greater than zero.", "danger")
            return redirect(url_for("progress"))

        conn = get_db()
        conn.execute("""
            INSERT INTO progress (user_id, entry_date, weight, notes)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], entry_date, weight, notes))
        conn.commit()
        conn.close()
        flash("Progress entry added.", "success")
        return redirect(url_for("progress"))

    conn = get_db()
    entries = conn.execute("""
        SELECT * FROM progress
        WHERE user_id = ?
        ORDER BY entry_date DESC, id DESC
    """, (session["user_id"],)).fetchall()
    conn.close()

    return render_template("progress.html", user=get_current_user(), entries=entries)


@app.route("/api/recommendations")
@login_required
def api_recommendations():
    return jsonify(get_recommendations(get_current_user()))


# Create database/tables whenever the application starts.
init_db()

if __name__ == "__main__":
    app.run(debug=True)
