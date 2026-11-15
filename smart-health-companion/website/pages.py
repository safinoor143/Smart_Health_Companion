from flask import Blueprint, redirect

pages = Blueprint("pages", __name__)

CSS = r"""<style>
:root{--navy:#0b1f3a;--navy2:#12305a;--teal:#14b8a6;--blue:#2563eb;--bg:#f1f5f9;--text:#0f172a;--muted:#64748b;--line:#e2e8f0;--red:#dc2626;--amber:#d97706;--green:#16a34a}
*{box-sizing:border-box}
body{margin:0;font-family:"Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif;color:var(--text)}
body.authbody{background:#0b1f3a}
body.patient,body.caregiver{background:var(--bg)}
i[data-ic]{display:inline-flex}
svg{flex:none}

/* ===== login / sign-up ===== */
#auth{display:grid;grid-template-columns:1.15fr .85fr;min-height:100vh}
#auth .hero{position:relative;overflow:hidden;color:#fff;padding:44px 56px;display:flex;flex-direction:column;
 background:radial-gradient(1100px 600px at 0% -10%,#1d4ed8 0,transparent 55%),radial-gradient(900px 520px at 100% 105%,#0d9488 0,transparent 55%),linear-gradient(160deg,#0b1f3a,#0f2f5c)}
.blob{position:absolute;border-radius:50%;filter:blur(60px);opacity:.35;animation:drift 12s ease-in-out infinite}
.b1{width:260px;height:260px;background:#22d3ee;top:8%;right:6%}
.b2{width:220px;height:220px;background:#6366f1;bottom:10%;left:-4%;animation-delay:3s}
@keyframes drift{0%,100%{transform:translate(0,0)}50%{transform:translate(24px,-30px)}}
.hbrand{display:flex;align-items:center;gap:12px;font-weight:700;font-size:18px;position:relative}
.hlogo{width:44px;height:44px;border-radius:13px;background:linear-gradient(135deg,#2dd4bf,#3b82f6);display:grid;place-items:center}
.hbrand small{display:block;font-weight:400;font-size:12px;color:#a5b4cf}
#auth .hero h1{font-size:42px;line-height:1.1;margin:34px 0 12px;position:relative;max-width:520px;color:#fff}
#auth .hero p.lead{color:#c3d0e6;font-size:16px;max-width:500px;line-height:1.55;margin:0;position:relative}
.art{width:100%;max-width:560px;margin:10px auto 0;position:relative;display:block}
.art text{font-family:"Segoe UI",system-ui,Arial,sans-serif;fill:#fff}
.ring{fill:none;stroke:#5eead4;stroke-width:2;opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 3.6s ease-out infinite}
.d2{animation-delay:1.2s}.d3{animation-delay:2.4s}
@keyframes ring{0%{transform:scale(.8);opacity:.7}100%{transform:scale(2.7);opacity:0}}
.bob{animation:bob 4s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
.beat{transform-box:fill-box;transform-origin:center;animation:beat 1.3s ease-in-out infinite}
@keyframes beat{0%,100%{transform:scale(1)}15%{transform:scale(1.16)}30%{transform:scale(1)}45%{transform:scale(1.1)}}
.ecg{fill:none;stroke:#5eead4;stroke-width:3;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:700;stroke-dashoffset:700;animation:ecg 3.2s linear infinite}
@keyframes ecg{0%{stroke-dashoffset:700}70%{stroke-dashoffset:0}100%{stroke-dashoffset:0;opacity:0}}
.float{animation:flt 5s ease-in-out infinite}
.f2{animation-delay:1.3s}.f3{animation-delay:2.4s}
@keyframes flt{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
.pills{display:flex;gap:10px;flex-wrap:wrap;margin-top:auto;padding-top:18px;position:relative}
.pills span{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);padding:8px 14px;border-radius:999px;font-size:13px}
#auth .panel{display:flex;align-items:center;justify-content:center;background:#f8fafc;padding:32px}
#auth .formcard{width:100%;max-width:400px}
#auth .formcard h2{margin:0 0 4px;font-size:28px}
#auth .formcard .lead{color:#64748b;margin:0 0 14px}
.atabs{display:flex;background:#e2e8f0;border-radius:12px;padding:4px;margin-bottom:22px}
.atabs button{flex:1;border:0;background:transparent;padding:10px;border-radius:9px;font-weight:600;color:#475569;cursor:pointer;font-size:14px}
.atabs button.sel{background:#fff;color:#1d4ed8;box-shadow:0 1px 4px rgba(0,0,0,.12)}
#auth label{display:block;font-size:13px;font-weight:600;color:#334155;margin:14px 0 6px}
#auth input[type=text],#auth input[type=email],#auth input[type=password]{width:100%;padding:13px 14px;border:1px solid #cbd5e1;border-radius:12px;font-size:15px;background:#fff;outline:none}
#auth input:focus{border-color:#2563eb;box-shadow:0 0 0 4px rgba(37,99,235,.12)}
#auth button.primary{width:100%;margin-top:20px;padding:14px;border:0;border-radius:12px;font-size:16px;font-weight:600;color:#fff;cursor:pointer;background:linear-gradient(135deg,#2563eb,#0d9488);box-shadow:0 8px 20px rgba(37,99,235,.28)}
#auth button.primary:hover{filter:brightness(1.07)}
.aerr{color:#b91c1c;background:#fee2e2;border-radius:10px;padding:10px 12px;margin:0 0 4px;font-size:14px}
.aerr:empty{display:none}
.roles{display:grid;grid-template-columns:1fr 1fr;gap:10px}
#auth label.role{margin:0}
.role input{display:none}
.role span{display:block;border:2px solid #e2e8f0;border-radius:12px;padding:12px;text-align:center;cursor:pointer;font-weight:600;background:#fff;color:#334155}
.role input:checked+span{border-color:#2563eb;background:#eff6ff;color:#1d4ed8}

/* ===== dashboard ===== */
.app{display:grid;grid-template-columns:256px 1fr;min-height:100vh}
.side{background:linear-gradient(185deg,var(--navy),var(--navy2));color:#cbd5e1;padding:20px 14px;position:sticky;top:0;height:100vh;display:flex;flex-direction:column}
.brand{display:flex;align-items:center;gap:11px;color:#fff;font-weight:700;font-size:16px;padding:4px 8px 22px;line-height:1.2}
.brand small{display:block;font-weight:400;font-size:12px;color:#94a3b8}
.logo{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,var(--teal),var(--blue));display:grid;place-items:center;color:#fff}
.nav{display:flex;flex-direction:column;gap:4px}
.nav button{display:flex;align-items:center;gap:12px;width:100%;padding:11px 12px;border:0;background:transparent;color:#cbd5e1;border-radius:10px;font-size:14.5px;cursor:pointer;text-align:left}
.nav button:hover{background:rgba(255,255,255,.07)}
.nav button.sel{background:rgba(255,255,255,.14);color:#fff;font-weight:600}
.navdot{display:none;width:9px;height:9px;border-radius:50%;background:#f87171;margin-left:auto;animation:pulse 1.2s infinite}
.spacer{flex:1}
.userchip{display:flex;align-items:center;gap:10px;padding:12px;background:rgba(255,255,255,.08);border-radius:12px;color:#fff}
.userchip small{display:block;color:#94a3b8;font-size:12px}
.userchip a{margin-left:auto;color:#cbd5e1;display:inline-flex}
.av{width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg,var(--teal),var(--blue));display:grid;place-items:center;font-weight:700;color:#fff;flex:none}
.av.big{width:44px;height:44px;font-size:18px}
.main{padding:24px 30px;min-width:0}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;gap:12px;flex-wrap:wrap}
.main h1{margin:0;font-size:26px}
.sub{color:var(--muted);font-size:14px;margin-top:2px}
.topright{display:flex;align-items:center;gap:10px}
.status{padding:7px 14px;border-radius:999px;font-size:13px;font-weight:600;background:#dcfce7;color:#166534}
.status.bad{background:#fee2e2;color:#991b1b;animation:pulse 1.2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.45}}
@keyframes flash{0%,100%{box-shadow:0 0 0 0 rgba(220,38,38,.5)}50%{box-shadow:0 0 0 10px rgba(220,38,38,0)}}
.banner{display:none;align-items:center;gap:14px;padding:16px 20px;border-radius:14px;margin-bottom:16px;font-weight:600;font-size:17px}
.banner.pending{display:flex;background:linear-gradient(90deg,#fee2e2,#fecaca);color:#991b1b;border:1px solid #fca5a5;animation:flash 1.3s infinite}
.banner.sent{display:flex;background:linear-gradient(90deg,#991b1b,#b91c1c);color:#fff}
.card{background:#fff;border-radius:16px;padding:18px 20px;box-shadow:0 1px 3px rgba(15,23,42,.06),0 8px 24px rgba(15,23,42,.04);margin-bottom:16px}
.card h3{margin:0 0 12px;font-size:16px}
.card p{color:var(--muted);font-size:14px;line-height:1.5}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:2px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:2px}
.grid2{display:grid;grid-template-columns:1.2fr 1fr;gap:16px}
.grid2e{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.stat{display:flex;gap:12px;align-items:center;margin-bottom:14px}
.stat .lbl{color:var(--muted);font-size:13px}
.stat b{font-size:20px;display:block;margin:1px 0}
.stat small{color:var(--muted);font-size:12.5px}
.ico{width:46px;height:46px;border-radius:13px;display:grid;place-items:center;color:#fff;flex:none}
.g1{background:linear-gradient(135deg,#3b82f6,#1d4ed8)}.g2{background:linear-gradient(135deg,#34d399,#059669)}
.g3{background:linear-gradient(135deg,#a78bfa,#6d28d9)}.g4{background:linear-gradient(135deg,#2dd4bf,#0d9488)}
.gred{background:linear-gradient(135deg,#f87171,#b91c1c)}
.bar{height:7px;background:#e2e8f0;border-radius:99px;overflow:hidden;margin-top:6px;width:130px}
.bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#34d399,#059669);transition:width .5s}
.welcome{display:flex;justify-content:space-between;align-items:center;color:#fff;border-radius:18px;padding:22px 26px;margin-bottom:16px;background:linear-gradient(120deg,#0b1f3a,#1e4fa3 60%,#0d9488)}
.welcome h2{margin:0 0 4px;font-size:24px}
.welcome p{margin:0;color:#cfe0f5;font-size:14.5px}
.item{display:flex;align-items:center;gap:12px;padding:11px 2px;border-bottom:1px solid var(--line)}
.item:last-child{border-bottom:0}
.time{font-weight:700;width:52px;color:var(--navy);font-size:14px}
.grow{flex:1;min-width:0}
.title{font-weight:600;font-size:14.5px}
.meta{color:var(--muted);font-size:12.5px}
.kic{display:grid;place-items:center;width:38px;height:38px;border-radius:11px;flex:none;background:#e2e8f0;color:#475569}
.k-medicine{background:#dbeafe;color:#1d4ed8}.k-hydration{background:#cffafe;color:#0e7490}
.k-meal{background:#ffedd5;color:#c2410c}.k-activity{background:#dcfce7;color:#15803d}
.k-vitals{background:#ede9fe;color:#6d28d9}.k-wake-up{background:#fef9c3;color:#a16207}
.k-bedtime{background:#e0e7ff;color:#4338ca}.k-appointment{background:#fce7f3;color:#be185d}
.k-fall{background:#fee2e2;color:#b91c1c}.k-med2{background:#fef3c7;color:#b45309}
.chip{display:inline-block;padding:4px 11px;border-radius:999px;font-size:12px;font-weight:600;white-space:nowrap}
.chip.upcoming{background:#e2e8f0;color:#475569}.chip.due{background:#fee2e2;color:#b91c1c}
.chip.taken{background:#dcfce7;color:#166534}.chip.missed{background:#fef3c7;color:#92400e}
.chip.late{background:#fef9c3;color:#854d0e}.chip.skipped{background:#f1f5f9;color:#94a3b8}
.chip.a-pending{background:#fee2e2;color:#b91c1c}.chip.a-alert_sent{background:#7f1d1d;color:#fff}
.chip.a-cancelled{background:#e2e8f0;color:#475569}
.chip.pa-ok{background:#dcfce7;color:#166534}.chip.pa-missed{background:#fef3c7;color:#92400e}
.chip.pa-fall_pending{background:#fee2e2;color:#b91c1c}.chip.pa-fall_sent{background:#7f1d1d;color:#fff}
.chip.bad{background:#fee2e2;color:#b91c1c}.chip.good{background:#dcfce7;color:#166534}
.duecard{display:flex;align-items:center;gap:14px;background:#fff;border-left:6px solid var(--red);border-radius:14px;padding:14px 18px;margin-bottom:12px;box-shadow:0 6px 20px rgba(220,38,38,.15);animation:flash 1.5s infinite}
.dtitle{font-size:18px;font-weight:700}
.btn{background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;border:0;padding:10px 18px;border-radius:10px;font-weight:600;cursor:pointer;font-size:14px;display:inline-flex;align-items:center;gap:6px}
.btn:hover{filter:brightness(1.08)}
.btn.ghost{background:#eef2f7;color:var(--navy)}
button.icon{border:0;background:transparent;color:#94a3b8;cursor:pointer;padding:6px;border-radius:8px;display:inline-flex}
button.icon:hover{background:#fee2e2;color:#b91c1c}
.main input,.main select{padding:10px 12px;border:1px solid #cbd5e1;border-radius:10px;font-size:14px;background:#fff;outline:none;font-family:inherit}
.main input:focus,.main select:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.12)}
.form{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.err{color:#b91c1c;font-size:13px}
.empty{color:var(--muted);text-align:center;padding:22px 8px;font-size:14px}
.sparks{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
.spark{border:1px solid var(--line);border-radius:12px;padding:10px 12px}
.spark.bad{border-color:#fecaca;background:#fef2f2}
.spark .sn{font-size:12px;color:var(--muted)}
.spark b{font-size:20px;display:block}
.spark svg{width:100%;height:34px;display:block;margin:4px 0}
.ringwrap{display:flex;align-items:center;gap:22px;flex-wrap:wrap}
.legend div{display:flex;align-items:center;gap:8px;font-size:14px;margin:5px 0}
.legend i{width:10px;height:10px;border-radius:50%;display:inline-block}
.legend.row{display:flex;gap:16px;flex-wrap:wrap;margin-top:6px}
.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
.pcard{display:flex;align-items:center;gap:12px;padding:14px;border:2px solid var(--line);border-radius:14px;cursor:pointer;background:#fff}
.pcard:hover{border-color:#93c5fd}
.pcard.sel{border-color:var(--blue);background:#eff6ff}
.pcard.s-fall_pending,.pcard.s-fall_sent{border-color:#fca5a5;background:#fff5f5}
.flow{display:flex;align-items:stretch;gap:8px;flex-wrap:wrap}
.step{flex:1;min-width:130px;background:#f8fafc;border:1px solid var(--line);border-radius:14px;padding:14px;text-align:center}
.step b{display:block;margin:8px 0 4px;font-size:14px}
.step small{color:var(--muted);font-size:12px}
.step .kic{margin:0 auto}
.arrow{align-self:center;color:#94a3b8;font-size:20px}
.conds{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;margin:8px 0 14px}
.cond-card input{display:none}
.cond-card span{display:block;border:2px solid var(--line);border-radius:12px;padding:14px;font-weight:600;cursor:pointer;background:#fff}
.cond-card input:checked+span{border-color:var(--blue);background:#eff6ff;color:#1d4ed8}
.tokenbox{background:#0b1f3a;color:#5eead4;font-family:Consolas,monospace;padding:14px;border-radius:12px;word-break:break-all;font-size:15px;margin:10px 0}
.bigcode{font-size:34px;letter-spacing:6px;font-weight:800;color:var(--navy);margin:8px 0}
#toasts{position:fixed;top:16px;right:16px;z-index:50;display:flex;flex-direction:column;gap:10px;max-width:340px}
.toast{background:#0b1f3a;color:#fff;padding:14px 16px;border-radius:12px;box-shadow:0 12px 30px rgba(0,0,0,.25);font-size:14px;border-left:5px solid #38bdf8;transition:opacity .4s}
.toast.bad{border-left-color:#f87171;background:#7f1d1d}
.toast.warn{border-left-color:#fbbf24}
body.caregiver .only-patient{display:none!important}
body.patient .only-caregiver{display:none!important}
#jserr{display:none;position:fixed;bottom:10px;left:10px;right:10px;background:#7f1d1d;color:#fff;padding:10px 14px;border-radius:8px;z-index:99;font-size:13px}
@media(max-width:1000px){.grid4{grid-template-columns:1fr 1fr}.grid2,.grid2e{grid-template-columns:1fr}.grid3{grid-template-columns:1fr}}
@media(max-width:900px){
 #auth{grid-template-columns:1fr}#auth .hero{padding:28px 24px}#auth .hero h1{font-size:30px;margin-top:20px}.art{max-width:380px}
 .app{grid-template-columns:1fr}.side{position:static;height:auto;flex-direction:row;align-items:center;padding:10px;overflow-x:auto}.brand{padding:0 12px 0 4px}.brand small,.userchip,.spacer{display:none}.nav{flex-direction:row}.nav button{white-space:nowrap;width:auto}.main{padding:16px}.grid4{grid-template-columns:1fr}}
</style>"""

AUTH_HTML = r"""<div id="auth">
<div class="hero"><span class="blob b1"></span><span class="blob b2"></span>
<div class="hbrand"><span class="hlogo"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="7 12 10 12 11.5 15 13.5 9 15 12 17 12"/></svg></span>
<div>Smart Health Companion<small>Elderly fall detection &amp; care reminders</small></div></div>
<h1>Care that never looks away.</h1>
<p class="lead">A smart wearable and a caring dashboard that detect falls, remind medicines and keep caregivers informed, in real time.</p>
<svg class="art" viewBox="0 0 560 400" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Wearable fall detection and care reminders illustration">
<defs>
<linearGradient id="gs" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2dd4bf"/><stop offset="1" stop-color="#3b82f6"/></linearGradient>
<linearGradient id="gc" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity=".2"/><stop offset="1" stop-color="#ffffff" stop-opacity=".07"/></linearGradient>
</defs>
<g transform="translate(280 168)">
<circle class="ring" r="70"/><circle class="ring d2" r="70"/><circle class="ring d3" r="70"/>
<g class="bob">
<path d="M0 -88 L70 -60 V10 C70 60 34 88 0 104 C-34 88 -70 60 -70 10 V-60 Z" fill="url(#gs)"/>
<path class="beat" d="M0 46 C-38 16 -38 -26 -16 -26 C-7 -26 0 -19 0 -11 C0 -19 7 -26 16 -26 C38 -26 38 16 0 46 Z" fill="#ffffff"/>
</g></g>
<path class="ecg" d="M30 352 H150 L172 320 L196 378 L224 298 L250 352 H530"/>
<g class="float">
<rect x="14" y="36" width="200" height="60" rx="14" fill="url(#gc)" stroke="#ffffff" stroke-opacity=".28"/>
<circle cx="42" cy="66" r="9" fill="#4ade80"/>
<text x="62" y="62" font-size="14" font-weight="700">Medicine reminder</text>
<text x="62" y="82" font-size="12" opacity=".78">8:00 AM  -  taken</text>
</g>
<g class="float f2">
<rect x="346" y="118" width="200" height="60" rx="14" fill="url(#gc)" stroke="#ffffff" stroke-opacity=".28"/>
<circle cx="374" cy="148" r="9" fill="#f87171"/>
<text x="394" y="144" font-size="14" font-weight="700">Fall detected</text>
<text x="394" y="164" font-size="12" opacity=".78">Caregiver alerted</text>
</g>
<g class="float f3">
<rect x="22" y="236" width="180" height="56" rx="14" fill="url(#gc)" stroke="#ffffff" stroke-opacity=".28"/>
<circle cx="50" cy="264" r="9" fill="#5eead4"/>
<text x="70" y="260" font-size="14" font-weight="700">Pulse 72 bpm</text>
<text x="70" y="279" font-size="12" opacity=".78">All vitals normal</text>
</g>
</svg>
<div class="pills"><span>50 Hz motion sensing</span><span>ML fall detection</span><span>Instant caregiver alerts</span></div>
</div>
<div class="panel"><div class="formcard">
<div class="atabs"><button id="tab-login" class="sel" onclick="authTab('login')">Log in</button><button id="tab-signup" onclick="authTab('signup')">Sign up</button></div>
<form id="f-login" onsubmit="doLogin(event)">
<h2>Welcome back</h2><p class="lead">Log in to your care dashboard.</p>
<p class="aerr" id="lerr"></p>
<label>Email</label><input id="l_email" type="email" placeholder="you@example.com" required>
<label>Password</label><input id="l_pw" type="password" placeholder="Your password" required>
<button class="primary">Log in</button>
</form>
<form id="f-signup" onsubmit="doSignup(event)" style="display:none">
<h2>Create your account</h2><p class="lead">Join as a patient or as a caregiver.</p>
<p class="aerr" id="serr"></p>
<label>Full name</label><input id="s_name" type="text" placeholder="Your full name" required>
<label>Email</label><input id="s_email" type="email" placeholder="you@example.com" required>
<label>Password</label><input id="s_pw" type="password" placeholder="At least 6 characters" required>
<label>I am a</label>
<div class="roles"><label class="role"><input type="radio" name="s_role" value="patient" checked><span>Patient</span></label>
<label class="role"><input type="radio" name="s_role" value="caregiver"><span>Caregiver</span></label></div>
<button class="primary">Create account</button>
</form>
</div></div>
</div>"""

DASH_HTML = r"""<div id="dash" style="display:none">
<div id="toasts"></div>
<span id="uname" hidden></span>
<div class="app">
<aside class="side">
<div class="brand"><span class="logo"><i data-ic="shield" data-s="22"></i></span><div>Health Companion<small>Care &amp; safety</small></div></div>
<nav class="nav" id="nav">
<button class="sel" data-sec="overview"><i data-ic="home"></i>Overview</button>
<button data-sec="reminders"><i data-ic="bell"></i>Reminders</button>
<button data-sec="falls"><i data-ic="alert"></i>Fall alerts<i class="navdot" id="navdot"></i></button>
<button data-sec="routine"><i data-ic="list"></i>Routine</button>
<button data-sec="vitals"><i data-ic="activity"></i>Vitals</button>
<button data-sec="appts"><i data-ic="calendar"></i>Appointments</button>
<button data-sec="device" class="only-patient"><i data-ic="watch"></i>My device</button>
</nav>
<div class="spacer"></div>
<div class="userchip"><span class="av" id="avatar"></span><div><b id="uname2"></b><small id="rolelbl"></small></div><a href="#" onclick="logout();return false" title="Log out"><i data-ic="logout"></i></a></div>
</aside>
<main class="main">
<div class="topbar">
<div><h1 id="pagetitle">Overview</h1><div class="sub"><span id="clock"></span><span id="viewing"></span></div></div>
<div class="topright"><select id="psel" class="only-caregiver" onchange="selectPatient(+this.value)"></select>
<span class="status" id="status">Monitoring</span></div>
</div>
<div id="fallbanner" class="banner"></div>
<div id="due"></div>

<section class="sec" id="sec-overview">
<div class="welcome"><div><h2 id="greet"></h2><p id="greetsub"></p></div><i data-ic="shield" data-s="54"></i></div>
<div class="card only-caregiver"><h3>My patients</h3><div class="pgrid" id="plist"></div>
<div class="form" style="margin-top:14px"><input id="code" placeholder="Patient invite code"><button class="btn" onclick="link()">Link patient</button><span id="lmsg" class="err"></span></div></div>
<div class="grid4">
<div class="card stat"><span class="ico g1"><i data-ic="clock" data-s="22"></i></span><div><div class="lbl">Next reminder</div><b id="st-next-v">-</b><small id="st-next-s"></small></div></div>
<div class="card stat"><span class="ico g2"><i data-ic="check" data-s="22"></i></span><div><div class="lbl">Today's adherence</div><b id="st-adh-v">-</b><div class="bar"><i id="st-adh-bar"></i></div></div></div>
<div class="card stat"><span class="ico g3"><i data-ic="activity" data-s="22"></i></span><div><div class="lbl">Latest vitals</div><b id="st-vit-v">-</b><small id="st-vit-s"></small></div></div>
<div class="card stat"><span class="ico g4" id="st-safe-ico"><i data-ic="shield" data-s="22"></i></span><div><div class="lbl">Safety status</div><b id="st-safe-v">-</b><small id="st-safe-s"></small></div></div>
</div>
<div class="grid2e" style="margin-top:14px">
<div class="card"><h3>Vitals at a glance</h3><div class="sparks" id="spark-grid"></div></div>
<div class="card"><h3>Today's routine</h3><div class="ringwrap"><svg id="adh-ring" viewBox="0 0 120 120" width="150" height="150" role="img" aria-label="Routine progress ring"></svg><div class="legend" id="ring-legend"></div></div></div>
</div>
<div class="card"><h3>Latest movement capture</h3><p id="live-sub" style="margin:0 0 8px"></p><canvas id="livechart" width="900" height="230" style="width:100%"></canvas></div>
<div class="grid2">
<div class="card"><h3>Alert center</h3><div id="center"></div></div>
<div class="card"><h3>Today's schedule</h3><div id="sched"></div></div>
</div>
</section>

<section class="sec" id="sec-reminders" style="display:none">
<div class="card"><h3>Today's reminders</h3><div id="rlist"></div></div>
<div class="card"><h3>Add a reminder</h3>
<div class="form"><select id="f_kind"><option>medicine</option><option>hydration</option><option>meal</option><option>activity</option><option>vitals</option><option>wake-up</option><option>bedtime</option><option>appointment</option></select>
<input id="f_title" placeholder="e.g. Metformin 500mg"><input id="f_time" type="time"><input id="f_date" type="date" title="Leave empty for daily">
<button class="btn" onclick="add()">Add</button></div>
<p>Leave the date empty for a daily reminder. Only missed medicine reminders alert the caregiver.</p></div>
</section>

<section class="sec" id="sec-falls" style="display:none">
<div class="grid3">
<div class="card stat"><span class="ico gred"><i data-ic="alert" data-s="22"></i></span><div><div class="lbl">Recent falls</div><b id="f-count">0</b></div></div>
<div class="card stat"><span class="ico g1"><i data-ic="bell" data-s="22"></i></span><div><div class="lbl">Caregiver alerted</div><b id="f-sent">0</b></div></div>
<div class="card stat"><span class="ico g2"><i data-ic="check" data-s="22"></i></span><div><div class="lbl">Cancelled by user</div><b id="f-canc">0</b></div></div>
</div>
<div class="grid2e">
<div class="card"><h3>Falls per day (last 7 days)</h3><canvas id="fchart-day" width="520" height="230" style="width:100%"></canvas></div>
<div class="card"><h3>Confidence of each fall</h3><canvas id="fchart-conf" width="520" height="230" style="width:100%"></canvas>
<div class="legend row"><div><i style="background:#dc2626"></i>Alert sent</div><div><i style="background:#16a34a"></i>Cancelled</div><div><i style="background:#d97706"></i>Waiting</div></div></div>
</div>
<div class="card"><h3>Fall events</h3><div id="fall-list"></div></div>
<div class="card"><h3>How fall detection works</h3><div class="flow">
<div class="step"><span class="kic k-vitals"><i data-ic="watch"></i></span><b>Wearable sensor</b><small>ESP32 + MPU6050 at 50 Hz</small></div><span class="arrow">&rarr;</span>
<div class="step"><span class="kic k-med2"><i data-ic="alert"></i></span><b>Impact trigger</b><small>Threshold on the device</small></div><span class="arrow">&rarr;</span>
<div class="step"><span class="kic k-medicine"><i data-ic="activity"></i></span><b>ML classifier</b><small>Random Forest on the window</small></div><span class="arrow">&rarr;</span>
<div class="step"><span class="kic k-activity"><i data-ic="clock"></i></span><b>15 s to cancel</b><small>Press the button if fine</small></div><span class="arrow">&rarr;</span>
<div class="step"><span class="kic k-fall"><i data-ic="bell"></i></span><b>Caregiver alert</b><small>Shown on the dashboard</small></div>
</div></div>
</section>

<section class="sec" id="sec-routine" style="display:none">
<div class="card"><h3>Build a daily routine</h3>
<p>Tick the health conditions that apply. A routine of wake-up, hydration, meals, activity, vitals checks and bedtime is added to the reminders. You can remove any item later.</p>
<div class="conds">
<label class="cond-card"><input type="checkbox" class="cond" value="diabetes"><span>Diabetes</span></label>
<label class="cond-card"><input type="checkbox" class="cond" value="hypertension"><span>High blood pressure</span></label>
<label class="cond-card"><input type="checkbox" class="cond" value="heart"><span>Heart condition</span></label>
<label class="cond-card"><input type="checkbox" class="cond" value="arthritis"><span>Arthritis / joint pain</span></label>
<label class="cond-card"><input type="checkbox" class="cond" value="fall_risk"><span>Fall risk / balance</span></label>
</div>
<button class="btn" onclick="applyRoutine()">Create routine</button> <span id="rmsg" class="meta"></span>
<p>These are general wellness suggestions, not medical advice. Add medicines yourself in Reminders and follow your doctor's instructions.</p></div>
</section>

<section class="sec" id="sec-vitals" style="display:none">
<div class="grid2e">
<div class="card"><h3>Log a reading</h3>
<div class="form"><select id="v_kind" onchange="kindChange();loadVitals()">
<option value="pulse">Pulse (bpm)</option><option value="spo2">SpO2 (%)</option>
<option value="bp">Blood pressure (top / bottom)</option><option value="sugar">Blood sugar (mg/dL)</option>
<option value="temp">Temperature (C)</option></select>
<input id="v_val" type="number" step="any" placeholder="value" style="width:110px">
<input id="v_val2" type="number" step="any" placeholder="bottom" style="width:110px;display:none">
<button class="btn" onclick="addVital()">Save</button></div>
<p id="vmsg"></p></div>
<div class="card"><h3>Trend</h3><canvas id="vchart" width="760" height="200" style="width:100%"></canvas></div>
</div>
<div class="card"><h3>Recent readings</h3><div id="vlist"></div></div>
</section>

<section class="sec" id="sec-appts" style="display:none">
<div class="grid2e">
<div class="card"><h3>Upcoming appointments</h3><div id="alist"></div></div>
<div class="card"><h3>Book an appointment</h3>
<div class="form"><input id="a_title" placeholder="Doctor or reason"><input id="a_date" type="date"><input id="a_time" type="time">
<button class="btn" onclick="addAppt()">Book</button></div>
<p>You get a reminder at the appointment time.</p></div>
</div>
</section>

<section class="sec only-patient" id="sec-device" style="display:none">
<div class="grid2e">
<div class="card"><h3>Wearable device token</h3>
<p>Paste this into the ESP32 code (DEVICE_TOKEN) so falls are saved under your name. Keep it private.</p>
<div class="tokenbox" id="token">-</div>
<button class="btn ghost" onclick="copyText('token',this)"><i data-ic="copy" data-s="16"></i> Copy token</button></div>
<div class="card"><h3>Caregiver invite code</h3>
<p>Give this code to your caregiver so they can link to your account.</p>
<div class="bigcode" id="invite">-</div>
<button class="btn ghost" onclick="copyText('invite',this)"><i data-ic="copy" data-s="16"></i> Copy code</button></div>
</div>
<div class="card"><h3>Linked caregivers</h3><div id="cgs"></div></div>
</section>
</main></div>
</div>"""

JS = r"""
let ROLE='', MYID=0;
const $=id=>document.getElementById(id);
const J={'Content-Type':'application/json'};
function showErr(m){const b=$('jserr');b.style.display='block';b.textContent='Page error: '+m}
window.addEventListener('error',e=>showErr(e.message));
window.addEventListener('unhandledrejection',e=>showErr(String(e.reason)));
const api=async(u,o)=>{const r=await fetch(u,o);if(r.status===401&&ROLE){ROLE='';showAuth()}return r};

const IC={
home:'<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
bell:'<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
alert:'<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
list:'<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',
activity:'<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
calendar:'<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
watch:'<circle cx="12" cy="12" r="7"/><polyline points="12 9 12 12 13.5 13.5"/><path d="M16.51 17.35l-.35 3.83a2 2 0 0 1-2 1.82H9.83a2 2 0 0 1-2-1.82l-.35-3.83m.01-10.7l.35-3.83A2 2 0 0 1 9.83 1h4.35a2 2 0 0 1 2 1.82l.35 3.83"/>',
clock:'<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
check:'<polyline points="20 6 9 17 4 12"/>',
shield:'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
logout:'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>',
copy:'<rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
pill:'<path d="M10.5 20.5L3.5 13.5a4.95 4.95 0 0 1 7-7l7 7a4.95 4.95 0 0 1-7 7z"/><line x1="8.5" y1="8.5" x2="15.5" y2="15.5"/>',
trash:'<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>',
droplet:'<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>',
coffee:'<path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/>',
sun:'<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>',
moon:'<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'
};
const KIC={medicine:'pill',hydration:'droplet',meal:'coffee',activity:'activity',vitals:'activity','wake-up':'sun',bedtime:'moon',appointment:'calendar'};
function icon(n,s){s=s||20;return '<svg viewBox="0 0 24 24" width="'+s+'" height="'+s+'" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'+(IC[n]||'')+'</svg>'}
document.querySelectorAll('[data-ic]').forEach(e=>{e.innerHTML=icon(e.dataset.ic,+e.dataset.s||20)});
function esc(s){const d=document.createElement('div');d.textContent=String(s==null?'':s);return d.innerHTML}
function empty(m){return '<div class="empty">'+m+'</div>'}

const STAT={upcoming:'Upcoming',due:'Due now',taken:'Taken',missed:'Missed',late:'Taken late',skipped:'Earlier'};
const ASTAT={pending:'Waiting for cancel',alert_sent:'Caregiver alerted',cancelled:'Cancelled by user'};
const PLABEL={ok:'All good',fall_pending:'Possible fall',fall_sent:'FALL ALERT',missed:'Missed medicine'};
const VNAME={pulse:'Pulse',spo2:'SpO2',bp:'Blood pressure',sugar:'Blood sugar',temp:'Temperature'};
const TITLES={overview:'Overview',reminders:'Reminders',falls:'Fall alerts',routine:'Daily routine',vitals:'Vitals',appts:'Appointments',device:'My device'};

let P=0, CANACK=false, TODAY=[], ALERTS=[], VIT=[], PATS=[], CENTER=[], SAFE='ok', cur='overview', lastIds='';
let ctx=null, sound=false, spoken={}, notified={}, seenFall={}, firstFall=true, lastAlert={}, firstP=true;
try{ctx=new (window.AudioContext||window.webkitAudioContext)();}catch(e){}
if(ctx&&ctx.state==='running')sound=true;
function unlock(){
  if(ctx&&ctx.state!=='running'){ctx.resume().then(()=>{if(ctx.state==='running')sound=true})}
  else if(ctx){sound=true}
  if('Notification' in window&&Notification.permission==='default')Notification.requestPermission();
}
['click','keydown','touchstart'].forEach(ev=>document.addEventListener(ev,unlock));
function beep(){if(!sound||!ctx)return;const o=ctx.createOscillator();o.frequency.value=900;o.connect(ctx.destination);o.start();setTimeout(()=>o.stop(),300)}
function fallBeep(){
  if(!sound||!ctx)return;let n=0;
  const t=setInterval(()=>{const o=ctx.createOscillator();o.type='square';o.frequency.value=880;
    o.connect(ctx.destination);o.start();setTimeout(()=>o.stop(),300);if(++n>=6)clearInterval(t)},500);
}
function popup(title,body,key){
  if(notified[key])return;notified[key]=1;
  if('Notification' in window&&Notification.permission==='granted')new Notification(title,{body:body,requireInteraction:true});
}
function toast(msg,type){
  const t=document.createElement('div');t.className='toast '+(type||'');t.innerHTML=msg;
  $('toasts').appendChild(t);
  setTimeout(()=>{t.style.opacity=0;setTimeout(()=>t.remove(),450)},7000);
}
function toastOnce(key,msg,type){if(notified['t'+key])return;notified['t'+key]=1;toast(msg,type)}
function tick(){
  const d=new Date();
  $('clock').textContent=d.toLocaleDateString(undefined,{weekday:'long',day:'numeric',month:'long'})+' \u00b7 '+d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
}
function greeting(){const h=new Date().getHours();return h<12?'Good morning':h<17?'Good afternoon':'Good evening'}

/* ---------- login / sign-up / log out (same page) ---------- */
function authTab(n){
  $('f-login').style.display=n==='login'?'block':'none';
  $('f-signup').style.display=n==='signup'?'block':'none';
  $('tab-login').classList.toggle('sel',n==='login');
  $('tab-signup').classList.toggle('sel',n==='signup');
}
async function doLogin(e){
  e.preventDefault();$('lerr').textContent='';
  const r=await fetch('/api/login',{method:'POST',headers:J,body:JSON.stringify({email:$('l_email').value,password:$('l_pw').value})});
  const d=await r.json();
  if(d.ok){$('l_pw').value='';boot()}else{$('lerr').textContent=d.error||'Login failed'}
}
async function doSignup(e){
  e.preventDefault();$('serr').textContent='';
  const role=document.querySelector('input[name=s_role]:checked').value;
  const r=await fetch('/api/signup',{method:'POST',headers:J,body:JSON.stringify({name:$('s_name').value,email:$('s_email').value,password:$('s_pw').value,role:role})});
  const d=await r.json();
  if(d.ok){$('s_pw').value='';boot()}else{$('serr').textContent=d.error||'Sign up failed'}
}
async function logout(){await fetch('/api/logout',{method:'POST'});ROLE='';resetState();showAuth()}
function showAuth(){$('dash').style.display='none';$('auth').style.display='grid';document.body.className='authbody'}
function resetState(){
  P=0;CANACK=false;TODAY=[];ALERTS=[];VIT=[];PATS=[];CENTER=[];SAFE='ok';cur='overview';lastIds='';
  spoken={};notified={};seenFall={};firstFall=true;lastAlert={};firstP=true;
  $('plist').innerHTML='';$('psel').innerHTML='';$('viewing').textContent='';$('due').innerHTML='';
  $('fallbanner').className='banner';$('fallbanner').innerHTML='';
}
async function boot(){
  let r;try{r=await fetch('/api/me')}catch(e){showAuth();return}
  if(!r.ok){showAuth();return}
  enterDash(await r.json());
}
function enterDash(d){
  resetState();
  ROLE=d.role;MYID=d.id;
  document.body.className=ROLE;
  $('auth').style.display='none';$('dash').style.display='block';
  $('uname').textContent=d.name;$('uname2').textContent=d.name;
  $('avatar').textContent=(d.name||'?').slice(0,1).toUpperCase();
  $('rolelbl').textContent=ROLE==='patient'?'Patient':'Caregiver';
  tick();showSec('overview');renderStats();updateStatus();
  if(ROLE==='patient'){start(MYID,true);loadMe()}else{loadPatients()}
}

/* ---------- navigation ---------- */
document.querySelectorAll('#nav button').forEach(b=>b.onclick=()=>showSec(b.dataset.sec));
function showSec(n){
  cur=n;
  document.querySelectorAll('.sec').forEach(s=>{s.style.display=(s.id==='sec-'+n)?'block':'none'});
  document.querySelectorAll('#nav button').forEach(b=>b.classList.toggle('sel',b.dataset.sec===n));
  $('pagetitle').textContent=TITLES[n];
  refreshSec();
}
function refreshSec(){
  if(cur==='vitals'){kindChange();loadVitals()}
  if(cur==='appts')loadAppts();
  if(cur==='routine')loadConds();
  if(cur==='device')loadMe();
}

/* ---------- reminders ---------- */
async function loadToday(){
  if(!P)return;
  const r=await api('/api/care/'+P+'/today');if(!r.ok)return;
  TODAY=await r.json();
  renderDue();renderReminders();renderSched();renderStats();
}
function renderDue(){
  const due=TODAY.filter(i=>i.status==='due'||i.status==='missed');
  $('due').innerHTML=due.map(i=>`<div class="duecard"><span class="kic k-${i.kind}">${icon(KIC[i.kind]||'bell',22)}</span>
   <div class="grow"><div class="dtitle">${esc(i.title)}</div><div class="meta">${esc(i.kind)} \u00b7 due at ${i.time}${i.status==='missed'?' \u00b7 overdue':''}</div></div>
   ${CANACK?`<button class="btn" onclick="ack(${i.id})">${icon('check',16)} Done</button>`:'<span class="chip due">Waiting for the patient</span>'}</div>`).join('');
  if(CANACK&&due.length){
    beep();
    due.forEach(i=>{
      popup('Reminder: '+i.title,i.kind+' at '+i.time,'r'+i.id);
      toastOnce('r'+i.id,'<b>Time for:</b> '+esc(i.title),'warn');
      if(sound&&!spoken[i.id]){speechSynthesis.speak(new SpeechSynthesisUtterance('Reminder. '+i.title));spoken[i.id]=1}
    });
  }
}
function renderReminders(){
  $('rlist').innerHTML=TODAY.map(i=>`<div class="item"><div class="time">${i.time}</div>
   <span class="kic k-${i.kind}">${icon(KIC[i.kind]||'bell',20)}</span>
   <div class="grow"><div class="title">${esc(i.title)}</div><div class="meta">${esc(i.kind)}</div></div>
   <span class="chip ${i.status}">${STAT[i.status]||i.status}</span>
   <button class="icon" title="Remove" onclick="del(${i.id})">${icon('trash',17)}</button></div>`).join('')
   ||empty('No reminders for today. Add one below or build a routine.');
}
function renderSched(){
  $('sched').innerHTML=TODAY.slice(0,8).map(i=>`<div class="item"><div class="time">${i.time}</div>
   <span class="kic k-${i.kind}">${icon(KIC[i.kind]||'bell',18)}</span>
   <div class="grow"><div class="title">${esc(i.title)}</div></div>
   <span class="chip ${i.status}">${STAT[i.status]||i.status}</span></div>`).join('')||empty('Nothing scheduled today.');
}
async function ack(id){await api('/api/care/'+P+'/ack/'+id,{method:'POST'});loadToday()}
async function del(id){await api('/api/care/'+P+'/reminders/'+id,{method:'DELETE'});loadToday()}
async function add(){
  const b={kind:$('f_kind').value,title:$('f_title').value,time:$('f_time').value,date:$('f_date').value};
  if(!b.title||!b.time){alert('Enter a title and a time');return}
  await api('/api/care/'+P+'/reminders',{method:'POST',headers:J,body:JSON.stringify(b)});
  $('f_title').value='';loadToday();
}

/* ---------- stats ---------- */
function renderStats(){
  const nx=TODAY.find(i=>i.status==='upcoming');
  $('st-next-v').textContent=nx?nx.time:(P?'None left':'-');
  $('st-next-s').textContent=nx?nx.title:(P?'All done for today':'');
  const done=TODAY.filter(i=>i.status==='taken'||i.status==='late').length;
  const tot=TODAY.filter(i=>['taken','late','missed','due'].includes(i.status)).length;
  const pct=tot?Math.round(done*100/tot):null;
  $('st-adh-v').textContent=pct===null?'-':pct+'%';
  $('st-adh-bar').style.width=(pct||0)+'%';
  const v=VIT[0];
  $('st-vit-v').textContent=v?(VNAME[v.kind]+' '+v.value+(v.kind==='bp'?'/'+v.value2:'')):'No data';
  $('st-vit-s').textContent=v?(v.flag?'Outside usual range':'Within usual range'):'Log a reading in Vitals';
  const left=TODAY.filter(i=>i.status==='upcoming').length;
  $('greet').textContent=greeting()+', '+$('uname').textContent;
  $('greetsub').textContent=(ROLE==='caregiver'?('Looking after '+PATS.length+' patient'+(PATS.length===1?'':'s')+' \u00b7 '):'')
    +(P?(left+' reminder'+(left===1?'':'s')+' left today'):'Link a patient to get started');
  drawSparks();drawRing();
}

/* ---------- alerts ---------- */
async function loadAlerts(){
  if(!P)return;
  const r=await api('/api/care/'+P+'/alerts');if(!r.ok)return;
  ALERTS=await r.json();renderAlerts();
}
function renderAlerts(){
  const falls=ALERTS.filter(e=>e.result==='fall');
  const latest=falls[0];
  const recent=latest&&(Date.now()-new Date(latest.time.replace(' ','T')).getTime())<30*60*1000;
  const b=$('fallbanner');
  SAFE='ok';
  if(recent&&latest.status==='pending'){SAFE='pending';b.className='banner pending';
    b.innerHTML=icon('alert',28)+'<div>Possible fall detected \u2014 waiting for the user to cancel...</div>'}
  else if(recent&&latest.status==='alert_sent'){SAFE='sent';b.className='banner sent';
    b.innerHTML=icon('alert',28)+'<div>FALL ALERT sent to caregiver \u00b7 '+esc(latest.time)+'</div>'}
  else{b.className='banner';b.innerHTML=''}
  falls.forEach(e=>{
    if(!firstFall&&seenFall[e.id]!==e.status&&e.status!=='cancelled'){
      fallBeep();popup('Fall alert','Fall detected at '+e.time,'f'+e.id+e.status);
      toast('<b>Fall detected</b><br>'+esc(e.time)+' \u00b7 '+(ASTAT[e.status]||e.status),'bad');
    }
    seenFall[e.id]=e.status;
  });
  firstFall=false;
  const ico=$('st-safe-ico');
  if(SAFE==='ok'){ico.className='ico g4';$('st-safe-v').textContent='All safe';$('st-safe-s').textContent='No active fall alerts'}
  else{ico.className='ico gred';$('st-safe-v').textContent=SAFE==='pending'?'Possible fall':'Fall alert sent';$('st-safe-s').textContent=latest.time}
  $('f-count').textContent=falls.length;
  $('f-sent').textContent=falls.filter(e=>e.status==='alert_sent').length;
  $('f-canc').textContent=falls.filter(e=>e.status==='cancelled').length;
  $('fall-list').innerHTML=falls.map(e=>`<div class="item"><span class="kic k-fall">${icon('alert',20)}</span>
   <div class="grow"><div class="title">Fall detected</div><div class="meta">${esc(e.time)} \u00b7 confidence ${e.confidence}</div></div>
   <span class="chip a-${e.status}">${ASTAT[e.status]||e.status}</span></div>`).join('')||empty('No falls recorded. Stay safe!');
  drawFallCharts(falls);
  updateStatus();
}
function updateStatus(){
  const bad=SAFE!=='ok'||PATS.some(p=>p.alert==='fall_pending'||p.alert==='fall_sent');
  const s=$('status');
  s.className='status'+(bad?' bad':'');
  s.textContent=bad?'Fall alert':'Monitoring';
  $('navdot').style.display=bad?'inline-block':'none';
}
async function loadCenter(){
  const targets=ROLE==='patient'?[{id:MYID,name:'You'}]:PATS;
  let all=[];
  for(const p of targets){
    const r=await api('/api/care/'+p.id+'/alerts');if(!r.ok)continue;
    (await r.json()).forEach(e=>{e.pname=p.name;all.push(e)});
  }
  all.sort((a,b)=>b.time.localeCompare(a.time));
  CENTER=all;
  $('center').innerHTML=CENTER.slice(0,8).map(e=>{
    const f=e.result==='fall';
    return `<div class="item"><span class="kic ${f?'k-fall':'k-med2'}">${icon(f?'alert':'pill',20)}</span>
     <div class="grow"><div class="title">${f?'Fall detected':'Missed medicine'}</div>
     <div class="meta">${ROLE==='caregiver'?esc(e.pname)+' \u00b7 ':''}${esc(e.time)}</div></div>
     <span class="chip a-${e.status}">${ASTAT[e.status]||e.status}</span></div>`}).join('')||empty('No alerts. Everything is calm.');
}

/* ---------- caregiver: patients ---------- */
async function loadPatients(){
  const r=await api('/api/patients');if(!r.ok)return;
  PATS=await r.json();
  $('plist').innerHTML=PATS.map(p=>`<div class="pcard s-${p.alert} ${p.id===P?'sel':''}" onclick="selectPatient(${p.id})">
   <span class="av big">${esc(p.name.slice(0,1).toUpperCase())}</span>
   <div><b>${esc(p.name)}</b><div><span class="chip pa-${p.alert}">${PLABEL[p.alert]}</span></div></div></div>`).join('')
   ||empty('No patients linked yet. Enter an invite code below.');
  const ids=PATS.map(p=>p.id).join(',');
  if(ids!==lastIds){lastIds=ids;
    $('psel').innerHTML=PATS.map(p=>`<option value="${p.id}" ${p.id===P?'selected':''}>${esc(p.name)}</option>`).join('')}
  PATS.forEach(p=>{
    if(!firstP&&lastAlert[p.id]!==p.alert&&(p.alert==='fall_pending'||p.alert==='fall_sent')){
      fallBeep();popup('Fall alert',p.name+' - '+PLABEL[p.alert],'p'+p.id+p.alert);
      toast('<b>'+esc(p.name)+'</b><br>'+PLABEL[p.alert],'bad');
    }
    lastAlert[p.id]=p.alert;
  });
  firstP=false;
  if(!P&&PATS.length)selectPatient(PATS[0].id);
  renderStats();updateStatus();
}
function selectPatient(id){
  P=id;
  const p=PATS.find(x=>x.id===id);
  $('viewing').textContent=p?(' \u00b7 Viewing: '+p.name):'';
  if($('psel').value!==String(id))$('psel').value=String(id);
  start(id,false);loadPatients();
}
async function link(){
  const r=await api('/api/link',{method:'POST',headers:J,body:JSON.stringify({code:$('code').value})});
  const d=await r.json();
  $('lmsg').textContent=d.ok?'':(d.error||'Failed');
  if(d.ok){$('code').value='';loadPatients()}
}

/* ---------- routine ---------- */
async function loadConds(){
  if(!P)return;
  const r=await api('/api/care/'+P+'/conditions');if(!r.ok)return;
  const c=await r.json();
  document.querySelectorAll('.cond').forEach(x=>x.checked=c.includes(x.value));
}
async function applyRoutine(){
  if(!P){alert('Select a patient first');return}
  const conds=[...document.querySelectorAll('.cond:checked')].map(x=>x.value);
  const r=await api('/api/care/'+P+'/routine',{method:'POST',headers:J,body:JSON.stringify({conditions:conds})});
  const d=await r.json();
  $('rmsg').textContent='Done: '+d.added+' new reminders added. See the Reminders section.';
  loadToday();
}

/* ---------- vitals ---------- */
function kindChange(){$('v_val2').style.display=($('v_kind').value==='bp')?'inline-block':'none'}
async function addVital(){
  if(!P){alert('Select a patient first');return}
  const k=$('v_kind').value, v=parseFloat($('v_val').value), v2=parseFloat($('v_val2').value);
  if(isNaN(v)||(k==='bp'&&isNaN(v2))){alert('Enter the reading');return}
  const r=await api('/api/care/'+P+'/vitals',{method:'POST',headers:J,body:JSON.stringify({kind:k,value:v,value2:isNaN(v2)?0:v2})});
  if(!r.ok){alert('Could not save');return}
  const d=await r.json();
  $('vmsg').textContent=d.flag?'Outside the usual range - consider contacting the doctor.':'Saved.';
  $('v_val').value='';$('v_val2').value='';loadVitals();
}
async function loadVitals(){
  if(!P)return;
  const r=await api('/api/care/'+P+'/vitals');if(!r.ok)return;
  VIT=await r.json();
  $('vlist').innerHTML=VIT.slice(0,10).map(x=>`<div class="item"><div class="time" style="width:130px">${x.time}</div>
   <div class="grow"><div class="title">${VNAME[x.kind]}: ${x.value}${x.kind==='bp'?'/'+x.value2:''}</div></div>
   <span class="chip ${x.flag?'bad':'good'}">${x.flag?'Outside usual range':'Normal'}</span></div>`).join('')||empty('No readings yet.');
  drawChart(VIT);renderStats();
}
function drawChart(rows){
  const k=$('v_kind').value, pts=rows.filter(x=>x.kind===k).reverse().map(x=>x.value);
  const cv=$('vchart'), g=cv.getContext('2d'), W=cv.width, H=cv.height;
  g.clearRect(0,0,W,H);
  g.font='14px Segoe UI, Arial';g.fillStyle='#64748b';
  if(pts.length<2){g.fillText('Add at least 2 readings of this type to see the trend',16,34);return}
  const mn=Math.min(...pts), mx=Math.max(...pts), pad=34;
  const X=i=>pad+i*(W-2*pad)/(pts.length-1);
  const Y=v=>H-pad-(mx===mn?0.5:(v-mn)/(mx-mn))*(H-2*pad);
  g.strokeStyle='#e2e8f0';g.lineWidth=1;
  for(let i=0;i<4;i++){const y=pad+i*(H-2*pad)/3;g.beginPath();g.moveTo(pad,y);g.lineTo(W-pad,y);g.stroke()}
  const gr=g.createLinearGradient(0,pad,0,H-pad);gr.addColorStop(0,'rgba(37,99,235,.28)');gr.addColorStop(1,'rgba(37,99,235,0)');
  g.beginPath();g.moveTo(X(0),H-pad);pts.forEach((v,i)=>g.lineTo(X(i),Y(v)));g.lineTo(X(pts.length-1),H-pad);g.closePath();g.fillStyle=gr;g.fill();
  g.beginPath();pts.forEach((v,i)=>{if(i)g.lineTo(X(i),Y(v));else g.moveTo(X(i),Y(v))});
  g.strokeStyle='#2563eb';g.lineWidth=3;g.lineJoin='round';g.stroke();
  pts.forEach((v,i)=>{g.beginPath();g.arc(X(i),Y(v),4.5,0,7);g.fillStyle='#fff';g.fill();g.strokeStyle='#2563eb';g.lineWidth=2;g.stroke()});
  g.fillStyle='#64748b';
  g.fillText(VNAME[k]+(k==='bp'?' (top number)':'')+': '+mn+' to '+mx,pad,20);
}

/* ---------- visuals ---------- */
const SPK=['pulse','spo2','bp','sugar','temp'];
function drawSparks(){
  const el=$('spark-grid');if(!el)return;
  const html=SPK.map(k=>{
    const rows=VIT.filter(x=>x.kind===k);
    if(!rows.length)return '';
    const last=rows[0], pts=rows.slice(0,12).reverse().map(x=>x.value);
    const mn=Math.min(...pts), mx=Math.max(...pts), W=120, H=34;
    const X=i=>pts.length>1?2+i*(W-4)/(pts.length-1):W/2;
    const Y=v=>mx===mn?H/2:H-4-(v-mn)/(mx-mn)*(H-8);
    const col=last.flag?'#dc2626':'#2563eb';
    const line=pts.map((v,i)=>X(i).toFixed(1)+','+Y(v).toFixed(1)).join(' ');
    return '<div class="spark'+(last.flag?' bad':'')+'"><div class="sn">'+VNAME[k]+'</div>'
      +'<b>'+last.value+(k==='bp'?'/'+last.value2:'')+'</b>'
      +'<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none"><polyline points="'+line+'" fill="none" stroke="'+col+'" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>'
      +'<circle cx="'+X(pts.length-1).toFixed(1)+'" cy="'+Y(pts[pts.length-1]).toFixed(1)+'" r="3" fill="'+col+'"/></svg>'
      +'<div class="sn">'+(last.flag?'Outside usual range':'Within usual range')+'</div></div>';
  }).join('');
  el.innerHTML=html||empty('No readings yet. Log one in Vitals.');
}
function drawRing(){
  const sv=$('adh-ring');if(!sv)return;
  const c={done:0,due:0,missed:0,upcoming:0};
  TODAY.forEach(i=>{
    if(i.status==='taken'||i.status==='late')c.done++;
    else if(i.status==='due')c.due++;
    else if(i.status==='missed')c.missed++;
    else if(i.status==='upcoming')c.upcoming++;
  });
  const tot=c.done+c.due+c.missed+c.upcoming, R=48, C=2*Math.PI*R;
  const segs=[['done','#16a34a','Done'],['due','#d97706','Due now'],['missed','#dc2626','Missed'],['upcoming','#cbd5e1','Coming up']];
  let off=0,h='<circle cx="60" cy="60" r="'+R+'" fill="none" stroke="#f1f5f9" stroke-width="14"/>';
  if(tot)segs.forEach(s=>{
    const len=c[s[0]]*C/tot;
    if(len>0){h+='<circle cx="60" cy="60" r="'+R+'" fill="none" stroke="'+s[1]+'" stroke-width="14" stroke-dasharray="'+len.toFixed(1)+' '+(C-len).toFixed(1)+'" stroke-dashoffset="'+(-off).toFixed(1)+'" transform="rotate(-90 60 60)"/>';off+=len}
  });
  h+='<text x="60" y="60" text-anchor="middle" font-size="24" font-weight="700" fill="#0f172a">'+(tot?c.done+'/'+tot:'-')+'</text>'
    +'<text x="60" y="78" text-anchor="middle" font-size="10" fill="#64748b">done today</text>';
  sv.innerHTML=h;
  $('ring-legend').innerHTML=segs.map(s=>'<div><i style="background:'+s[1]+'"></i>'+s[2]+': <b>'+c[s[0]]+'</b></div>').join('');
}
let LIVE=null;
async function loadLive(){
  if(!P)return;
  const r=await api('/api/care/'+P+'/live');if(!r.ok)return;
  LIVE=await r.json();drawLive();
}
function drawLive(){
  const cv=$('livechart');if(!cv)return;
  const g=cv.getContext('2d'), W=cv.width, H=cv.height, sub=$('live-sub');
  g.clearRect(0,0,W,H);g.font='13px Segoe UI, Arial';g.fillStyle='#64748b';g.textAlign='left';
  if(!LIVE||!LIVE.svm||LIVE.svm.length<2){
    sub.textContent='';
    g.fillText('No capture yet. The wearable sends one when it feels a strong movement.',16,34);return}
  const v=LIVE.svm, n=v.length, pl=42, pr=14, pt=14, pb=26;
  const mx=Math.max(3,Math.ceil(Math.max(...v)));
  const X=i=>pl+i*(W-pl-pr)/(n-1), Y=a=>H-pb-a/mx*(H-pb-pt);
  g.strokeStyle='#e2e8f0';g.lineWidth=1;
  for(let a=0;a<=mx;a++){g.beginPath();g.moveTo(pl,Y(a));g.lineTo(W-pr,Y(a));g.stroke();g.fillText(a+' g',6,Y(a)+4)}
  for(let s=0;s*50<n;s++)g.fillText(s+' s',X(s*50)-8,H-8);
  const fall=LIVE.result==='fall', col=fall?'#dc2626':'#2563eb';
  g.setLineDash([6,5]);g.strokeStyle='#f59e0b';g.beginPath();g.moveTo(pl,Y(1.8));g.lineTo(W-pr,Y(1.8));g.stroke();g.setLineDash([]);
  g.fillStyle='#d97706';g.fillText('trigger 1.8 g',W-pr-84,Y(1.8)-6);
  const gr=g.createLinearGradient(0,pt,0,H-pb);gr.addColorStop(0,fall?'rgba(220,38,38,.28)':'rgba(37,99,235,.25)');gr.addColorStop(1,'rgba(255,255,255,0)');
  g.beginPath();g.moveTo(X(0),H-pb);v.forEach((a,i)=>g.lineTo(X(i),Y(a)));g.lineTo(X(n-1),H-pb);g.closePath();g.fillStyle=gr;g.fill();
  g.beginPath();v.forEach((a,i)=>{if(i)g.lineTo(X(i),Y(a));else g.moveTo(X(i),Y(a))});
  g.strokeStyle=col;g.lineWidth=2.5;g.lineJoin='round';g.stroke();
  sub.textContent='Captured '+LIVE.time+' \u00b7 classified as '+(fall?'a fall':'normal movement')+' ('+LIVE.confidence+' confidence) \u00b7 peak '+Math.max(...v).toFixed(1)+' g';
}
function barChart(cv,labels,vals,cols,fmt,mx,msg){
  const g=cv.getContext('2d'), W=cv.width, H=cv.height, pt=24, pb=28, px=12;
  g.clearRect(0,0,W,H);g.font='13px Segoe UI, Arial';
  if(!vals.length){g.fillStyle='#64748b';g.textAlign='left';g.fillText(msg,16,34);return}
  const n=vals.length, slot=(W-2*px)/n, bw=Math.min(46,slot*.6);
  g.strokeStyle='#e2e8f0';g.lineWidth=1;g.beginPath();g.moveTo(px,H-pb);g.lineTo(W-px,H-pb);g.stroke();
  vals.forEach((v,i)=>{
    const h=v/mx*(H-pt-pb), x=px+i*slot+(slot-bw)/2, y=H-pb-h;
    g.fillStyle=cols[i];
    g.beginPath();
    if(g.roundRect){g.roundRect(x,y,bw,Math.max(h,0),6)}else{g.rect(x,y,bw,Math.max(h,0))}
    g.fill();
    g.textAlign='center';g.fillStyle='#0f172a';g.fillText(fmt(v),x+bw/2,y-6);
    g.fillStyle='#64748b';g.fillText(labels[i],x+bw/2,H-9);
  });
}
function drawFallCharts(falls){
  const a=$('fchart-day'), b=$('fchart-conf');if(!a||!b)return;
  const days=[];for(let i=6;i>=0;i--){const d=new Date();d.setDate(d.getDate()-i);days.push(d)}
  const key=d=>d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
  const cnt=days.map(d=>falls.filter(e=>e.time.slice(0,10)===key(d)).length);
  barChart(a,days.map(d=>['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][d.getDay()]),cnt,cnt.map(()=>'#2563eb'),String,Math.max(3,...cnt),'');
  const last=falls.slice(0,8).reverse();
  const SC={alert_sent:'#dc2626',cancelled:'#16a34a',pending:'#d97706'};
  barChart(b,last.map(e=>e.time.slice(11,16)),last.map(e=>e.confidence),last.map(e=>SC[e.status]||'#64748b'),
           v=>Math.round(v*100)+'%',1,'No falls recorded yet.');
}

/* ---------- appointments ---------- */
async function loadAppts(){
  if(!P)return;
  const r=await api('/api/care/'+P+'/appointments');if(!r.ok)return;
  const a=await r.json();
  $('alist').innerHTML=a.map(x=>`<div class="item"><span class="kic k-appointment">${icon('calendar',20)}</span>
   <div class="grow"><div class="title">${esc(x.title)}</div><div class="meta">${x.date} \u00b7 ${x.time}</div></div>
   <button class="icon" title="Cancel" onclick="delAppt(${x.id})">${icon('trash',17)}</button></div>`).join('')||empty('No upcoming appointments.');
}
async function delAppt(id){await api('/api/care/'+P+'/reminders/'+id,{method:'DELETE'});loadAppts();loadToday()}
async function addAppt(){
  if(!P){alert('Select a patient first');return}
  const b={kind:'appointment',title:$('a_title').value,time:$('a_time').value,date:$('a_date').value};
  if(!b.title||!b.time||!b.date){alert('Enter the doctor or reason, a date and a time');return}
  await api('/api/care/'+P+'/reminders',{method:'POST',headers:J,body:JSON.stringify(b)});
  $('a_title').value='';loadAppts();loadToday();
}

/* ---------- my device (patient) ---------- */
async function loadMe(){
  const r=await api('/api/me');if(!r.ok)return;
  const d=await r.json();
  if(d.role!=='patient')return;
  $('token').textContent=d.token;$('invite').textContent=d.invite;
  $('cgs').innerHTML=d.caregivers.map(n=>`<div class="item"><span class="av">${esc(n.slice(0,1).toUpperCase())}</span>
   <div class="grow"><div class="title">${esc(n)}</div></div><span class="chip good">Linked</span></div>`).join('')
   ||empty('No caregivers linked yet. Share your invite code.');
}
function copyText(id,btn){
  const t=$(id).textContent, o=btn.innerHTML;
  const done=()=>{btn.innerHTML=icon('check',16)+' Copied';setTimeout(()=>{btn.innerHTML=o},1500)};
  if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(done)}
  else{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand('copy')}catch(e){}a.remove();done()}
}

/* ---------- start ---------- */
function start(pid,canack){
  P=pid;CANACK=canack;
  seenFall={};firstFall=true;spoken={};notified={};TODAY=[];ALERTS=[];VIT=[];
  LIVE=null;loadToday();loadAlerts();loadVitals();loadCenter();loadLive();refreshSec();
}
function every(ms,fn){setInterval(()=>{if(!ROLE)return;try{const p=fn();if(p&&p.catch)p.catch(()=>{})}catch(e){}},ms)}
every(5000,loadToday);every(2000,loadAlerts);every(2000,loadLive);every(4000,loadCenter);
every(4000,()=>ROLE==='caregiver'?loadPatients():null);
setInterval(()=>{if(ROLE)tick()},30000);
boot();
"""

HTML = ("<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Smart Health Companion</title>" + CSS + "</head><body class='authbody'>"
        + AUTH_HTML + DASH_HTML + "<div id='jserr'></div><script>" + JS + "</script></body></html>")

@pages.route("/")
def index():
    return HTML

@pages.route("/care")
@pages.route("/care/<int:pid>")
def old_care(pid=None):
    return redirect("/")