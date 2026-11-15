"""Version 2 features: the 10 acceleration features of featlib.py plus rotation (gyro) and
stillness / energy features.  rows = 200 samples of (ax, ay, az, gx, gy, gz)."""
import math
from featlib import features as acc_features

FEATURES2 = ["peak", "peak_pos", "ffmin", "pre_sd", "post_mean_dev", "post_sd", "tilt",
             "n_above2", "max_jerk", "post_range",
             "gyro_peak", "gyro_pre_mean", "gyro_around_peak", "gyro_post_mean",
             "pre_energy", "post_energy", "n_above3", "settle_time", "impact_width", "peak_minus_pre"]


def features2(rows):
    vals = [r[:3] for r in rows]
    base = acc_features(vals)
    n = len(rows)
    svm = [math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) for v in vals]
    gy = [math.sqrt(r[3] * r[3] + r[4] * r[4] + r[5] * r[5]) for r in rows]
    pk = 40
    for i in range(40, min(110, n)):
        if svm[i] > svm[pk]:
            pk = i
    lo, hi = max(0, pk - 20), min(n, pk + 30)
    gyro_peak = max(gy[40:110])
    gyro_pre = sum(gy[0:30]) / 30.0
    gyro_around = sum(gy[lo:hi]) / (hi - lo)
    gyro_post = sum(gy[n - 60:]) / 60.0
    pre_energy = sum(abs(s - 1.0) for s in svm[0:30]) / 30.0
    post_energy = sum(abs(s - 1.0) for s in svm[n - 60:]) / 60.0
    n3 = sum(1 for s in svm if s > 3.0)
    settle = n - pk
    run = 0
    for i in range(pk, n):
        if abs(svm[i] - 1.0) < 0.25:
            run += 1
            if run >= 10:
                settle = i - pk - 9
                break
        else:
            run = 0
    width = sum(1 for i in range(max(0, pk - 40), min(n, pk + 40)) if svm[i] > 1.5)
    pre_mean = sum(svm[0:30]) / 30.0
    return base + [gyro_peak, gyro_pre, gyro_around, gyro_post, pre_energy, post_energy,
                   n3, settle, width, svm[pk] - pre_mean]
