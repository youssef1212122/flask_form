from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key_change_in_production"

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

def check_auth():
    return "user" in session


@app.route("/")
def home():
    if check_auth():
        return redirect("/dashboard")
    return redirect("/login")


@app.route("/dashboard")
def dashboard():
    if not check_auth():
        return redirect("/login")
    
    username = session.get("user", "User")
    return render_template("dashboard.html", username=username)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if check_auth():
        return redirect("/login")
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("signup.html", error="Please fill in all fields")

        if len(username) < 3:
            return render_template("signup.html", error="The username must be at least 3 characters long.")

        if len(password) < 6:
            return render_template("signup.html", error="The password must be at least 6 characters long.")

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        try:
            hashed_password = generate_password_hash(password)
            c.execute("INSERT INTO users(username, password) VALUES (?, ?)", 
                      (username, hashed_password))
            conn.commit()
            conn.close()
            
            return redirect("/login")
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("signup.html", error="The username already exists")
        except Exception as e:
            conn.close()
            return render_template("signup.html", error="An error occurred, please try again.")

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if check_auth():
        return redirect("/dashboard")
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("login.html", error="Please fill in all fields")

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Incorrect username or password")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)