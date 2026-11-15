"""Features used BOTH on the laptop (training) and on the ESP32 (running).
Pure Python, no numpy, so the same code runs in MicroPython.
vals = list of (ax, ay, az) in g, 200 samples at 50 Hz, trigger near index 50."""
import math

FEATURES = ["peak", "peak_pos", "ffmin", "pre_sd", "post_mean_dev", "post_sd",
            "tilt", "n_above2", "max_jerk", "post_range"]


def features(vals):
    n = len(vals)
    svm = [math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) for v in vals]
    pk = 40
    for i in range(40, min(110, n)):
        if svm[i] > svm[pk]:
            pk = i
    peak = svm[pk]
    lo = max(0, pk - 25)
    ffmin = min(svm[lo:pk]) if pk > lo else 1.0
    pre = svm[0:30]
    pm = sum(pre) / len(pre)
    pre_sd = math.sqrt(sum((v - pm) * (v - pm) for v in pre) / len(pre))
    s0 = min(pk + 40, n - 40)
    post = svm[s0:]
    m = sum(post) / len(post)
    post_sd = math.sqrt(sum((v - m) * (v - m) for v in post) / len(post))
    post_range = max(post) - min(post)

    def avg(a, b):
        sx = sy = sz = 0.0
        for i in range(a, b):
            sx += vals[i][0]
            sy += vals[i][1]
            sz += vals[i][2]
        k = b - a
        return sx / k, sy / k, sz / k

    gb = avg(0, 30)
    ga = avg(s0, n)
    nb = math.sqrt(gb[0] ** 2 + gb[1] ** 2 + gb[2] ** 2)
    na = math.sqrt(ga[0] ** 2 + ga[1] ** 2 + ga[2] ** 2)
    if nb < 0.3 or na < 0.3:
        tilt = 0.0
    else:
        c = (gb[0] * ga[0] + gb[1] * ga[1] + gb[2] * ga[2]) / (nb * na)
        c = max(-1.0, min(1.0, c))
        tilt = math.acos(c) * 57.2958
    n_above2 = 0
    max_jerk = 0.0
    for i in range(1, n):
        if svm[i] > 2.0:
            n_above2 += 1
        d = svm[i] - svm[i - 1]
        if d < 0:
            d = -d
        if d > max_jerk:
            max_jerk = d
    return [peak, pk - 50, ffmin, pre_sd, abs(m - 1.0), post_sd, tilt,
            n_above2, max_jerk, post_range]
