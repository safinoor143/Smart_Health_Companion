"""Version 2 training: compares the current features with the richer ones and several models,
all with leave-one-subject-out testing, then sweeps the alarm cut-off.
Run:  python train2.py        Writes results2.txt
Needs: pip install scikit-learn numpy"""
import csv, os, sys
import numpy as np
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import confusion_matrix
from featlib import features
from featlib2 import features2, FEATURES2

D = "data"
X1, X2, y, g, acts = [], [], [], [], []
for r in csv.DictReader(open(os.path.join(D, "labels.csv"))):
    rows = [[float(v) for v in l.split(",")] for l in open(os.path.join(D, r["file"])) if l.strip()]
    X1.append(features([x[:3] for x in rows])); X2.append(features2(rows))
    y.append(int(r["is_fall"])); g.append(r["subject"]); acts.append(r["activity"])
X1, X2, y, g, acts = np.array(X1), np.array(X2), np.array(y), np.array(g), np.array(acts)
subs = sorted(set(g))
out = []
def say(s=""):
    print(s); out.append(s)
say("Windows: %d (falls %d, not falls %d)  Subjects: %s" % (len(y), y.sum(), (1 - y).sum(), ", ".join(subs)))
if len(subs) < 3:
    sys.exit("Need at least 3 subjects.")

def rates(yt, yp):
    tn, fp, fn, tp = confusion_matrix(yt, yp, labels=[0, 1]).ravel()
    se = tp / (tp + fn) if tp + fn else float("nan"); sp = tn / (tn + fp) if tn + fp else float("nan")
    return tp, fn, tn, fp, se, sp, (tp + tn) / len(yt)

MODELS = {
    "RF, old features":      (X1, lambda: RandomForestClassifier(n_estimators=15, max_depth=5, min_samples_leaf=2, class_weight="balanced", random_state=1)),
    "RF, new features":      (X2, lambda: RandomForestClassifier(n_estimators=200, max_depth=6, min_samples_leaf=2, class_weight="balanced", random_state=1)),
    "ExtraTrees, new":       (X2, lambda: ExtraTreesClassifier(n_estimators=200, max_depth=7, min_samples_leaf=2, class_weight="balanced", random_state=1)),
    "GradBoost, new":        (X2, lambda: GradientBoostingClassifier(n_estimators=120, max_depth=3, learning_rate=0.08, random_state=1)),
}
probs = {}
say("\nLeave-one-subject-out, cut-off 0.5 (all windows pooled):")
best, bestscore = None, -1
for name, (X, mk) in MODELS.items():
    p = np.zeros(len(y))
    for tr, te in LeaveOneGroupOut().split(X, y, g):
        m = mk().fit(X[tr], y[tr]); p[te] = m.predict_proba(X[te])[:, 1]
    probs[name] = p
    tp, fn, tn, fp, se, sp, ac = rates(y, (p >= 0.5).astype(int))
    bal = (se + sp) / 2
    say("  %-20s sens=%5.1f%%  spec=%5.1f%%  acc=%5.1f%%  balanced=%5.1f%%" % (name, 100 * se, 100 * sp, 100 * ac, 100 * bal))
    if name != "RF, old features" and bal > bestscore:
        best, bestscore = name, bal
say("\nBest new model: %s" % best)
p = probs[best]
say("\nCut-off sweep for the best model (higher cut-off = fewer false alarms, more missed falls):")
for c in (0.3, 0.4, 0.5, 0.6, 0.7):
    tp, fn, tn, fp, se, sp, ac = rates(y, (p >= c).astype(int))
    say("  cut-off %.1f  sens=%5.1f%%  spec=%5.1f%%  missed falls=%d  false alarms=%d" % (c, 100 * se, 100 * sp, fn, fp))
say("\nPer person (best model, cut-off 0.5):")
for s in subs:
    k = g == s; tp, fn, tn, fp, se, sp, ac = rates(y[k], (p[k] >= 0.5).astype(int))
    say("  %-4s n=%d  sens=%.0f%%  spec=%.0f%%" % (s, k.sum(), 100 * se, 100 * sp))
say("\nPer activity (share called FALL, best model):")
for a in sorted(set(acts)):
    k = acts == a; say("  %-20s n=%2d  called fall: %3.0f%%" % (a, k.sum(), 100 * (p[k] >= 0.5).mean()))
mdl = MODELS[best][1]().fit(MODELS[best][0], y)
if hasattr(mdl, "feature_importances_"):
    say("\nMost useful features:")
    for n, v in sorted(zip(FEATURES2, mdl.feature_importances_), key=lambda t: -t[1])[:8]:
        say("  %-18s %.2f" % (n, v))
open("results2.txt", "w").write("\n".join(out))
say("\nSaved results2.txt")
