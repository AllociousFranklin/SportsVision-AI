import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_utils import get_connection
from pushup_counter import analyze_pushups
from vertical_jump_max_height import analyze_jump
from boxing import analyze_punching_speed
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
app.secret_key = "supersecretkey"

# ✅ helper: require login
def login_required(role=None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in first.")
                return redirect(url_for("login"))

            if role and session.get("role") != role:
                flash("Unauthorized access.")
                return redirect(url_for("landing"))

            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

# ✅ Sign Up Page
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        age = int(request.form["age"])
        height_cm = float(request.form["height_cm"])
        weight_kg = float(request.form["weight_kg"])
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, age, height_cm, weight_kg, email, password, role) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (name, age, height_cm, weight_kg, email, generate_password_hash(password), role)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("✅ Account created successfully! Please log in.")
        return redirect(url_for("login"))
    return render_template("signup.html")
# log in
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["user_id"]
            session["role"] = user["role"]
            session["name"] = user["name"]

            if user["role"] == "Player":
                return redirect(url_for("index"))  # Upload + analyze page
            else:
                return redirect(url_for("leaderboard"))  # Coaches see leaderboard
        else:
            flash("❌ Invalid email or password")
    return render_template("login.html")

# ✅ Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!")
    return redirect(url_for("login"))

# ✅ Landing Page
@app.route("/")
def landing():
    return render_template("landing.html")
# ✅ Insert user into DB
def register_user(name, age, height_cm, weight_kg):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, age, height_cm, weight_kg) VALUES (%s, %s, %s, %s)",
        (name, age, height_cm, weight_kg)
    )
    conn.commit()
    user_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return user_id

@app.route("/index")
@login_required(role="Player")
def index():
    return render_template("index.html", user=session)

@app.route("/analyze_v_up_form")
@login_required(role="Player")
def analyze_v_up_form():
    return render_template("analyze_v_up.html", user=session)

@app.route("/analyze_v_up", methods=["POST"])
@login_required(role="Player")
def analyze_v_up():
    name = session["name"]
    user_id = session["user_id"]
    height_cm = float(request.form["height_cm"]) if "height_cm" in request.form else 170
    weight_kg = float(request.form["weight_kg"]) if "weight_kg" in request.form else 70
    test_type = request.form["test_type"]

    # Save video
    video = request.files["video"]
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], video.filename)
    video.save(video_path)

    # Run analysis
    if test_type == "pushups":
        findings = f"Total Push-ups: {analyze_pushups(video_path, user_id, show_video=False)}"
    elif test_type == "jump":
        findings = f"Vertical Jump Height: {analyze_jump(video_path, user_height_cm=height_cm, user_id=user_id, show_video=False):.2f} cm"
    else:
        result = analyze_punching_speed(video_path, user_id=user_id, hand="RIGHT", show=False)
        findings = f"Total Punches: {result['total_punches']}\nDuration: {result['duration_sec']:.2f}s\nPunches/sec: {result['punches_per_sec']:.2f}\nPunches/min: {result['punches_per_min']:.2f}"

    return render_template("results.html", user=session, test_type=test_type, findings=findings)


@app.route("/analyze", methods=["POST"])
def analyze():
    name = request.form["name"]
    age = int(request.form["age"])
    height_cm = float(request.form["height_cm"])
    weight_kg = float(request.form["weight_kg"])
    test_type = request.form["test_type"]

    # Save user
    user_id = register_user(name, age, height_cm, weight_kg)

    # Save video
    video = request.files["video"]
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], video.filename)
    video.save(video_path)

    # Run analysis
    if test_type == "pushups":
        findings = f"Total Push-ups: {analyze_pushups(video_path, user_id, show_video=False)}"
    elif test_type == "jump":
        findings = f"Vertical Jump Height: {analyze_jump(video_path, user_height_cm=height_cm, user_id=user_id, show_video=False):.2f} cm"
    else:  # punches
        result = analyze_punching_speed(video_path, user_id=user_id, hand="RIGHT", show=False)
        findings = f"Total Punches: {result['total_punches']}\nDuration: {result['duration_sec']:.2f}s\nPunches/sec: {result['punches_per_sec']:.2f}\nPunches/min: {result['punches_per_min']:.2f}"

    # Send results to frontend
    user = {"name": name, "age": age, "height_cm": height_cm, "weight_kg": weight_kg}
    return render_template("results.html", user=user, test_type=test_type, findings=findings)

@app.route("/leaderboard")
@login_required(role="Coach")
def leaderboard():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.name, p.total_pushups, p.analyzed_at
        FROM pushups p JOIN users u ON p.user_id = u.user_id
        ORDER BY p.total_pushups DESC
    """)
    pushups_all = cursor.fetchall()

    cursor.execute("""
        SELECT u.name, v.jump_height_cm, v.analyzed_at
        FROM vertical_jumps v JOIN users u ON v.user_id = u.user_id
        ORDER BY v.jump_height_cm DESC
    """)
    jumps_all = cursor.fetchall()

    cursor.execute("""
        SELECT u.name, p.total_punches, p.analyzed_at
        FROM punches p JOIN users u ON p.user_id = u.user_id
        ORDER BY p.total_punches DESC
    """)
    punches_all = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "leaderboard.html",
        pushups_all=pushups_all,
        jumps_all=jumps_all,
        punches_all=punches_all
    )


if __name__ == "__main__":
    app.run(debug=True)

