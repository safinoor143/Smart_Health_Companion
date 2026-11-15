"""Review and clean recordings.  Nothing is deleted: rejected files are moved to data_rejected\\ and logged.
  python review.py                      list all recordings of every subject (oldest first)
  python review.py s2                   list only subject s2
  python review.py reject "reason" file1.csv file2.csv ...     move recording errors out of the dataset
  python review.py restore file1.csv    put a rejected file back
"""
import csv, os, sys, shutil, time, math
D, R = "data", "data_rejected"
idx = os.path.join(D, "labels.csv")

def rows():
    return list(csv.DictReader(open(idx)))

def peak(fn):
    best = 0.0
    for l in open(os.path.join(D, fn)):
        p = l.strip().split(",")
        if len(p) >= 3:
            a = math.sqrt(sum(float(v) ** 2 for v in p[:3]))
            best = max(best, a)
    return best

args = sys.argv[1:]
if args and args[0] == "reject":
    reason, files = args[1], args[2:]
    os.makedirs(R, exist_ok=True)
    allr = rows(); keep = [r for r in allr if r["file"] not in files]
    log = open(os.path.join(R, "rejected_log.csv"), "a", newline="")
    lw = csv.writer(log)
    for r in allr:
        if r["file"] in files:
            shutil.move(os.path.join(D, r["file"]), os.path.join(R, r["file"]))
            lw.writerow([time.strftime("%Y-%m-%d %H:%M"), r["file"], r["subject"], r["activity"], reason])
            print("rejected", r["file"])
    log.close()
    w = csv.DictWriter(open(idx, "w", newline=""), fieldnames=["file", "subject", "wrist", "activity", "is_fall"])
    w.writeheader(); w.writerows(keep)
    print("%d recordings left in the dataset" % len(keep))
elif args and args[0] == "restore":
    allr = rows()
    for fn in args[1:]:
        src = os.path.join(R, fn)
        if os.path.exists(src):
            shutil.move(src, os.path.join(D, fn))
            parts = fn[:-4].split("_")
            print("restored", fn, "- add its row back to labels.csv by hand (subject, wrist, activity, is_fall)")
else:
    who = args[0] if args else None
    rs = [r for r in rows() if who is None or r["subject"] == who]
    rs.sort(key=lambda r: os.path.getmtime(os.path.join(D, r["file"])))
    print("%-5s %-8s %-30s %-6s %-8s %s" % ("#", "time", "file", "fall?", "peak(g)", "activity"))
    for i, r in enumerate(rs, 1):
        t = time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(os.path.join(D, r["file"]))))
        print("%-5d %-8s %-30s %-6s %-8.1f %s" % (i, t, r["file"], "FALL" if r["is_fall"] == "1" else "no", peak(r["file"]), r["activity"]))
    c = {}
    for r in rs:
        c[r["activity"]] = c.get(r["activity"], 0) + 1
    print("\nCounts:", ", ".join("%s=%d" % kv for kv in sorted(c.items())))
