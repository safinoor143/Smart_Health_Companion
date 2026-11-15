import os, time
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # so falls.db and secret.key live next to this file
os.environ["TZ"] = "Asia/Kolkata"                        # reminder times are India time on any server
try:
    time.tzset()
except AttributeError:
    pass                                                 # Windows already uses the PC's time zone

import sqlite3, datetime, threading
from flask import Flask, request, jsonify

DB = "falls.db"

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

with db() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT, result TEXT, confidence REAL, status TEXT)""")
    try:
        c.execute("ALTER TABLE events ADD COLUMN patient_id INTEGER")
    except sqlite3.OperationalError:
        pass   # column already exists

from auth import init_auth
from care import care, escalate_pending
from features import feat
from pages import HTML
from tgbot import tg, dispatch, TG_NAV, TG_SECTION, TG_JS
try:
    from chat import chat, CHAT_NAV, CHAT_SECTION, CHAT_JS
    HAVE_CHAT = True
except ImportError:
    HAVE_CHAT = False

ROLE_PICKER = ('<label>I am a</label>'
               '<div class="roles"><label class="role"><input type="radio" name="l_role" value="patient" checked><span>Patient</span></label>'
               '<label class="role"><input type="radio" name="l_role" value="caregiver"><span>Caregiver</span></label></div>')

def build_page():
    h = HTML
    # Patient / Caregiver choice on the Log in tab (Sign up already has one)
    h = h.replace('<label>Email</label><input id="l_email"', ROLE_PICKER + '<label>Email</label><input id="l_email"', 1)
    h = h.replace("password:$('l_pw').value})",
                  "password:$('l_pw').value,role:document.querySelector('input[name=l_role]:checked').value})", 1)
    h = h.replace("confidence ${e.confidence}", "impact ${e.confidence} g")
    # "Cancel - I am OK" button inside the red fall banner (shown only to the patient)
    h = h.replace(r"waiting for the user to cancel...</div>'}",
                  r"""waiting for the user to cancel...</div>'+(CANACK?'<button class="btn" style="margin-left:auto" onclick="cancelFall('+latest.id+')">Cancel - I am OK</button>':'')}""")
    h = h.replace("</script></body></html>",
                  "async function cancelFall(id){await fetch('/api/care/'+MYID+'/falls/'+id+'/cancel',{method:'POST'});loadAlerts()}</script></body></html>")
    if HAVE_CHAT:
        h = h.replace('<button data-sec="device" class="only-patient">',
                      CHAT_NAV + '<button data-sec="device" class="only-patient">', 1)
        h = h.replace("</main></div>", CHAT_SECTION + "</main></div>", 1)
        h = h.replace("</script></body></html>", CHAT_JS + "</script></body></html>")
    # Telegram alerts tab (caregivers connect their Telegram here)
    h = h.replace('<button data-sec="device" class="only-patient">',
                  TG_NAV + '<button data-sec="device" class="only-patient">', 1)
    h = h.replace("</main></div>", TG_SECTION + "</main></div>", 1)
    h = h.replace("</script></body></html>", TG_JS + "</script></body></html>")
    return h

PAGE = build_page()

app = Flask(__name__)
app.config["SESSION_COOKIE_NAME"] = "hc_session"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
init_auth(app)
app.register_blueprint(care)
app.register_blueprint(feat)
app.register_blueprint(tg)
if HAVE_CHAT:
    app.register_blueprint(chat)

# ---- limit wrong-password attempts (the site is public) ----
FAILS = {}

def client_ip():
    return (request.headers.get("X-Forwarded-For") or request.remote_addr or "").split(",")[0].strip()

@app.before_request
def throttle_login():
    if request.path == "/api/login" and request.method == "POST":
        ip, t = client_ip(), time.time()
        FAILS[ip] = [x for x in FAILS.get(ip, []) if t - x < 900]
        if len(FAILS[ip]) >= 8:
            return jsonify(ok=False, error="Too many attempts. Please try again in a few minutes."), 429
    return None

@app.after_request
def count_login_fail(resp):
    if request.path == "/api/login" and request.method == "POST" and resp.status_code in (401, 403):
        FAILS.setdefault(client_ip(), []).append(time.time())
    return resp

# ---- the wearable ----
def patient_from_token():
    tok = request.args.get("token", "")
    if not tok:
        return None
    with db() as c:
        r = c.execute("SELECT id FROM users WHERE device_token=? AND role='patient'", (tok,)).fetchone()
    return r["id"] if r else None

@app.route("/")
def index():
    return PAGE

@app.route("/api/fall", methods=["POST"])
def fall():
    pid = patient_from_token()
    if pid is None:
        return jsonify(error="invalid device token"), 401
    b = request.get_json(silent=True) or {}
    try:
        peak = float(b.get("peak", 0))
    except (TypeError, ValueError):
        peak = 0.0
    with db() as c:
        cur = c.execute("INSERT INTO events(time,result,confidence,status,patient_id) VALUES(?,?,?,?,?)",
                        (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "fall", round(peak, 1), "pending", pid))
        eid = cur.lastrowid
    return jsonify(id=eid)

@app.route("/api/cancel/<int:eid>", methods=["POST"])
def cancel(eid):
    pid = patient_from_token()
    if pid is None:
        return jsonify(error="invalid device token"), 401
    with db() as c:
        c.execute("UPDATE events SET status='cancelled' WHERE id=? AND status='pending' AND patient_id=?", (eid, pid))
    return jsonify(ok=True)

@app.route("/api/confirm/<int:eid>", methods=["POST"])
def confirm(eid):
    pid = patient_from_token()
    if pid is None:
        return jsonify(error="invalid device token"), 401
    with db() as c:
        c.execute("UPDATE events SET status='alert_sent' WHERE id=? AND status='pending' AND patient_id=?", (eid, pid))
    return jsonify(ok=True)

# ---- background sender: Telegram alerts to caregivers only ----
def _alert_loop():
    while True:
        try:
            escalate_pending()   # un-cancelled falls become "alert_sent" after 20 s
            dispatch()           # sends Telegram messages to linked caregivers only
        except Exception as e:
            print("alert loop error:", e)
        time.sleep(5)

threading.Thread(target=_alert_loop, daemon=True).start()

if __name__ == "__main__":
    print("Smart Health Companion - ONE website for patients and caregivers: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000)