"""Receives recordings from the board over Wi-Fi (MODE = "wifi") and saves them in data\\.
Run on the laptop (same hotspot as the board):   python collect_wifi.py
No USB cable and no extra packages needed.
Commands at the prompt:  a number (1-14) = record that activity   p = pause (stray movements are thrown away)
                         q = quit        s = show counts
"""
import os, csv, sys, threading, socket
from http.server import BaseHTTPRequestHandler, HTTPServer

ACTIVITIES = {
    "1": ("fall_forward", 1), "2": ("fall_backward", 1), "3": ("fall_side_left", 1),
    "4": ("fall_side_right", 1), "5": ("fall_slump_sitting", 1),
    "6": ("walk_arm_swing", 0), "7": ("wave_clap", 0), "8": ("hit_table", 0),
    "9": ("sit_down_fast", 0), "10": ("jump", 0), "11": ("stumble_no_fall", 0),
    "12": ("put_down_object", 0), "13": ("stairs", 0), "14": ("lie_down_slowly", 0),
}
PORT = 8000
os.makedirs("data", exist_ok=True)
index = os.path.join("data", "labels.csv")
new = not os.path.exists(index)
lf = open(index, "a", newline="")
lw = csv.writer(lf)
if new:
    lw.writerow(["file", "subject", "wrist", "activity", "is_fall"])
    lf.flush()
lock = threading.Lock()
state = {"cur": None, "subject": "", "wrist": "", "counts": {}}


def save_window(text):
    rows = []
    for line in text.strip().splitlines():
        try:
            rows.append([float(x) for x in line.split(",")])
        except ValueError:
            pass
    with lock:
        key = state["cur"]
        if key is None:
            print("  (paused) stray window thrown away")
            return 200, "ignored"
        if len(rows) != 200:
            print("  incomplete window (%d rows) - repeat the movement" % len(rows))
            return 422, "incomplete"
        act, cls = ACTIVITIES[key]
        n = state["counts"].get((state["subject"], act), 0) + 1
        fn = "%s_%s_%s_%02d.csv" % (state["subject"], state["wrist"], act, n)
        while os.path.exists(os.path.join("data", fn)):
            n += 1
            fn = "%s_%s_%s_%02d.csv" % (state["subject"], state["wrist"], act, n)
        state["counts"][(state["subject"], act)] = n
        with open(os.path.join("data", fn), "w", newline="") as f:
            csv.writer(f).writerows(rows)
        lw.writerow([fn, state["subject"], state["wrist"], act, cls])
        lf.flush()
        print("  saved %s   (%s so far: %d)" % (fn, act, n))
        return 200, "ok"


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        code, msg = save_window(self.rfile.read(n).decode(errors="ignore"))
        self.send_response(code); self.send_header("Content-Length", str(len(msg))); self.end_headers()
        self.wfile.write(msg.encode())

    def log_message(self, *a):
        pass


def my_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except Exception:
        return "(run ipconfig)"


state["subject"] = input("Subject id (e.g. s1, s2): ").strip()
state["wrist"] = input("Wrist (left/right): ").strip()
srv = HTTPServer(("0.0.0.0", PORT), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
print("\nThis laptop's address for the board (LAPTOP_IP in main.py): %s" % my_ip())
print("If Windows asks about the firewall, allow Python on PRIVATE networks.\n")
for k, (a, c) in ACTIVITIES.items():
    print("  %2s  %-20s %s" % (k, a, "FALL" if c else "not a fall"))
print("\nType a number to start recording that activity. p = pause, s = counts, q = quit.\n")
while True:
    s = input("activity> ").strip().lower()
    if s == "q":
        break
    elif s == "p":
        state["cur"] = None; print("  paused: windows are thrown away")
    elif s == "s":
        print("  ", ", ".join("%s=%d" % (a, n) for (_, a), n in sorted(state["counts"].items())))
    elif s in ACTIVITIES:
        state["cur"] = s; print("  recording: %s (each movement above 1.8 g is saved)" % ACTIVITIES[s][0])
