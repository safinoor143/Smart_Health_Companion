# Smart Health Companion

A low-cost wrist-worn **fall detector** (ESP32 + MPU6050) and a multi-user **care website** (Flask + SQLite) for elderly people and their caregivers. When a fall is detected the wearer gets 15 seconds to press a cancel button; if they do not, the caregiver is alerted on the website and on Telegram. The website also handles medicine reminders, vital signs, routines and appointments.

> **Status: student prototype / pilot study.** It is not a medical device. The fall data were simulated by four volunteers, so the detection results below are preliminary.

## What is in this repository

| Folder | Contents |
|---|---|
| `website/` | Flask website: accounts (patient / caregiver), reminders, vitals, routines, appointments, fall alerts, Telegram alerts and a health assistant chatbot (`chat.py`) |
| `firmware/` | MicroPython code for the ESP32 (`main.py` = normal use, `main_collect.py` = data recording, `main_ml.py` = learned model) |
| `ml/` | Scripts for recording, cleaning, training and evaluating the fall classifier |
| `data/` | `fall_recordings.zip`: 254 labelled 4-second wrist recordings (`s1`..`s4`) with `labels.csv`. **Unzip it into this folder before running the ML scripts.** |
| `docs/` | Architecture and wiring pictures |

## Hardware

- ESP32 DevKit (30-pin) running MicroPython
- MPU6050 accelerometer/gyroscope (I2C, address 0x68)
- Low-trigger buzzer module, push button, on-board blue LED
- 3.7 V 1500 mAh Li-ion battery, TP4056 charger, MT3608 boost converter set to 5.0 V (feeds VIN)

| From | To (ESP32) |
|---|---|
| MPU6050 VCC and buzzer VCC | 3V3 |
| MPU6050 GND and buzzer GND | GND |
| MPU6050 SDA / SCL | GPIO21 / GPIO22 |
| Buzzer IN | GPIO25 |
| Cancel button | GPIO27 and GPIO14 |
| MT3608 5.0 V output | VIN |

Never connect USB while the battery chain feeds VIN. Pictures are in `docs/`.

## Run the website

```
pip install -r requirements.txt
cd website
python app.py
```

Open http://127.0.0.1:5000, create a patient and a caregiver account, and open the **Device** tab to get the patient's device token.

**Telegram (optional):** create a bot with BotFather and put its token in a file called `telegram.token` next to `app.py`, or set `TELEGRAM_BOT_TOKEN`. Never commit this file (it is in `.gitignore`).

**Health assistant (optional):** `chat.py` adds a chat tab that answers questions about the user's reminders and falls from their own records, and general health questions through the Groq API. Put a free Groq key in a file called `groq.key` next to `app.py`, or set `GROQ_API_KEY`. Without a key the tab still answers reminder and fall questions. It refuses to give doses or diagnoses and points to 112 in an emergency. Never commit `groq.key` (it is in `.gitignore`).

## Put the program on the ESP32

1. Install MicroPython on the ESP32 and open the board in Thonny.
2. Open `firmware/main.py` and set `SSID`, `PASSWORD` (2.4 GHz hotspot), `LAPTOP_IP` (the IPv4 address of the computer running `app.py`, from `ipconfig`) and `LAPTOP_TOKEN` (from the website's Device tab). Keep `MODE = "run"`.
3. Save it **on the board** as `main.py` (File > Save as > MicroPython device).
4. Put the laptop and the board on the same hotspot, start `app.py`, then power the board.

`MODE = "collect"` is only for recording data over USB and does nothing on battery.

## Detection method

Windows of 200 samples (4 s at 50 Hz, ±8 g, 44 Hz low-pass) are saved when the acceleration exceeds 1.8 g.

* **Baseline rule:** a peak between 3 g and 14 g is a fall.
* **Learned classifier:** 20 features from the accelerometer and gyroscope fed to a gradient-boosting model (`ml/train2.py`). A Random Forest on the 10 acceleration features can be exported as plain if/else code for the board (`ml/train.py` writes `fallmodel.py`).

## Pilot results

254 recordings (82 simulated falls, 172 daily activities) from four volunteers wearing the device on the left wrist. Each classifier was tested leave-one-volunteer-out (trained on three people, tested on the fourth).

| Method | Sensitivity (95% CI) | Specificity (95% CI) |
|---|---|---|
| Impact rule, 3-14 g | 87% (78-92) | 22% (17-29) |
| Random Forest, acceleration features | 76% (65-84) | 78% (72-84) |
| Gradient boosting, acceleration + gyroscope | 76% (65-84) | 93% (88-96) |

Reproduce: unzip `data/fall_recordings.zip` into the `data/` folder, then run `cd ml && python final_analysis.py`.

## Limitations

- Only four volunteers, all simulated falls on a soft mat; no older adults.
- Left wrist only. Windows were recorded only after the 1.8 g trigger, so false alarms per day are not measured.
- The learned model was evaluated offline; it is not yet running on the board.
- Alert latency and battery life are not yet measured.

## Ethics

Volunteers took part voluntarily, with a mat and supervision, and are identified only as `s1`..`s4`. <!-- confirm consent covers sharing the recordings -->

## Licence

MIT, see `LICENSE`.
