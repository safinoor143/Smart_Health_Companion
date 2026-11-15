import os, re, time, string, secrets, sqlite3, datetime
import requests
from flask import Blueprint, request, jsonify, abort
from auth import current_user

tg = Blueprint("tg", __name__)
DB = "falls.db"
NOTIFY_POSSIBLE = True                       # also tell caregivers the moment a possible fall is detected
LOOKBACK_HOURS = 2                           # never send alerts older than this

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

with db() as c:
    c.execute("CREATE TABLE IF NOT EXISTS tg_links(user_id INTEGER PRIMARY KEY, chat_id TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS tg_codes(code TEXT PRIMARY KEY, user_id INTEGER, created TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS tg_state(k TEXT PRIMARY KEY, v TEXT)")
    for stmt in ("ALTER TABLE events ADD COLUMN tg TEXT DEFAULT ''",
                 "ALTER TABLE events ADD COLUMN note TEXT"):
        try:
            c.execute(stmt)
        except sqlite3.OperationalError:
            pass   # column already exists

def get_state(k, default=""):
    with db() as c:
        r = c.execute("SELECT v FROM tg_state WHERE k=?", (k,)).fetchone()
    return r["v"] if r else default

def set_state(k, v):
    with db() as c:
        c.execute("INSERT OR REPLACE INTO tg_state(k,v) VALUES(?,?)", (k, str(v)))

def bot_token():
    t = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not t and os.path.exists("telegram.token"):
        with open("telegram.token") as f:
            t = f.read().strip()
    return t

_down_until = [0.0]
LAST_ERROR = [""]

def net_down():
    return time.time() < _down_until[0]

def api(method, force=False, **params):
    tok = bot_token()
    if not tok:
        LAST_ERROR[0] = "No bot token: the telegram.token file is missing."
        return None
    if not force and net_down():
        return None
    try:
        r = requests.post("https://api.telegram.org/bot%s/%s" % (tok, method), json=params, timeout=(3, 6))
    except requests.RequestException:
        _down_until[0] = time.time() + 120
        LAST_ERROR[0] = "This server cannot reach api.telegram.org (blocked or no internet)."
        return None
    try:
        data = r.json()
    except ValueError:
        _down_until[0] = time.time() + 60
        LAST_ERROR[0] = "Telegram gave an unreadable answer (HTTP %s)." % r.status_code
        return None
    if not data.get("ok"):
        LAST_ERROR[0] = "Telegram said: %s" % data.get("description", r.status_code)
        return None
    LAST_ERROR[0] = ""
    return data.get("result")

def bot_username():
    u = get_state("bot_username")
    if u:
        return u
    me = api("getMe", force=True)
    if me and me.get("username"):
        set_state("bot_username", me["username"])
        return me["username"]
    return ""

def chat_of(user_id):
    with db() as c:
        r = c.execute("SELECT chat_id FROM tg_links WHERE user_id=?", (user_id,)).fetchone()
    return r["chat_id"] if r else None

def send_chat(chat_id, text, force=False):
    return api("sendMessage", force=force, chat_id=chat_id, text=text) is not None

def send_user(user_id, text):
    cid = chat_of(user_id)
    return bool(cid) and send_chat(cid, text)

def caregiver_chats(pid):
    with db() as c:
        rows = c.execute("""SELECT t.chat_id FROM links l JOIN tg_links t ON t.user_id = l.caregiver_id
                            WHERE l.patient_id=?""", (pid,)).fetchall()
    return [r["chat_id"] for r in rows]

def _send_all(chat_ids, text):
    return any([send_chat(cid, text) for cid in chat_ids]) if chat_ids else True

def notify_reminder(pid, kind, title, hm):
    """Reminders are no longer sent by Telegram (alerts go to caregivers only).
    Kept so existing calls from app.py keep working."""
    return

_last_dispatch = [0.0]

def dispatch(force=False):
    """Send Telegram messages to caregivers for new falls and missed medicines (each event is handled once)."""
    if not bot_token() or net_down():
        return
    t = time.time()
    if not force and t - _last_dispatch[0] < 2:
        return
    _last_dispatch[0] = t
    since = (datetime.datetime.now() - datetime.timedelta(hours=LOOKBACK_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
    with db() as c:
        rows = c.execute("""SELECT e.id, e.time, e.result, e.status, COALESCE(e.tg,'') AS tg, e.note,
                                   e.patient_id, u.name
                            FROM events e JOIN users u ON u.id = e.patient_id
                            WHERE e.result IN ('fall','missed_reminder') AND COALESCE(e.tg,'') != 'done'
                              AND e.time >= ? ORDER BY e.id LIMIT 20""", (since,)).fetchall()
    for e in rows:
        if net_down():
            break
        pid, name, hm = e["patient_id"], e["name"], e["time"][11:16]
        cg = caregiver_chats(pid)
        new = None
        if e["result"] == "fall":
            if e["status"] == "pending" and e["tg"] == "":
                if NOTIFY_POSSIBLE:
                    _send_all(cg, "\u26a0\ufe0f Possible fall: %s at %s. Waiting a few seconds to see if they cancel." % (name, hm))
                new = "pending"
            elif e["status"] == "alert_sent" and e["tg"] in ("", "pending"):
                _send_all(cg, "\U0001F6A8 FALL ALERT: %s fell at %s and did not cancel. Please check on them now." % (name, hm))
                new = "done"
            elif e["status"] == "cancelled" and e["tg"] in ("", "pending"):
                if e["tg"] == "pending" and NOTIFY_POSSIBLE:
                    _send_all(cg, "\u2705 %s is OK: the fall alert was cancelled." % name)
                new = "done"
        elif e["status"] == "alert_sent" and e["tg"] == "":
            what = e["note"] or "their medicine"
            _send_all(cg, "\U0001F48A Missed medicine: %s did not confirm %s (due %s)." % (name, what, hm))
            new = "done"
        if net_down():
            break            # not delivered: leave it unmarked and try again when the network is back
        if new:
            with db() as c:
                c.execute("UPDATE events SET tg=? WHERE id=?", (new, e["id"]))

def process_updates():
    """Read new messages sent to the bot and link Telegram chats to website accounts."""
    off = int(get_state("offset", "0") or 0)
    res = api("getUpdates", force=True, offset=off, timeout=0, allowed_updates=["message"])
    if res is None:
        return False
    for upd in res:
        off = max(off, upd["update_id"] + 1)
        msg = upd.get("message") or {}
        text = (msg.get("text") or "").strip()
        cid = (msg.get("chat") or {}).get("id")
        if not cid or not text:
            continue
        parts = text.split()
        code = ""
        if parts[0].lower().startswith("/start") and len(parts) > 1:
            code = parts[1].upper()
        elif len(parts) == 1 and re.fullmatch(r"[A-Za-z0-9]{8}", parts[0]):
            code = parts[0].upper()
        if not code:
            send_chat(cid, "Hi! I send fall and medicine alerts to caregivers. To connect: open the website, press 'Connect Telegram', and tap the link it shows.", force=True)
            continue
        with db() as c:
            row = c.execute("SELECT code, user_id, created FROM tg_codes WHERE code=?", (code,)).fetchone()
        fresh = False
        if row:
            age = (datetime.datetime.now() - datetime.datetime.strptime(row["created"], "%Y-%m-%d %H:%M:%S")).total_seconds()
            fresh = age < 900
        if not row or not fresh:
            send_chat(cid, "That code is not valid or has expired. Press 'Connect Telegram' on the website to get a new link.", force=True)
            continue
        with db() as c:
            c.execute("INSERT OR REPLACE INTO tg_links(user_id, chat_id) VALUES(?,?)", (row["user_id"], str(cid)))
            c.execute("DELETE FROM tg_codes WHERE code=?", (code,))
            u = c.execute("SELECT name FROM users WHERE id=?", (row["user_id"],)).fetchone()
        send_chat(cid, "\u2705 Connected! Hello %s. Your alerts will arrive here." % (u["name"] if u else ""), force=True)
    set_state("offset", off)
    return True

def me_or_401():
    u = current_user()
    if not u:
        abort(401)
    return u

@tg.route("/api/telegram/status")
def status():
    u = me_or_401()
    configured = bool(bot_token())
    linked = bool(chat_of(u["id"]))
    if configured and not linked:
        bot_username()   # warm the cache; failures show up as an error message
    return jsonify(configured=configured, linked=linked, error=LAST_ERROR[0] if configured and not linked else "")

@tg.route("/api/telegram/connect", methods=["POST"])
def connect():
    u = me_or_401()
    if not bot_token():
        return jsonify(ok=False, error="Telegram is not set up on this server yet (telegram.token is missing)."), 503
    name = bot_username()
    if not name:
        return jsonify(ok=False, error=LAST_ERROR[0] or "Could not reach Telegram."), 502
    chars = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
    code = "".join(secrets.choice(chars) for _ in range(8))
    now = datetime.datetime.now()
    old = (now - datetime.timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    with db() as c:
        c.execute("DELETE FROM tg_codes WHERE user_id=? OR created < ?", (u["id"], old))
        c.execute("INSERT INTO tg_codes(code,user_id,created) VALUES(?,?,?)",
                  (code, u["id"], now.strftime("%Y-%m-%d %H:%M:%S")))
    return jsonify(ok=True, link="https://t.me/%s?start=%s" % (name, code))

@tg.route("/api/telegram/check", methods=["POST"])
def check():
    u = me_or_401()
    ok = process_updates()
    return jsonify(ok=ok, linked=bool(chat_of(u["id"])), error="" if ok else LAST_ERROR[0])

@tg.route("/api/telegram/test", methods=["POST"])
def test():
    u = me_or_401()
    cid = chat_of(u["id"])
    if not cid:
        return jsonify(ok=False, error="Telegram is not connected yet."), 400
    ok = send_chat(cid, "\u2705 Test alert from Smart Health Companion. Alerts for your patients will arrive here.", force=True)
    return jsonify(ok=ok, error="" if ok else LAST_ERROR[0])

@tg.route("/api/telegram/disconnect", methods=["POST"])
def disconnect():
    u = me_or_401()
    with db() as c:
        c.execute("DELETE FROM tg_links WHERE user_id=?", (u["id"],))
    return jsonify(ok=True)

# ---------- page pieces, inserted into the website by app.py ----------
TG_NAV = ('<button data-sec="tg"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
          'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"/>'
          '<path d="M22 2l-7 20-4-9-9-4 20-7z"/></svg>Telegram alerts</button>\n')

TG_SECTION = r"""<section class="sec" id="sec-tg" style="display:none">
<div class="card">
<h3>Telegram alerts</h3>
<p>Get fall alerts and missed-medicine alerts for your patients as Telegram messages on your phone.</p>
<div id="tg-off" style="display:none"><p class="err">Telegram is not set up on this server yet. The person who runs the site must add the bot token (telegram.token).</p></div>
<div id="tg-main">
<div id="tg-unlinked">
<button class="btn" onclick="tgConnect()">Connect Telegram</button>
<div id="tg-steps" style="display:none;margin-top:14px">
<p><b>1.</b> Open this link on the phone or computer where you use Telegram:</p>
<p><a id="tg-link" href="#" target="_blank" rel="noopener"></a></p>
<p><b>2.</b> Press <b>Start</b> in Telegram. This page connects by itself within a few seconds.</p>
<p class="meta" id="tg-wait"></p>
</div>
</div>
<div id="tg-linked" style="display:none">
<p><span class="chip good">Connected</span> Your messages arrive in Telegram: <span id="tg-what"></span></p>
<button class="btn ghost" onclick="tgTest()">Send a test message</button>
<button class="btn ghost" onclick="tgDisconnect()">Disconnect</button>
</div>
<p class="err" id="tg-err"></p>
</div>
</div></section>
"""

TG_JS = r"""
TITLES.tg='Telegram alerts';
const _refreshSecTg=refreshSec;
refreshSec=function(){_refreshSecTg();if(cur==='tg')tgStatus()};
let TGTIMER=null;
async function tgStatus(){
  const r=await api('/api/telegram/status');if(!r.ok)return;
  const d=await r.json();
  const isPatient=ROLE==='patient';
  $('tg-off').style.display=d.configured?'none':'block';
  $('tg-main').style.display=d.configured?'block':'none';
  $('tg-linked').style.display=(d.linked&&!isPatient)?'block':'none';
  $('tg-unlinked').style.display=(d.linked||isPatient)?'none':'block';
  $('tg-what').textContent='fall alerts and missed-medicine alerts for your patients.';
  $('tg-err').textContent=isPatient
    ? 'Telegram alerts are sent to your caregivers only. Ask them to connect Telegram from their own account.'
    : (d.error||'');
}
async function tgConnect(){
  $('tg-err').textContent='';
  const r=await api('/api/telegram/connect',{method:'POST'});const d=await r.json();
  if(!d.ok){$('tg-err').textContent=d.error||'Could not start.';return}
  $('tg-link').href=d.link;$('tg-link').textContent=d.link;
  $('tg-steps').style.display='block';
  $('tg-wait').textContent='Waiting for you to press Start in Telegram...';
  clearInterval(TGTIMER);let n=0;
  TGTIMER=setInterval(async()=>{
    n++;
    if(n>60){clearInterval(TGTIMER);$('tg-wait').textContent='Timed out. Press Connect Telegram to try again.';return}
    const rr=await api('/api/telegram/check',{method:'POST'});if(!rr.ok)return;
    const dd=await rr.json();
    if(!dd.ok&&dd.error){$('tg-err').textContent=dd.error;clearInterval(TGTIMER);return}
    if(dd.linked){clearInterval(TGTIMER);$('tg-steps').style.display='none';toast('<b>Telegram connected</b>');tgStatus()}
  },3000);
}
async function tgTest(){
  $('tg-err').textContent='';
  const r=await api('/api/telegram/test',{method:'POST'});const d=await r.json();
  if(d.ok){toast('<b>Test message sent.</b> Check Telegram.')}else{$('tg-err').textContent=d.error||'Could not send.'}
}
async function tgDisconnect(){
  if(!confirm('Stop Telegram alerts for this account?'))return;
  await api('/api/telegram/disconnect',{method:'POST'});tgStatus();
}
"""