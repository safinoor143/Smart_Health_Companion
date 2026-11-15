# Data recording protocol (about 20 min per volunteer)

Safety: soft mat or bed, adult volunteers only, written consent, stop any time. No elderly volunteers.
Device: the finished wrist unit, same strap tightness for everyone. Note left/right wrist.

Each volunteer (S1, S2, ...), minimum 5 volunteers:
| Group | Activity (key in collect3.py) | Repeats |
|---|---|---|
| Falls | forward (1), backward (2), side left (3), side right (4), slump from sitting (5) | 5 each = 25 |
| Not falls | walking with arm swing (6), wave/clap (7), hit table (8), sit down fast (9), jump (10), stumble without falling (11), put down object (12), stairs (13), lie down slowly (14) | 5 each = 45 |

About 70 windows per volunteer, 350 for five volunteers. Use different people for training and testing:
train.py always tests on a volunteer it did not train on (leave-one-subject-out).
Only movements above 1.8 g make the board send a window, so do them firmly like a real activity.
