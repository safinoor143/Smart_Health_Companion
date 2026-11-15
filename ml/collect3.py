"""Record labelled windows from the board (MODE = "collect") over USB.
Close Thonny first (it holds the COM port).   Run:  python collect3.py COM5
Needs:  pip install pyserial
"""
import sys, os, csv, time
import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM5"
ACTIVITIES = {   # key: (label, class)  class 1 = fall, 0 = not a fall
    "1": ("fall_forward", 1), "2": ("fall_backward", 1), "3": ("fall_side_left", 1),
    "4": ("fall_side_right", 1), "5": ("fall_slump_sitting", 1),
    "6": ("walk_arm_swing", 0), "7": ("wave_clap", 0), "8": ("hit_table", 0),
    "9": ("sit_down_fast", 0), "10": ("jump", 0), "11": ("stumble_no_fall", 0),
    "12": ("put_down_object", 0), "13": ("stairs", 0), "14": ("lie_down_slowly", 0),
}
os.makedirs("data", exist_ok=True)
subject = input("Subject id (e.g. S1, S2, ...): ").strip()
side = input("Wrist (left/right): ").strip()
index = os.path.join("data", "labels.csv")
new = not os.path.exists(index)
lf = open(index, "a", newline="")
lw = csv.writer(lf)
if new:
    lw.writerow(["file", "subject", "wrist", "activity", "is_fall"])
ser = serial.Serial()
ser.port = PORT
ser.baudrate = 115200
ser.timeout = 1
ser.dtr = False      # do not hold the board in reset
ser.rts = False
ser.open()
print("\nOn the board set MODE = \"collect\", save, press Ctrl+D... then close Thonny.")
print("Activities:")
for k, (a, c) in ACTIVITIES.items():
    print("  %2s  %-20s %s" % (k, a, "FALL" if c else "not a fall"))
print("Type a number to choose; Enter repeats the last one; q quits.\n")
cur = None
counts = {}
while True:
    s = input("activity> ").strip()
    if s == "q":
        break
    if s in ACTIVITIES:
        cur = s
    if cur is None:
        continue
    act, cls = ACTIVITIES[cur]
    print("  Do: %s -> waiting for the board's window (move hard enough to pass 1.8 g)..." % act)
    rows, got, t0 = [], False, time.time()
    while time.time() - t0 < 60:
        line = ser.readline().decode(errors="ignore").strip()
        if line == "WINDOW_START":
            rows, got = [], True
        elif line == "WINDOW_END" and got:
            break
        elif got and line:
            try:
                rows.append([float(x) for x in line.split(",")])
            except ValueError:
                pass
    else:
        print("  nothing received in 60 s (movement too gentle? skipped)")
        continue
    if len(rows) != 200:
        print("  incomplete window (%d rows), discarded - repeat" % len(rows))
        continue
    counts[act] = counts.get(act, 0) + 1
    fn = "%s_%s_%s_%02d.csv" % (subject, side, act, counts[act])
    while os.path.exists(os.path.join("data", fn)):      # never overwrite an earlier recording
        counts[act] += 1
        fn = "%s_%s_%s_%02d.csv" % (subject, side, act, counts[act])
    with open(os.path.join("data", fn), "w", newline="") as f:
        csv.writer(f).writerows(rows)
    lw.writerow([fn, subject, side, act, cls])
    lf.flush()
    print("  saved %s   (so far: %s)" % (fn, ", ".join("%s=%d" % kv for kv in sorted(counts.items()))))
