"""Makes the figures and table that show the improvement, from YOUR recordings.
Run:  python make_figures.py         Needs: pip install matplotlib scikit-learn numpy
Outputs (in the folder 'figures'):
  fig1_raw_signals.png      raw examples: a fall vs. confusing normal movements
  fig2_improvement.png      sensitivity / specificity: old rule -> model v1 -> model v2
  fig3_activity.png         which activities are called FALL: old rule vs best model
  fig4_confusion.png        confusion matrices (old rule vs best model)
  improvement_table.csv     the numbers behind the charts
"""
import csv, os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import confusion_matrix
from featlib import features
from featlib2 import features2

D, OUT = "data", "figures"
os.makedirs(OUT, exist_ok=True)
R, X1, X2, y, g, acts, files = [], [], [], [], [], [], []
for r in csv.DictReader(open(os.path.join(D, "labels.csv"))):
    rows = [[float(v) for v in l.split(",")] for l in open(os.path.join(D, r["file"])) if l.strip()]
    R.append(rows); X1.append(features([x[:3] for x in rows])); X2.append(features2(rows))
    y.append(int(r["is_fall"])); g.append(r["subject"]); acts.append(r["activity"]); files.append(r["file"])
X1, X2, y, g, acts = map(np.array, (X1, X2, y, g, acts))
peak = X1[:, 0]

def loso(X, mk):
    p = np.zeros(len(y))
    for tr, te in LeaveOneGroupOut().split(X, y, g):
        p[te] = mk().fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return (p >= 0.5).astype(int)

old = ((peak >= 3.0) & (peak <= 14.0)).astype(int)
v1 = loso(X1, lambda: RandomForestClassifier(n_estimators=15, max_depth=5, min_samples_leaf=2, class_weight="balanced", random_state=1))
v2 = loso(X2, lambda: RandomForestClassifier(n_estimators=200, max_depth=6, min_samples_leaf=2, class_weight="balanced", random_state=1))
stages = [("1. Old rule\n(peak 3-14 g)", old), ("2. Model v1\n(acceleration)", v1), ("3. Model v2\n(+ rotation)", v2)]

def rates(yp):
    tn, fp, fn, tp = confusion_matrix(y, yp, labels=[0, 1]).ravel()
    return tp, fn, tn, fp, tp / (tp + fn), tn / (tn + fp), (tp + tn) / len(y)

with open(os.path.join(OUT, "improvement_table.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["stage", "sensitivity_%", "specificity_%", "accuracy_%", "missed_falls", "false_alarms"])
    for name, yp in stages:
        tp, fn, tn, fp, se, sp, ac = rates(yp)
        w.writerow([name.replace("\n", " "), round(100 * se, 1), round(100 * sp, 1), round(100 * ac, 1), fn, fp])
        print("%-34s sens %5.1f%%  spec %5.1f%%  acc %5.1f%%  missed %d  false alarms %d" % (name.replace("\n", " "), 100 * se, 100 * sp, 100 * ac, fn, fp))

# fig 1: raw signals
def pick(act, want_fall):
    idx = [i for i in range(len(y)) if acts[i] == act and abs(X1[i, 0] - np.median(X1[acts == act, 0])) < 99]
    return idx[0] if idx else None
show = [("fall_backward", "A real fall (backward)"), ("sit_down_fast", "Normal: sitting down fast"),
        ("hit_table", "Normal: hitting a table"), ("walk_arm_swing", "Normal: walking, arm swing")]
fig, ax = plt.subplots(2, 4, figsize=(15, 5.6), sharex=True)
for j, (a, title) in enumerate(show):
    cand = [i for i in range(len(y)) if acts[i] == a]
    if not cand: continue
    i = sorted(cand, key=lambda k: abs(X1[k, 0] - np.median(X1[cand, 0])))[0]
    arr = np.array(R[i]); t = np.arange(len(arr)) / 50.0
    svm = np.sqrt((arr[:, :3] ** 2).sum(1)); gy = np.sqrt((arr[:, 3:6] ** 2).sum(1))
    ax[0, j].plot(t, svm, color="#2b6cb0"); ax[0, j].axhline(1, color="grey", lw=0.6)
    ax[0, j].set_title(title, fontsize=10); ax[1, j].plot(t, gy, color="#c05621")
    ax[1, j].set_xlabel("time (s)")
ax[0, 0].set_ylabel("acceleration (g)"); ax[1, 0].set_ylabel("rotation (deg/s)")
fig.suptitle("Raw wrist-sensor signals: confusing movements can look like falls", fontsize=12)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig1_raw_signals.png"), dpi=140); plt.close()

# fig 2: improvement bars
fig, ax = plt.subplots(figsize=(8, 4.6)); x = np.arange(3); w = 0.36
se = [100 * rates(yp)[4] for _, yp in stages]; sp = [100 * rates(yp)[5] for _, yp in stages]
b1 = ax.bar(x - w / 2, se, w, label="Sensitivity (falls caught)", color="#2b6cb0")
b2 = ax.bar(x + w / 2, sp, w, label="Specificity (normal movements ignored)", color="#38a169")
for b in list(b1) + list(b2): ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1, "%.0f%%" % b.get_height(), ha="center", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels([n for n, _ in stages]); ax.set_ylim(0, 112); ax.set_ylabel("%")
ax.set_title("Improvement on the same data (each test person never seen in training)", fontsize=10)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False, fontsize=9); ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig2_improvement.png"), dpi=140); plt.close()

# fig 3: per activity
names = sorted(set(acts)); isf = [a.startswith("fall_") for a in names]
fo = [100 * old[acts == a].mean() for a in names]; fm = [100 * v2[acts == a].mean() for a in names]
fig, ax = plt.subplots(figsize=(11, 4.8)); x = np.arange(len(names)); w = 0.4
ax.bar(x - w / 2, fo, w, label="Old rule", color="#a0aec0"); ax.bar(x + w / 2, fm, w, label="Model v2", color="#2b6cb0")
ax.set_xticks(x); ax.set_xticklabels([n.replace("_", "\n") for n in names], fontsize=8)
for k, a in enumerate(isf):
    if a: ax.axvspan(k - 0.5, k + 0.5, color="#fde2e2", zorder=0)
ax.set_ylabel("% of windows called FALL"); ax.set_ylim(0, 110); ax.legend(frameon=False)
ax.set_title("Pink = real falls (should be high). Others = normal movements (should be low)", fontsize=10)
ax.spines[["top", "right"]].set_visible(False); plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig3_activity.png"), dpi=140); plt.close()

# fig 4: confusion
fig, axs = plt.subplots(1, 2, figsize=(9, 4))
for a_, (name, yp) in zip(axs, (stages[0], stages[2])):
    cm = confusion_matrix(y, yp, labels=[0, 1]); a_.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2): a_.text(j, i, cm[i, j], ha="center", va="center", fontsize=15, color="white" if cm[i, j] > cm.max() / 2 else "black")
    a_.set_xticks([0, 1]); a_.set_yticks([0, 1]); a_.set_xticklabels(["said not fall", "said FALL"]); a_.set_yticklabels(["really not fall", "really FALL"])
    a_.set_title(name.replace("\n", " "), fontsize=10)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig4_confusion.png"), dpi=140); plt.close()
print("\nSaved the figures in the folder 'figures'")
