from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key_change_in_production"

# ===== Database Setup =====
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

# ===== Helper Functions =====
def check_auth():
    """التحقق من تسجيل الدخول"""
    return "user" in session

# ===== Routes =====

@app.route("/")
def home():
    if check_auth():
        return redirect("/dashboard")
    return redirect("/login")


@app.route("/dashboard")
def dashboard():
    """الصفحة الرئيسية بعد تسجيل الدخول"""
    if not check_auth():
        return redirect("/login")
    
    username = session.get("user", "User")
    return render_template("dashboard.html", username=username)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if check_auth():
        return redirect("/dashboard")
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # التحقق من البيانات
        if not username or not password:
            return render_template("signup.html", error="يرجى ملء جميع الحقول")

        if len(username) < 3:
            return render_template("signup.html", error="اسم المستخدم يجب أن يكون 3 أحرف على الأقل")

        if len(password) < 6:
            return render_template("signup.html", error="كلمة المرور يجب أن تكون 6 أحرف على الأقل")

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        try:
            # تشفير كلمة المرور
            hashed_password = generate_password_hash(password)
            c.execute("INSERT INTO users(username, password) VALUES (?, ?)", 
                      (username, hashed_password))
            conn.commit()
            conn.close()
            
            # تسجيل الدخول تلقائياً
            session["user"] = username
            return redirect("/dashboard")
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("signup.html", error="اسم المستخدم موجود بالفعل!")
        except Exception as e:
            conn.close()
            return render_template("signup.html", error="حدث خطأ، حاول مرة أخرى")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if check_auth():
        return redirect("/dashboard")
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("login.html", error="يرجى ملء جميع الحقول")

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="اسم المستخدم أو كلمة المرور غير صحيحة")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """تسجيل الخروج"""
    session.pop("user", None)
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)