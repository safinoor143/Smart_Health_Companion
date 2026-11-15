import os, re, time, sqlite3, datetime
import requests
from flask import Blueprint, request, jsonify, abort
from auth import current_user

chat = Blueprint("chat", __name__)
DB = "falls.db"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"      # first choice; if Groq no longer has it, a working model is picked automatically
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
PREFERRED = ["llama-3.1-8b-instant", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "openai/gpt-oss-120b"]
SKIP = re.compile(r"whisper|guard|tts|embed|prompt|orpheus|playai|distil|safeguard|transcri|speech", re.I)
_model = [None]
LIMIT_COUNT, LIMIT_SECONDS = 20, 600     # 20 messages per user every 10 minutes
_hits = {}
LAST_ERROR = [""]

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def groq_key():
    k = os.environ.get("GROQ_API_KEY", "").strip()
    if not k and os.path.exists("groq.key"):
        with open("groq.key", encoding="utf-8-sig") as f:
            k = f.read().strip()
    return k

SYSTEM = ("You are the Smart Health Companion assistant for elderly people and their caregivers in India. "
          "Use short, simple, kind sentences (under 150 words). Answer general health questions with educational "
          "information: what a condition is, common symptoms, causes, risk factors, prevention, diet, exercise, sleep, "
          "fall prevention, and when to see a doctor. Also explain how to use the website. "
          "Do not diagnose the person you are talking to, never give medicine doses, and never tell anyone to start, "
          "stop or change a medicine; say to ask a doctor or pharmacist instead. "
          "If the symptoms sound serious or sudden, say to call 112 (ambulance 108). "
          "End health answers with one short line that this is general information and not a substitute for a doctor. "
          "The website has only these tabs: Overview, Reminders, Fall alerts, Routine, Vitals, Appointments, My device "
          "(patients), Telegram alerts (caregivers) and Health assistant. Never mention any other menu or feature. "
          "You do not know the user's name or records, so never invent them.")

EMERGENCY = re.compile(r"chest pain|can'?t breathe|cannot breathe|trouble breathing|difficulty breathing|not breathing|"
                       r"stroke|unconscious|passed out|seizure|heavy bleeding|bleeding a lot|overdose|"
                       r"suicid|kill myself|want to die|end my life|hurt myself", re.I)
EMERGENCY_REPLY = ("This may be an emergency. Please call 112 now (ambulance: 108) and tell someone near you. "
                   "I am only a helper on this website and cannot give emergency help.")
SELFHARM = re.compile(r"suicid|kill myself|want to die|end my life|hurt myself", re.I)
SELFHARM_REPLY = ("I am sorry you feel this way. Please call 112 or talk to someone you trust right now, "
                  "and tell your caregiver or doctor how you feel. You do not have to go through this alone.")
MEDICAL = re.compile(r"\b(dose|dosage|overdos\w*|how many (mg|tablets|pills|capsules)|how much (medicine|tablet|pill)|"
                     r"stop taking|skip (my |the )?(medicine|tablet|dose)|"
                     r"increase (my |the )?(medicine|dose)|what (disease|illness) do i have)\b", re.I)
MEDICAL_REPLY = ("I cannot advise on doses, diagnoses or changing medicines. Please ask your doctor or pharmacist. "
                 "I can help with your reminders, fall alerts and healthy daily habits.")

def today_hm():
    n = datetime.datetime.now()
    return n.strftime("%Y-%m-%d"), n.strftime("%H:%M")

def rule_answer(u, text):
    t = text.lower().strip()
    pid = u["id"] if u["role"] == "patient" else None
    if re.fullmatch(r"(hi|hello|hey|namaste|good (morning|afternoon|evening))[ !.]*", t):
        return "Hello! You can ask me about your reminders, fall alerts, Telegram alerts, or healthy daily habits."
    if re.search(r"what can you (do|help)|\bhelp\b", t) and len(t) < 40:
        return ("I can tell you your next reminders, your last fall alert, how to cancel a fall alert, "
                "how to link a caregiver, and give general healthy-habit tips. I cannot give medical advice.")
    if re.search(r"cancel", t) and re.search(r"fall|alert|buzz|alarm", t):
        return ("To cancel a fall alert, press the push button on your device within 15 seconds, "
                "or press 'Cancel - I am OK' in the red banner on this website. After that time the caregiver is alerted.")
    if re.search(r"invite|link", t) and re.search(r"code|caregiver|patient|link", t):
        if pid:
            with db() as c:
                r = c.execute("SELECT invite FROM users WHERE id=?", (pid,)).fetchone()
            return "Your invite code is %s. Give it to your caregiver so they can link to you." % (r["invite"] if r else "not available")
        return "Ask the patient for their 6-character invite code (shown on their account) and enter it where the site asks to link a patient."
    if "telegram" in t:
        if pid:
            return "Telegram alerts go to caregivers only. Ask your caregiver to open the Telegram alerts tab and press Connect Telegram."
        return "Open the Telegram alerts tab, press Connect Telegram, open the link on your phone and press Start. Then use 'Send a test message'."
    if re.search(r"medicine|tablet|pill|reminder|appointment|schedule", t) and re.search(r"next|when|today|upcoming|what|show|my", t):
        if not pid:
            return "Choose a patient, then open the Reminders tab to see and add their reminders."
        d, hm = today_hm()
        with db() as c:
            rows = c.execute("""SELECT kind, title, time FROM reminders
                                WHERE patient_id=? AND active=1 AND (date IS NULL OR date='' OR date=?) AND time>?
                                ORDER BY time LIMIT 3""", (pid, d, hm)).fetchall()
        if not rows:
            return "You have no more reminders today."
        return "Your next reminders: " + "; ".join("%s at %s (%s)" % (r["title"], r["time"], r["kind"]) for r in rows) + "."
    if "fall" in t and re.search(r"last|recent|history|when|any|did", t):
        with db() as c:
            if pid:
                rows = c.execute("SELECT time, status FROM events WHERE patient_id=? AND result='fall' ORDER BY id DESC LIMIT 1", (pid,)).fetchall()
                names = {pid: "You"}
            else:
                rows = c.execute("""SELECT e.time, e.status, e.patient_id FROM events e
                                    JOIN links l ON l.patient_id=e.patient_id
                                    WHERE l.caregiver_id=? AND e.result='fall' ORDER BY e.id DESC LIMIT 3""", (u["id"],)).fetchall()
                names = {r["id"]: r["name"] for r in c.execute(
                    "SELECT users.id, users.name FROM links JOIN users ON users.id=links.patient_id WHERE links.caregiver_id=?", (u["id"],)).fetchall()}
        if not rows:
            return "No falls have been recorded."
        out = []
        for r in rows:
            who = names.get(r["patient_id"], "Patient") if not pid else "You"
            out.append("%s: fall at %s (%s)" % (who, r["time"], r["status"].replace("_", " ")))
        return "Latest fall: " + "; ".join(out) + "."
    return None

def rate_ok(uid):
    now = time.time()
    h = [x for x in _hits.get(uid, []) if now - x < LIMIT_SECONDS]
    ok = len(h) < LIMIT_COUNT
    if ok:
        h.append(now)
    _hits[uid] = h
    return ok

def pick_model(key):
    """Ask Groq which models this key can use and choose a text chat model."""
    try:
        r = requests.get(GROQ_MODELS_URL, headers={"Authorization": "Bearer " + key}, timeout=(4, 10))
        ids = [m["id"] for m in r.json().get("data", []) if m.get("id")]
    except (requests.RequestException, ValueError, AttributeError, KeyError):
        return None
    for p in PREFERRED:
        if p in ids:
            return p
    for i in ids:
        if not SKIP.search(i):
            return i
    return None

def ask_groq(history, text, _retry=True):
    key = groq_key()
    if not key:
        LAST_ERROR[0] = "No Groq key: groq.key file is missing."
        return None
    msgs = [{"role": "system", "content": SYSTEM}]
    for m in history[-6:]:
        if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str):
            msgs.append({"role": m["role"], "content": m["content"][:500]})
    msgs.append({"role": "user", "content": text})
    try:
        r = requests.post(GROQ_URL, headers={"Authorization": "Bearer " + key},
                          json={"model": _model[0] or GROQ_MODEL, "messages": msgs, "max_tokens": 380, "temperature": 0.4},
                          timeout=(4, 20))
    except requests.RequestException:
        LAST_ERROR[0] = "Cannot reach api.groq.com (no internet or blocked)."
        return None
    try:
        data = r.json()
    except ValueError:
        LAST_ERROR[0] = "Groq gave an unreadable answer (HTTP %s)." % r.status_code
        return None
    if r.status_code != 200:
        msg = ((data.get("error") or {}).get("message") or "")
        if _retry and r.status_code in (400, 404) and re.search(r"model", msg, re.I):
            m = pick_model(key)
            if m and m != (_model[0] or GROQ_MODEL):
                _model[0] = m
                return ask_groq(history, text, _retry=False)
        LAST_ERROR[0] = "Groq said: %s" % ((data.get("error") or {}).get("message") or r.status_code)
        return None
    try:
        LAST_ERROR[0] = ""
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError):
        LAST_ERROR[0] = "Groq answer had an unexpected shape."
        return None

@chat.route("/api/chat/status")
def status():
    if not current_user():
        abort(401)
    return jsonify(ai=bool(groq_key()), error=LAST_ERROR[0], model=_model[0] or GROQ_MODEL)

@chat.route("/api/chat", methods=["POST"])
def talk():
    u = current_user()
    if not u:
        abort(401)
    b = request.get_json(silent=True) or {}
    text = (b.get("message") or "").strip()[:500]
    if not text:
        return jsonify(reply="Please type a question.", source="rules")
    if SELFHARM.search(text):
        return jsonify(reply=SELFHARM_REPLY, source="safety")
    if EMERGENCY.search(text):
        return jsonify(reply=EMERGENCY_REPLY, source="safety")
    if MEDICAL.search(text):
        return jsonify(reply=MEDICAL_REPLY, source="safety")
    if not rate_ok(u["id"]):
        return jsonify(reply="You have asked a lot of questions. Please wait a few minutes and try again.", source="limit")
    ans = rule_answer(u, text)
    if ans:
        return jsonify(reply=ans, source="rules")
    hist = b.get("history") if isinstance(b.get("history"), list) else []
    ai = ask_groq(hist, text)
    if ai:
        return jsonify(reply=ai, source="ai")
    return jsonify(reply=("I cannot reach the AI service right now. I can still answer questions about your reminders, "
                          "your last fall alert, cancelling an alert and linking a caregiver."),
                   source="offline", note=LAST_ERROR[0])

# ---------- page pieces, inserted into the website by app.py ----------
CHAT_NAV = ('<button data-sec="chat"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>Health assistant</button>\n')

CHAT_SECTION = r"""<section class="sec" id="sec-chat" style="display:none">
<div class="card">
<h3>Health assistant</h3>
<p class="meta" id="chat-mode"></p>
<div id="chat-log" style="height:340px;overflow:auto;border:1px solid #e2e8f0;border-radius:12px;padding:12px;background:#f8fafc;margin:10px 0"></div>
<div style="display:flex;gap:8px">
<input id="chat-in" placeholder="Ask about your reminders, falls or any general health topic" maxlength="500" style="flex:1;padding:11px 13px;border:1px solid #cbd5e1;border-radius:10px;font-size:14px">
<button class="btn" id="chat-send" onclick="chatSend()">Send</button>
</div>
<p class="meta" style="margin-top:10px">General health information only. It cannot diagnose you or give doses. In an emergency call 112.</p>
</div></section>
"""

CHAT_JS = r"""
TITLES.chat='Health assistant';
let CHATHIST=[];
function chatAdd(who,text,note){
  const log=$('chat-log');const d=document.createElement('div');
  d.style.cssText='margin:8px 0;display:flex;'+(who==='me'?'justify-content:flex-end':'');
  const b=document.createElement('div');
  b.style.cssText='max-width:82%;padding:9px 13px;border-radius:14px;font-size:14px;line-height:1.45;white-space:pre-wrap;'
    +(who==='me'?'background:#2563eb;color:#fff':'background:#fff;border:1px solid #e2e8f0;color:#0f172a');
  b.textContent=text;d.appendChild(b);log.appendChild(d);
  if(note){const n=document.createElement('div');n.className='meta';n.style.cssText='margin:-4px 0 6px 4px';n.textContent=note;log.appendChild(n)}
  log.scrollTop=log.scrollHeight;
}
async function chatInit(){
  if(!$('chat-log').dataset.ready){
    $('chat-log').dataset.ready='1';
    chatAdd('bot','Hello! Ask me about your reminders, your last fall alert, or any general health topic.');
  }
  const r=await api('/api/chat/status');if(!r.ok)return;
  const d=await r.json();
  $('chat-mode').textContent=d.ai?'AI answers are on. Questions about your reminders and falls are answered from your own records.'
                                 :'AI answers are off (no groq.key file). Questions about reminders and falls still work.';
}
async function chatSend(){
  const inp=$('chat-in');const text=inp.value.trim();if(!text)return;
  inp.value='';chatAdd('me',text);$('chat-send').disabled=true;
  try{
    const r=await api('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message:text,history:CHATHIST})});
    const d=await r.json();
    chatAdd('bot',d.reply||'Sorry, something went wrong.',d.source==='ai'?'AI answer':(d.note||''));
    CHATHIST.push({role:'user',content:text},{role:'assistant',content:d.reply||''});
    CHATHIST=CHATHIST.slice(-8);
  }catch(e){chatAdd('bot','Sorry, I could not reach the website.')}
  $('chat-send').disabled=false;inp.focus();
}
document.addEventListener('keydown',e=>{if(e.key==='Enter'&&document.activeElement&&document.activeElement.id==='chat-in')chatSend()});
const _refreshSecChat=refreshSec;
refreshSec=function(){_refreshSecChat();if(cur==='chat')chatInit()};
"""