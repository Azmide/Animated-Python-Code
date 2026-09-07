# Animated-Python-Code

Five little pop-up animations written in plain Python. Every one of them opens
its own window, animates until you close it, and reacts to your mouse and
keyboard. One file per animation, no dependencies beyond the standard library.

```bash
python3 fireworks.py
```

That's it. No `pip install`, no virtualenv, no build step.

## What's in the box

| File | What happens |
| --- | --- |
| [`fireworks.py`](fireworks.py) | A night sky with shells that climb, arc and burst. Eight shell types including rings, willows, hearts and a smiley face. Click anywhere to aim one. |
| [`dvd_bounce.py`](dvd_bounce.py) | The bouncing logo. Counts bounces, near misses and the seconds of your life spent watching. When it finally hits a corner, you get confetti and a diploma. There is also a cheat key, for the impatient. |
| [`matrix_rain.py`](matrix_rain.py) | Green digital rain that swallows your keystrokes: type a line, press Enter, and watch it fall down a column. Click to punch a glitch into the code. |
| [`bug_squash.py`](bug_squash.py) | The bugs got out of the codebase. They scatter when your cursor gets close, they multiply when you miss, and eventually a boss bug shows up. There is bug spray. |
| [`flying_toasters.py`](flying_toasters.py) | Chrome toasters flapping across a starfield, exactly as 1991 intended. Click one to pop its toast. There is a burnt mode; it was a mistake. |

## Controls

Each file lists its own keys in its docstring, and every window prints the
hints along the bottom edge. The shared ones:

* **Click** — the main interaction in all five
* **Space** — the big one: finale, bug spray, toaster storm
* **F** (F1 in the Matrix) — fullscreen
* **Esc** / **Q** — quit

## Requirements

Python 3.8 or newer with `tkinter`, which ships with Python on Windows and
macOS. On Debian/Ubuntu it is a separate package:

```bash
sudo apt install python3-tk
```

Check with `python3 -c "import tkinter"` — silence means you're good.

## Notes

Everything is drawn with a plain `tkinter.Canvas`: ovals, polygons and lines,
moved a few pixels per frame by `after()` callbacks. No sprites, no images, no
game engine. Each script is self-contained and readable top to bottom, so they
double as examples if you want to build your own.
