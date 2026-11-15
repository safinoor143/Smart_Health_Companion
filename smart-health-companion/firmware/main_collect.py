from machine import Pin, I2C
import time, struct, network, json, gc, math, sys, socket, ssl

from machine import Pin as _P
_P(25, _P.OUT).value(1)   # keep the low-trigger buzzer silent from the very start
time.sleep(3)   # gives you 3 s to press Ctrl+C after a reset

# ---------------- SETTINGS ----------------
MODE = "collect"
# MODE options: "test" = decide on the board and print; "collect" = send windows to the laptop over USB; "run" = normal use over Wi-Fi
SSID = "YOUR_HOTSPOT_NAME"
PASSWORD = "YOUR_WIFI_PASSWORD"          # hotspot password (2.4 GHz)

# The board sends falls to the website running on your laptop (python app.py).
LAPTOP_IP    = "192.168.0.100"   # <-- IPv4 of the computer running app.py (run ipconfig)
LAPTOP_TOKEN = "PASTE_DEVICE_TOKEN_HERE"   # <-- shown on the website, Device tab

PRE, POST, TRIGGER_G, CANCEL_S = 50, 150, 1.8, 15

USE_ML = False        # True = use the trained model (needs fallmodel.py on the board)
ML_THRESHOLD = 0.5     # model probability needed to call a fall (raise = fewer false alarms)
FALL_MIN_G = 3.0       # a hit of at least this many g counts as a fall ...
FALL_MAX_G = 14.0      # ... up to this many g
EXTRA_CHECKS = False   # True = a fall must ALSO have a free-fall dip, a tilt and lie still
FREEFALL_G = 0.3       # (only used when EXTRA_CHECKS = True)
TILT_DEG = 25
STILL_STD = 0.15

# Pins (see the wiring diagram)
MPU_POWER_PIN = None   # MPU6050 VCC is on the 3V3 pin. (Use 19 only if VCC is wired to GPIO19.)
BUZZER_PIN = 25        # buzzer module signal pin
BUZZER_ACTIVE_LOW = True    # your buzzer module is low-level trigger (beeps when the pin is LOW)
BTN_PIN = 27           # push button leg 1
BTN_GND_PIN = 14       # push button leg 2 (the code drives it LOW)
# ------------------------------------------

SERVERS = [{"name": "laptop", "host": LAPTOP_IP, "port": 5000, "https": False,
            "token": LAPTOP_TOKEN, "timeout": 8, "tries": 3}]

led = Pin(2, Pin.OUT)                    # onboard LED
boot_btn = Pin(0, Pin.IN, Pin.PULL_UP)   # BOOT button (pressed = 0)
btn = Pin(BTN_PIN, Pin.IN, Pin.PULL_UP)  # external cancel button (pressed = 0)
btn_gnd = Pin(BTN_GND_PIN, Pin.OUT)
btn_gnd.value(0)

buzzer = Pin(BUZZER_PIN, Pin.OUT)


def buzz(on):
    buzzer.value((0 if on else 1) if BUZZER_ACTIVE_LOW else (1 if on else 0))


buzz(False)

if MPU_POWER_PIN is not None:
    mpu_pwr = Pin(MPU_POWER_PIN, Pin.OUT)
    mpu_pwr.value(1)
    time.sleep_ms(200)

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
i2c.writeto_mem(0x68, 0x6B, b'\x00')     # wake the MPU6050
i2c.writeto_mem(0x68, 0x1C, b'\x10')     # accelerometer range +-8 g
i2c.writeto_mem(0x68, 0x1B, b'\x10')     # gyroscope range +-1000 deg/s
i2c.writeto_mem(0x68, 0x1A, b'\x03')     # low-pass filter (about 44 Hz)
ASCALE = 4096.0
GSCALE = 32.8

FMT = "[%.3f,%.3f,%.3f,%.1f,%.1f,%.1f]"


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        # reset the radio first: avoids "Wifi Internal State Error" after a failed attempt
        wlan.active(False)
        time.sleep_ms(300)
        wlan.active(True)
        time.sleep_ms(300)
        try:
            wlan.disconnect()
        except Exception:
            pass
        print("Connecting to Wi-Fi", SSID, "...")
        wlan.connect(SSID, PASSWORD)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > 20000:
                raise RuntimeError("Wi-Fi failed: check name, password, 2.4 GHz hotspot")
            led.value(not led.value())
            time.sleep_ms(250)
    led.value(0)
    return wlan


def tls_wrap(s, host):
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.verify_mode = ssl.CERT_NONE
        return ctx.wrap_socket(s, server_hostname=host)
    except AttributeError:
        return ssl.wrap_socket(s, server_hostname=host)


def http(srv, method, path, obj=None):
    """Send one request to one server. Returns the reply (bytes)."""
    data = json.dumps(obj).encode() if obj is not None else b""
    addr = socket.getaddrinfo(srv["host"], srv["port"])[0][-1]
    s = socket.socket()
    s.settimeout(srv["timeout"])
    resp = b""
    try:
        s.connect(addr)
        if srv["https"]:
            s = tls_wrap(s, srv["host"])
        head = ("%s %s HTTP/1.0\r\nHost: %s\r\n"
                "Content-Type: application/json\r\n"
                "Content-Length: %d\r\nConnection: close\r\n\r\n"
                % (method, path, srv["host"], len(data)))
        s.write(head.encode() + data)
        try:
            while True:
                chunk = s.read(512)
                if not chunk:
                    break
                resp += chunk
        except OSError:
            pass          # timeout or closed after we already got the reply
    finally:
        s.close()
    return resp


def api_post(srv, path, obj=None):
    """POST with the server's token. Returns the reply as a dict (or None)."""
    sep = "&" if "?" in path else "?"
    resp = http(srv, "POST", path + sep + "token=" + srv["token"], obj if obj is not None else {})
    print("[%s] HTTP reply starts:" % srv["name"], resp[:30])
    i = resp.find(b"{")
    j = resp.rfind(b"}")
    if i < 0 or j < i:
        return None
    return json.loads(resp[i:j + 1])


def cancel_pressed():
    return boot_btn.value() == 0 or btn.value() == 0


nxt = time.ticks_ms()


def sample():
    """Wait for the next 20 ms slot (50 Hz), then read the sensor."""
    global nxt
    nxt = time.ticks_add(nxt, 20)
    wait = time.ticks_diff(nxt, time.ticks_ms())
    if wait > 0:
        time.sleep_ms(wait)
    else:
        nxt = time.ticks_ms()
    d = i2c.readfrom_mem(0x68, 0x3B, 14)
    ax, ay, az, t, gx, gy, gz = struct.unpack('>hhhhhhh', d)
    return (ax / ASCALE, ay / ASCALE, az / ASCALE, gx / GSCALE, gy / GSCALE, gz / GSCALE)


def judge_rule(vals):
    """Old rule: decide on the board whether a 200-sample window is a fall."""
    n = len(vals)
    svm = [math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) for v in vals]
    pk = 40
    for i in range(40, min(110, n)):
        if svm[i] > svm[pk]:
            pk = i
    peak = svm[pk]
    lo = max(0, pk - 25)
    ffmin = min(svm[lo:pk]) if pk > lo else 1.0
    s0 = min(pk + 40, n - 40)
    post = svm[s0:]
    m = sum(post) / len(post)
    sd = math.sqrt(sum((v - m) * (v - m) for v in post) / len(post))

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

    in_range = FALL_MIN_G <= peak <= FALL_MAX_G
    fall = in_range
    if EXTRA_CHECKS:
        still = (sd < STILL_STD) and (abs(m - 1.0) < 0.2)
        fall = in_range and still and tilt >= TILT_DEG and ffmin < FREEFALL_G

    if fall:
        why = "FALL"
    elif peak < FALL_MIN_G:
        why = "normal: hit under %.1f g" % FALL_MIN_G
    elif peak > FALL_MAX_G:
        why = "normal: hit over %.1f g" % FALL_MAX_G
    else:
        why = "normal: failed the extra checks"
    return fall, peak, ffmin, sd, tilt, why





# ---------------- LEARNED MODEL (Random Forest exported by train.py) ----------------
try:
    import fallmodel
except ImportError:
    fallmodel = None


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


def judge(vals):
    """Use the trained model if fallmodel.py is on the board, else the old rule."""
    fall, peak, ffmin, sd, tilt, why = judge_rule(vals)
    if USE_ML and fallmodel is not None:
        p = fallmodel.fall_probability(features(vals))
        fall = p >= ML_THRESHOLD
        why = "FALL" if fall else "normal"
        why += " (model p=%.2f)" % p
    return fall, peak, ffmin, sd, tilt, why


# ---------------- START ----------------
if MODE == "run":
    while True:
        try:
            wlan = connect_wifi()
            break
        except Exception as e:
            print("Wi-Fi retry:", e)
            time.sleep(3)
    print("Wi-Fi connected. Board IP:", wlan.ifconfig()[0])
    # ---- startup self-test: which servers can this board reach? ----
    for srv in SERVERS:
        print("Self-test:", srv["name"], srv["host"], "...")
        try:
            r = http(srv, "GET", "/")
            print("  answered:", r[:15])
        except Exception as e:
            print("  NOT reachable:", e)
    gc.collect()
elif MODE == "collect":
    print("COLLECT mode: windows are sent to the laptop over USB")
else:
    print("TEST mode: the board decides and prints the verdict (no Wi-Fi)")
print("Monitoring... (Ctrl+C to stop)")

ring = [""] * PRE
rnum = [None] * PRE
idx = 0
count = 0

while True:
    s = sample()
    ring[idx] = FMT % s
    rnum[idx] = s[:3]
    idx = (idx + 1) % PRE
    if count < PRE:
        count += 1

    if count >= PRE and (s[0] ** 2 + s[1] ** 2 + s[2] ** 2) ** 0.5 > TRIGGER_G:
        led.value(1)
        win = ring[idx:] + ring[:idx]          # oldest to newest
        vals = rnum[idx:] + rnum[:idx]
        for _ in range(POST):
            s2 = sample()
            win.append(FMT % s2)
            vals.append(s2[:3])
        led.value(0)

        fall, peak, ffmin, sd, tilt, why = judge(vals)
        vals = None

        if MODE == "collect":
            print("WINDOW_START")
            for row in win:
                print(row[1:-1])
            print("WINDOW_END")
        print("peak=%.1fg  freefall_min=%.2fg  still_sd=%.2f  tilt=%d deg  ->  %s"
              % (peak, ffmin, sd, tilt, why))

        if MODE == "test":
            if fall:
                for _ in range(3):
                    led.value(1)
                    buzz(True)
                    time.sleep_ms(150)
                    led.value(0)
                    buzz(False)
                    time.sleep_ms(150)
        elif MODE == "run":
            if fall:
                win = None
                gc.collect()
                t_fall = time.ticks_ms()       # the cancel time counts from the moment of the fall

                # 1) tell the laptop website about the fall
                eid = None
                used = None
                for srv in SERVERS:
                    for attempt in range(srv["tries"]):
                        try:
                            connect_wifi()
                            print("Sending fall to %s (try %d of %d)..." % (srv["name"], attempt + 1, srv["tries"]))
                            r = api_post(srv, "/api/fall", {"peak": round(peak, 1)})
                            print("Website replied:", r)
                            if r is not None and "id" in r:
                                eid = r["id"]
                                used = srv
                                break
                            print("Server refused:", r)
                        except Exception as e:
                            print("Server error:")
                            sys.print_exception(e)
                        time.sleep(2)
                    if eid is not None:
                        break
                gc.collect()

                # 2) beep and give the patient time to cancel
                if eid is not None:
                    print("Fall %d sent to %s. Press the button within %d s to cancel." % (eid, used["name"], CANCEL_S))
                    cancelled = False
                    end = time.ticks_add(t_fall, CANCEL_S * 1000)
                    while time.ticks_diff(end, time.ticks_ms()) > 0:
                        on = not led.value()
                        led.value(on)
                        buzz(on)
                        if cancel_pressed():
                            cancelled = True
                            break
                        time.sleep_ms(100)
                    led.value(0)
                    buzz(False)

                    # 3) cancel or confirm on the same website that got the fall
                    try:
                        if cancelled:
                            api_post(used, "/api/cancel/%d" % eid)
                            print("Alert cancelled by user.")
                        else:
                            api_post(used, "/api/confirm/%d" % eid)
                            print("ALERT SENT to caregiver.")
                    except Exception as e:
                        print("Could not update the server:", e)
                else:
                    print("Could not reach any website - fall NOT sent.")
                    for _ in range(3):          # warn the patient locally
                        buzz(True)
                        time.sleep_ms(300)
                        buzz(False)
                        time.sleep_ms(300)

        win = None
        gc.collect()
        time.sleep(2)
        ring = [""] * PRE
        rnum = [None] * PRE
        idx = 0
        count = 0
        nxt = time.ticks_ms()
