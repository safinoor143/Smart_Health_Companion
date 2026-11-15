import sqlite3, datetime, time
from flask import Blueprint, request, jsonify, abort
from auth import current_user

care = Blueprint("care", __name__)
DB = "falls.db"
MISSED_AFTER_MIN = 2     # demo value; use 15-30 for real use
CANCEL_WINDOW_S = 20     # a fall nobody cancels is sent to the caregiver after this long

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

with db() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS reminders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT, title TEXT, time TEXT, date TEXT, notes TEXT,
        active INTEGER DEFAULT 1, patient_id INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS reminder_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reminder_id INTEGER, day TEXT, due_at TEXT, status TEXT, acked_at TEXT)""")
    for stmt in ("ALTER TABLE reminders ADD COLUMN patient_id INTEGER",
                 "ALTER TABLE events ADD COLUMN patient_id INTEGER"):
        try:
            c.execute(stmt)
        except sqlite3.OperationalError:
            pass   # column already exists

def notify(msg):
    print("[NOTIFY]", msg)

def applies_today(r, today):
    return (not r["date"]) or r["date"] == today

def guard(pid):
    """Allow the patient themself, or a caregiver linked to that patient."""
    u = current_user()
    if not u:
        abort(401)
    if u["id"] == pid:
        return u
    if u["role"] == "caregiver":
        with db() as c:
            if c.execute("SELECT 1 FROM links WHERE patient_id=? AND caregiver_id=?",
                         (pid, u["id"])).fetchone():
                return u
    abort(403)

def escalate_pending():
    """A fall nobody cancelled in time becomes a caregiver alert."""
    cutoff = (datetime.datetime.now() - datetime.timedelta(seconds=CANCEL_WINDOW_S)).strftime("%Y-%m-%d %H:%M:%S")
    with db() as c:
        c.execute("UPDATE events SET status='alert_sent' WHERE result='fall' AND status='pending' AND time<=?", (cutoff,))

def run_checks():
    """Reminder checks: mark due reminders, mark missed ones, alert on missed medicine."""
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    hm = now.strftime("%H:%M")
    earliest = (now - datetime.timedelta(minutes=30)).strftime("%H:%M")
    with db() as c:
        for r in c.execute("SELECT * FROM reminders WHERE active=1 AND patient_id IS NOT NULL").fetchall():
            if not applies_today(r, today) or r["time"] > hm or r["time"] < earliest:
                continue
            log = c.execute("SELECT * FROM reminder_log WHERE reminder_id=? AND day=?",
                            (r["id"], today)).fetchone()
            if log is None:
                c.execute("INSERT INTO reminder_log(reminder_id,day,due_at,status) VALUES(?,?,?,'due')",
                          (r["id"], today, now.strftime("%H:%M:%S")))
                notify("Reminder due for patient %s: %s" % (r["patient_id"], r["title"]))
            elif log["status"] == "due":
                due = datetime.datetime.strptime(today + " " + log["due_at"], "%Y-%m-%d %H:%M:%S")
                if (now - due).total_seconds() > MISSED_AFTER_MIN * 60:
                    c.execute("UPDATE reminder_log SET status='missed' WHERE id=?", (log["id"],))
                    if r["kind"] == "medicine":
                        c.execute("INSERT INTO events(time,result,confidence,status,patient_id) VALUES(?,?,?,?,?)",
                                  (now.strftime("%Y-%m-%d %H:%M:%S"), "missed_reminder", 0,
                                   "alert_sent", r["patient_id"]))
                        notify("MISSED MEDICINE: %s (patient %s) - caregiver alerted" % (r["title"], r["patient_id"]))

_last = [0.0]

@care.before_app_request
def lazy_tick():
    """No background thread on free hosting: do the checks whenever a page polls the server."""
    if not request.path.startswith("/api/"):
        return None
    try:
        escalate_pending()
        t = time.time()
        if t - _last[0] >= 10:
            _last[0] = t
            run_checks()
    except Exception as e:
        print("tick error:", e)
    return None

def start_scheduler():
    pass   # kept so older code still imports; checks now run on requests

@care.route("/api/me")
def me():
    u = current_user()
    if not u:
        abort(401)
    d = dict(id=u["id"], name=u["name"], role=u["role"])
    if u["role"] == "patient":
        d["invite"] = u["invite"]
        d["token"] = u["device_token"]
        with db() as c:
            d["caregivers"] = [r["name"] for r in c.execute(
                "SELECT users.name FROM links JOIN users ON users.id=links.caregiver_id WHERE links.patient_id=?",
                (u["id"],)).fetchall()]
    return jsonify(d)

@care.route("/api/patients")
def patients():
    u = current_user()
    if not u or u["role"] != "caregiver":
        abort(403)
    out = []
    with db() as c:
        pts = c.execute("""SELECT users.id, users.name FROM links
                           JOIN users ON users.id = links.patient_id
                           WHERE links.caregiver_id=? ORDER BY users.name""", (u["id"],)).fetchall()
        for p in pts:
            e = c.execute("""SELECT result, status, time FROM events
                             WHERE patient_id=? AND result IN ('fall','missed_reminder')
                             ORDER BY id DESC LIMIT 1""", (p["id"],)).fetchone()
            alert = "ok"
            if e:
                age = (datetime.datetime.now() - datetime.datetime.strptime(e["time"], "%Y-%m-%d %H:%M:%S")).total_seconds()
                if age < 1800:
                    if e["result"] == "fall" and e["status"] == "pending":
                        alert = "fall_pending"
                    elif e["result"] == "fall" and e["status"] == "alert_sent":
                        alert = "fall_sent"
                    elif e["result"] == "missed_reminder":
                        alert = "missed"
            out.append(dict(id=p["id"], name=p["name"], alert=alert))
    return jsonify(out)

@care.route("/api/link", methods=["POST"])
def link():
    u = current_user()
    if not u or u["role"] != "caregiver":
        abort(403)
    code = ((request.get_json() or {}).get("code") or "").strip().upper()
    with db() as c:
        p = c.execute("SELECT id FROM users WHERE invite=? AND role='patient'", (code,)).fetchone()
        if not p:
            return jsonify(ok=False, error="Invalid invite code"), 404
        c.execute("INSERT OR IGNORE INTO links(patient_id, caregiver_id) VALUES(?,?)", (p["id"], u["id"]))
    return jsonify(ok=True)

@care.route("/api/care/<int:pid>/reminders", methods=["POST"])
def add_reminder(pid):
    guard(pid)
    b = request.get_json()
    if not b.get("title") or not b.get("time"):
        abort(400)
    with db() as c:
        c.execute("INSERT INTO reminders(kind,title,time,date,notes,patient_id) VALUES(?,?,?,?,?,?)",
                  (b["kind"], b["title"], b["time"], b.get("date", ""), b.get("notes", ""), pid))
    return jsonify(ok=True)

@care.route("/api/care/<int:pid>/reminders/<int:rid>", methods=["DELETE"])
def del_reminder(pid, rid):
    guard(pid)
    with db() as c:
        c.execute("UPDATE reminders SET active=0 WHERE id=? AND patient_id=?", (rid, pid))
    return jsonify(ok=True)

@care.route("/api/care/<int:pid>/today")
def today_list(pid):
    guard(pid)
    today = datetime.date.today().strftime("%Y-%m-%d")
    hm = datetime.datetime.now().strftime("%H:%M")
    out = []
    with db() as c:
        for r in c.execute("SELECT * FROM reminders WHERE active=1 AND patient_id=? ORDER BY time", (pid,)).fetchall():
            if not applies_today(r, today):
                continue
            log = c.execute("SELECT status FROM reminder_log WHERE reminder_id=? AND day=?",
                            (r["id"], today)).fetchone()
            status = log["status"] if log else ("upcoming" if r["time"] > hm else "skipped")
            out.append(dict(id=r["id"], kind=r["kind"], title=r["title"], time=r["time"], status=status))
    return jsonify(out)

@care.route("/api/care/<int:pid>/alerts")
def alerts_list(pid):
    guard(pid)
    with db() as c:
        rows = c.execute("""SELECT id, time, result, confidence, status FROM events
                            WHERE patient_id=? AND result IN ('fall','missed_reminder')
                            ORDER BY id DESC LIMIT 8""", (pid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@care.route("/api/care/<int:pid>/falls/<int:eid>/cancel", methods=["POST"])
def cancel_fall(pid, eid):
    u = guard(pid)
    if u["id"] != pid:
        abort(403)   # only the patient can say "I am OK"
    with db() as c:
        c.execute("UPDATE events SET status='cancelled' WHERE id=? AND patient_id=? AND status='pending'", (eid, pid))
    return jsonify(ok=True)

@care.route("/api/care/<int:pid>/ack/<int:rid>", methods=["POST"])
def ack(pid, rid):
    u = guard(pid)
    if u["id"] != pid:
        abort(403)   # only the patient confirms their own dose
    today = datetime.date.today().strftime("%Y-%m-%d")
    now = datetime.datetime.now().strftime("%H:%M:%S")
    with db() as c:
        if not c.execute("SELECT 1 FROM reminders WHERE id=? AND patient_id=?", (rid, pid)).fetchone():
            abort(404)
        c.execute("UPDATE reminder_log SET status='taken', acked_at=? WHERE reminder_id=? AND day=? AND status='due'",
                  (now, rid, today))
        c.execute("UPDATE reminder_log SET status='late', acked_at=? WHERE reminder_id=? AND day=? AND status='missed'",
                  (now, rid, today))
    return jsonify(ok=True)