import sqlite3, datetime
from flask import Blueprint, request, jsonify, abort
from care import guard

feat = Blueprint("feat", __name__)
DB = "falls.db"

# latest sensor window per patient (in memory, shared by both websites)
LIVE = {}

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

with db() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS patient_conditions(
        patient_id INTEGER, condition TEXT, UNIQUE(patient_id, condition))""")
    c.execute("""CREATE TABLE IF NOT EXISTS vitals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER, time TEXT, kind TEXT, value REAL, value2 REAL)""")

BASE = [
    ("wake-up", "Wake up, stretch and take a few slow breaths", "07:00"),
    ("meal", "Breakfast", "08:00"),
    ("hydration", "Drink a glass of water", "09:00"),
    ("hydration", "Drink a glass of water", "11:00"),
    ("meal", "Lunch", "13:00"),
    ("hydration", "Drink a glass of water", "15:00"),
    ("activity", "Gentle walk or light movement", "17:30"),
    ("meal", "Dinner", "19:30"),
    ("bedtime", "Wind down: dim the lights, get ready for bed", "21:30"),
]
EXTRA = {
    "diabetes": [("vitals", "Check blood sugar before breakfast", "07:30"),
                 ("meal", "Healthy snack (no sugary drinks)", "16:00"),
                 ("activity", "Check your feet for cuts or sores", "20:00"),
                 ("vitals", "Check blood sugar after dinner", "21:00")],
    "hypertension": [("vitals", "Check blood pressure", "08:15"),
                     ("activity", "20 minute easy walk", "18:00"),
                     ("vitals", "Check blood pressure", "20:30")],
    "heart": [("vitals", "Check pulse and note how you feel", "08:15"),
              ("activity", "Short easy walk, rest if breathless", "17:00"),
              ("vitals", "Check pulse", "20:30")],
    "arthritis": [("activity", "Gentle joint stretches", "08:30"),
                  ("activity", "Gentle joint stretches", "18:30")],
    "fall_risk": [("activity", "Check walkways and wear non-slip footwear", "07:15"),
                  ("activity", "Balance exercise near a sturdy support", "10:00")],
}

KINDS = ("pulse", "spo2", "bp", "sugar", "temp")
RANGES = {"pulse": (50, 110), "spo2": (92, 100), "sugar": (70, 250), "temp": (35.5, 38.0)}

def flagged(kind, v, v2):
    if kind == "bp":
        return v >= 160 or v2 >= 100 or v < 90
    lo, hi = RANGES[kind]
    return v < lo or v > hi

@feat.route("/api/care/<int:pid>/conditions")
def conditions(pid):
    guard(pid)
    with db() as c:
        rows = c.execute("SELECT condition FROM patient_conditions WHERE patient_id=?", (pid,)).fetchall()
    return jsonify([r["condition"] for r in rows])

@feat.route("/api/care/<int:pid>/routine", methods=["POST"])
def apply_routine(pid):
    guard(pid)
    conds = [x for x in (request.get_json() or {}).get("conditions", []) if x in EXTRA]
    items = list(BASE)
    for k in conds:
        items += EXTRA[k]
    added = 0
    with db() as c:
        c.execute("DELETE FROM patient_conditions WHERE patient_id=?", (pid,))
        for k in conds:
            c.execute("INSERT INTO patient_conditions(patient_id, condition) VALUES(?,?)", (pid, k))
        for kind, title, tm in items:
            exists = c.execute("""SELECT 1 FROM reminders WHERE patient_id=? AND active=1
                                  AND title=? AND time=? AND (date IS NULL OR date='')""",
                               (pid, title, tm)).fetchone()
            if not exists:
                c.execute("INSERT INTO reminders(kind,title,time,date,notes,patient_id) VALUES(?,?,?,?,?,?)",
                          (kind, title, tm, "", "routine", pid))
                added += 1
    return jsonify(ok=True, added=added)

@feat.route("/api/care/<int:pid>/vitals", methods=["GET", "POST"])
def vitals(pid):
    guard(pid)
    if request.method == "POST":
        b = request.get_json() or {}
        kind = b.get("kind")
        if kind not in KINDS:
            abort(400)
        try:
            v = float(b.get("value"))
            v2 = float(b.get("value2") or 0)
        except (TypeError, ValueError):
            abort(400)
        if kind == "bp" and v2 <= 0:
            abort(400)
        with db() as c:
            c.execute("INSERT INTO vitals(patient_id,time,kind,value,value2) VALUES(?,?,?,?,?)",
                      (pid, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), kind, v, v2))
        return jsonify(ok=True, flag=flagged(kind, v, v2))
    with db() as c:
        rows = c.execute("""SELECT time, kind, value, value2 FROM vitals
                            WHERE patient_id=? ORDER BY id DESC LIMIT 60""", (pid,)).fetchall()
    return jsonify([dict(time=r["time"], kind=r["kind"], value=r["value"], value2=r["value2"],
                         flag=flagged(r["kind"], r["value"], r["value2"])) for r in rows])

@feat.route("/api/care/<int:pid>/appointments")
def appointments(pid):
    guard(pid)
    today = datetime.date.today().strftime("%Y-%m-%d")
    with db() as c:
        rows = c.execute("""SELECT id, title, date, time FROM reminders
                            WHERE patient_id=? AND active=1 AND kind='appointment' AND date>=?
                            ORDER BY date, time""", (pid, today)).fetchall()
    return jsonify([dict(r) for r in rows])

@feat.route("/api/care/<int:pid>/live")
def live(pid):
    guard(pid)
    return jsonify(LIVE.get(pid) or {})