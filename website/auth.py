import sqlite3, secrets, os, string
from functools import wraps
from flask import Blueprint, request, session, redirect, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint("auth", __name__)
DB = "falls.db"

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

with db() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT UNIQUE, pw TEXT, role TEXT, invite TEXT, created TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS links(
        patient_id INTEGER, caregiver_id INTEGER, UNIQUE(patient_id, caregiver_id))""")
    try:
        c.execute("ALTER TABLE users ADD COLUMN device_token TEXT")
    except sqlite3.OperationalError:
        pass   # column already exists
    for r in c.execute("SELECT id FROM users WHERE role='patient' AND (device_token IS NULL OR device_token='')").fetchall():
        c.execute("UPDATE users SET device_token=? WHERE id=?", (secrets.token_hex(10), r["id"]))

def init_auth(app):
    key_file = "secret.key"
    if not os.path.exists(key_file):
        with open(key_file, "w") as f:
            f.write(secrets.token_hex(32))
    with open(key_file) as f:
        app.secret_key = f.read().strip()
    app.register_blueprint(auth)

def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    with db() as c:
        return c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()

def login_required(role=None):
    def deco(f):
        @wraps(f)
        def wrapper(*a, **k):
            u = current_user()
            if not u or (role and u["role"] != role):
                return redirect("/")
            return f(*a, **k)
        return wrapper
    return deco

def new_invite():
    chars = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
    while True:
        code = "".join(secrets.choice(chars) for _ in range(6))
        with db() as c:
            if not c.execute("SELECT 1 FROM users WHERE invite=?", (code,)).fetchone():
                return code

@auth.route("/api/signup", methods=["POST"])
def api_signup():
    b = request.get_json() or {}
    site = current_app.config.get("SITE")
    role = site if site in ("patient", "caregiver") else b.get("role")
    name = (b.get("name") or "").strip()
    email = (b.get("email") or "").strip().lower()
    pw = b.get("password") or ""
    if not name or "@" not in email or len(pw) < 6 or role not in ("patient", "caregiver"):
        return jsonify(ok=False, error="Fill every field. The password needs 6 or more characters."), 400
    invite = new_invite() if role == "patient" else None
    token = secrets.token_hex(10) if role == "patient" else None
    try:
        with db() as c:
            cur = c.execute(
                "INSERT INTO users(name,email,pw,role,invite,created,device_token) "
                "VALUES(?,?,?,?,?,datetime('now','localtime'),?)",
                (name, email, generate_password_hash(pw), role, invite, token))
        session["uid"] = cur.lastrowid
        return jsonify(ok=True)
    except sqlite3.IntegrityError:
        return jsonify(ok=False, error="That email is already registered."), 400

@auth.route("/api/login", methods=["POST"])
def api_login():
    b = request.get_json() or {}
    email = (b.get("email") or "").strip().lower()
    with db() as c:
        u = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if u and check_password_hash(u["pw"], b.get("password") or ""):
        site = current_app.config.get("SITE")
        if site and u["role"] != site:
            other = "5001" if u["role"] == "caregiver" else "5000"
            return jsonify(ok=False, error="This is a %s account. Please use the %s website (port %s)."
                           % (u["role"], u["role"], other)), 403
        want = b.get("role")
        if want in ("patient", "caregiver") and u["role"] != want:
            return jsonify(ok=False, error="This is a %s account. Please choose %s above."
                           % (u["role"], u["role"].capitalize())), 403
        session["uid"] = u["id"]
        return jsonify(ok=True)
    return jsonify(ok=False, error="Wrong email or password."), 401

@auth.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify(ok=True)

@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")

def go_home():
    return redirect("/")

for _p in ("/login", "/signup", "/home", "/patient", "/caregiver"):
    auth.add_url_rule(_p, endpoint="go_" + _p.strip("/"), view_func=go_home)