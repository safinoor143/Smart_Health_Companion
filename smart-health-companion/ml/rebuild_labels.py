"""Rebuild data\\labels.csv from the recordings that are really in the data folder.
Fixes 'FileNotFoundError' when labels.csv lists files that no longer exist.
Run from C:\\fallproject:   python rebuild_labels.py
The old labels.csv is kept as labels_before_rebuild.csv."""
import os, re, csv, shutil, collections
D = "data"
idx = os.path.join(D, "labels.csv")
if os.path.exists(idx):
    shutil.copy(idx, os.path.join(D, "labels_before_rebuild.csv"))
rows, count = [], collections.defaultdict(collections.Counter)
for fn in sorted(os.listdir(D)):
    m = re.match(r"^(.+?)_(left|right)_(.+)_(\d+)\.csv$", fn)
    if not m:
        continue
    subject, wrist, act, _ = m.groups()
    is_fall = 1 if act.startswith("fall_") else 0
    rows.append([fn, subject, wrist, act, is_fall])
    count[subject][act] += 1
with open(idx, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["file", "subject", "wrist", "activity", "is_fall"])
    w.writerows(rows)
print("labels.csv rebuilt: %d recordings" % len(rows))
for s in sorted(count):
    falls = sum(v for a, v in count[s].items() if a.startswith("fall_"))
    print("  %-4s falls=%-3d not-falls=%-3d" % (s, falls, sum(count[s].values()) - falls))
