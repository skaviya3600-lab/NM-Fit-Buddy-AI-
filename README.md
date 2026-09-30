# FitBuddy AI – Your Personal Fitness & Wellness Assistant

## NM (Naan Mudhalvan) Project

FitBuddy AI is a beginner-friendly fitness and wellness web application built with Python Flask, HTML, CSS, JavaScript and SQLite.

### Main Features

1. User Registration and Login
2. User Profile
3. BMI Calculator
4. Daily Calorie Requirement Calculator
5. Personalized Fitness Recommendations
6. Basic Workout Recommendations
7. Healthy Food Recommendations
8. Daily Water Intake Recommendation
9. Progress Tracking
10. Rule-based AI fitness recommendations
11. Dashboard
12. Logout

## Technology Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python Flask
- Database: SQLite
- Password Security: Werkzeug password hashing
- Data: JSON sample workout and food data

## Requirements

- Python 3.9 or newer
- A modern web browser

## Installation

Open a terminal inside the `FitBuddy_AI` folder.

### Windows

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open:

`http://127.0.0.1:5000`


## Demo Login

- Email: `demo@fitbuddy.local`
- Password: `demo123`

## Database

The included `database.db` contains the required `users` and `progress` tables. The application also runs `init_db()` at startup, so a missing database can be recreated automatically.

## AI Logic

This student project uses simple rule-based logic rather than an external AI API. Recommendations are generated from:

- BMI category
- Fitness goal
- Age
- Gender
- Height
- Weight

This makes the project easy to explain during an NM project review or viva.

## Important Note

BMI, calorie and water calculations are educational estimates. They are not medical diagnosis or individualized medical advice.

## Suggested Viva Points

### What is Flask?
Flask is a lightweight Python web framework used to build the backend of the application.

### Why SQLite?
SQLite is simple, file-based and suitable for small college projects.

### What is BMI?
BMI is calculated as weight in kilograms divided by height in meters squared.

### What is the AI component?
The project implements explainable rule-based recommendations. For example, the user's goal and BMI category are used to select suitable workout, food and lifestyle suggestions.

### Main Database Tables

**users**
- id
- name
- email
- password
- age
- gender
- height
- weight
- goal
- created_at

**progress**
- id
- user_id
- entry_date
- weight
- notes

## Troubleshooting

If the port is busy, change the final line in `app.py` to:

```python
app.run(debug=True, port=5001)
```

Then open `http://127.0.0.1:5001`.

If you modify the database schema during development, you can delete `database.db` and restart the app; the tables will be created again.
