"""Leave-one-volunteer-out evaluation used for the paper's results.
Run from the ml folder:  python final_analysis.py   (reads ../data, writes results_final.json and three figures)"""
import csv, os, json, math
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import roc_auc_score
from featlib import features
from featlib2 import features2
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
X1, X2, y, g, acts = [], [], [], [], []
for r in csv.DictReader(open(os.path.join(D, "labels.csv"))):
    rows = [[float(v) for v in l.split(",")] for l in open(os.path.join(D, r["file"])) if l.strip()]
    X1.append(features([x[:3] for x in rows])); X2.append(features2(rows))
    y.append(int(r["is_fall"])); g.append(r["subject"]); acts.append(r["activity"])
X1, X2, y, g, acts = map(np.array, (X1, X2, y, g, acts))

def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 2
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)

def loso(X, make):
    p = np.zeros(len(y))
    for tr, te in LeaveOneGroupOut().split(X, y, g):
        p[te] = make().fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return p

rf1 = loso(X1, lambda: RandomForestClassifier(n_estimators=15, max_depth=5, min_samples_leaf=2, class_weight="balanced", random_state=1))
gb = loso(X2, lambda: GradientBoostingClassifier(n_estimators=120, max_depth=3, learning_rate=0.08, random_state=1))
rule = ((X1[:, 0] >= 3.0) & (X1[:, 0] <= 14.0)).astype(float)   # the simple impact rule (peak 3-14 g)

def stats(p, cut=0.5, mask=None):
    m = np.ones(len(y), bool) if mask is None else mask
    pr = p[m] >= cut; yt = y[m] == 1
    tp = int((pr & yt).sum()); fn = int((~pr & yt).sum()); tn = int((~pr & ~yt).sum()); fp = int((pr & ~yt).sum())
    return dict(tp=tp, fn=fn, tn=tn, fp=fp, sens=tp / (tp + fn) if tp + fn else None, spec=tn / (tn + fp) if tn + fp else None,
                acc=(tp + tn) / m.sum(), sens_ci=wilson(tp, tp + fn), spec_ci=wilson(tn, tn + fp))

R = {"n": len(y), "falls": int(y.sum()), "nonfalls": int((1 - y).sum()), "subjects": sorted(set(g)),
     "rule": stats(rule), "rf1": stats(rf1), "gb": stats(gb), "gb03": stats(gb, 0.3),
     "auc_gb": roc_auc_score(y, gb), "auc_rf1": roc_auc_score(y, rf1)}
R["per_subject"] = {s: stats(gb, 0.5, g == s) for s in sorted(set(g))}
R["per_activity"] = {a: dict(n=int((acts == a).sum()), called=float((gb[acts == a] >= 0.5).mean()), fall=int(y[acts == a][0])) for a in sorted(set(acts))}
json.dump(R, open("results_final.json", "w"), indent=1, default=float)

plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(3.4, 2.4), dpi=300)
names = ["Old rule\n(3-14 g)", "RF, accel.\nfeatures", "GB, accel. +\ngyro features"]; keys = ["rule", "rf1", "gb"]; w = 0.36; x = np.arange(3)
for off, met, hatch, col in ((-w / 2, "sens", "//", "#4a4a4a"), (w / 2, "spec", "", "#bdbdbd")):
    v = [100 * R[k][met] for k in keys]; ci = [R[k][met + "_ci"] for k in keys]
    err = [[v[i] - 100 * ci[i][0] for i in range(3)], [100 * ci[i][1] - v[i] for i in range(3)]]
    ax.bar(x + off, v, w, yerr=err, capsize=2, color=col, edgecolor="black", hatch=hatch, linewidth=0.5, error_kw={"linewidth": 0.6}, label="Sensitivity" if met == "sens" else "Specificity")
ax.set_xticks(x); ax.set_xticklabels(names, fontsize=7); ax.set_ylabel("Percent"); ax.set_ylim(0, 118)
ax.legend(frameon=False, fontsize=7, loc="upper left", ncol=2); plt.tight_layout(); plt.savefig("fig_results.png"); plt.close()
fig, ax = plt.subplots(figsize=(3.4, 3.0), dpi=300)
order = sorted(R["per_activity"], key=lambda a: (-R["per_activity"][a]["fall"], -R["per_activity"][a]["called"]))
val = [100 * R["per_activity"][a]["called"] for a in order]
ax.barh(range(len(order)), val, color=["#4a4a4a" if R["per_activity"][a]["fall"] else "#bdbdbd" for a in order], edgecolor="black", linewidth=0.4)
ax.set_yticks(range(len(order))); ax.set_yticklabels([a.replace("_", " ") for a in order], fontsize=6.5); ax.invert_yaxis(); ax.set_xlim(0, 105)
ax.set_xlabel("Windows called FALL (%)")
ax.legend(handles=[Patch(fc="#4a4a4a", ec="k", label="real falls (want high)"), Patch(fc="#bdbdbd", ec="k", label="not falls (want low)")], frameon=False, fontsize=6.5, loc="lower right")
plt.tight_layout(); plt.savefig("fig_activity.png"); plt.close()
for k in keys + ["gb03"]:
    s = R[k]; print(k, "TP", s["tp"], "FN", s["fn"], "TN", s["tn"], "FP", s["fp"], "sens %.1f spec %.1f" % (100 * s["sens"], 100 * s["spec"]))
