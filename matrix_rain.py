#!/usr/bin/env python3
"""Matrix Rain - digital rain that eats whatever you type.

    python3 matrix_rain.py

Controls
    Type anything .... your letters fall into the rain
    Enter ............ send the whole line down a column (empty line = a classic)
    Backspace ........ fix your typo before the machines see it
    Click ............ punch a glitch into the code
    F1 ............... fullscreen on/off
    F2 ............... change the phosphor colour
    F3 ............... heavier rain
    Esc .............. unplug

Standard library only: tkinter, random. Nothing to install.
"""

import random
import tkinter as tk

WIDTH, HEIGHT = 900, 640
BG = "#020604"
FRAME_MS = 33                 # ~30 fps
CELL_W, CELL_H = 16, 20
FONT = ("Courier", 15, "bold")

GLYPHS = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
          "@#$%&*+=-<>[]{}()/\\|!?;:^~"
          "ΛΦΨΩΣΔΞΘΠΓαβγδεζηθλμξπστφχψω")

PHOSPHORS = [
    ((60, 255, 110), "#d8ffe4"),    # classic green
    ((255, 176, 40), "#fff0cf"),    # amber terminal
    ((90, 190, 255), "#dff0ff"),    # blue pill
    ((255, 90, 200), "#ffdcf3"),    # ...the other pill
]

CLASSICS = [
    "WAKE UP NEO", "FOLLOW THE WHITE RABBIT", "KNOCK KNOCK",
    "THERE IS NO SPOON", "THE CAKE IS A LIE", "HELLO WORLD",
    "SUDO MAKE ME A SANDWICH", "IT IS 3 AM GO TO BED",
]


def shade(rgb, k):
    k = 0.0 if k < 0.0 else (1.0 if k > 1.0 else k)
    return "#%02x%02x%02x" % (int(rgb[0] * k), int(rgb[1] * k), int(rgb[2] * k))


class Column:
    """One vertical stream. Its glyphs are recycled, never recreated."""

    def __init__(self, canvas, index, rows):
        self.canvas = canvas
        self.x = index * CELL_W + CELL_W / 2
        self.length = random.randint(9, 26)
        self.items = [canvas.create_text(self.x, -100, text=" ", font=FONT,
                                         fill="#000000", anchor="c")
                      for _ in range(self.length)]
        self.message = None
        self.reset(rows, first=True)

    def reset(self, rows, first=False):
        self.head = -random.randint(0, rows)
        self.speed = random.randint(1, 4)      # frames between steps
        self.wait = random.randint(0, 4)
        self.message = None
        if not first:
            for item in self.items:
                self.canvas.coords(item, self.x, -100)

    def send(self, text):
        """Drop a typed line down this column, one glyph per row."""
        self.message = list(text)
        self.head = -1
        self.speed = 3
        self.wait = 0
        for item in self.items:
            self.canvas.coords(item, self.x, -100)

    def advance(self, rows, gradient, hot_gradient):
        self.wait -= 1
        if self.wait > 0:
            return
        self.wait = self.speed
        self.head += 1

        item = self.items.pop()            # the tail glyph becomes the new head
        self.items.insert(0, item)
        if self.message is not None:
            glyph = self.message.pop(0) if self.message else random.choice(GLYPHS)
            if not self.message:
                self.message = None
        else:
            glyph = random.choice(GLYPHS)
        self.canvas.itemconfig(item, text=glyph)
        self.canvas.coords(item, self.x, self.head * CELL_H + CELL_H / 2)

        ramp = hot_gradient if self.message is not None else gradient
        for i, glyph_item in enumerate(self.items):
            self.canvas.itemconfig(glyph_item, fill=ramp[i])

        if self.head - self.length > rows:
            self.reset(rows)

    def flicker(self):
        if self.items:
            self.canvas.itemconfig(random.choice(self.items),
                                   text=random.choice(GLYPHS))

    def destroy(self):
        for item in self.items:
            self.canvas.delete(item)


class MatrixRain:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BG,
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.w, self.h = WIDTH, HEIGHT
        self.rows = HEIGHT // CELL_H

        self.phosphor = 0
        self.heavy = False
        self.fullscreen = False
        self.typed = ""
        self.blink = 0
        self.columns = []
        self.build_columns()

        self.prompt = self.canvas.create_text(14, HEIGHT - 18, anchor="w",
                                              fill="#7dffb0", font=("Courier", 13, "bold"))
        self.hint = self.canvas.create_text(
            WIDTH - 14, HEIGHT - 18, anchor="e", fill="#1f5a35", font=("Courier", 10),
            text="type + enter    click: glitch    f1 full    f2 colour    f3 rain    esc: out")

        root.bind("<KeyPress>", self.on_key)
        root.bind("<Button-1>", self.on_click)
        root.bind("<F1>", lambda e: self.toggle_fullscreen())
        root.bind("<F2>", lambda e: self.cycle_phosphor())
        root.bind("<F3>", lambda e: self.toggle_heavy())
        root.bind("<Escape>", lambda e: root.destroy())
        self.canvas.focus_set()

        self.tick()

    # --- setup --------------------------------------------------------------

    def gradients(self, length):
        base, head = PHOSPHORS[self.phosphor]
        ramp = [head] + [shade(base, (1.0 - i / length) ** 1.7)
                         for i in range(1, length)]
        hot = ["#ffffff"] + [shade(tuple(min(255, c + 90) for c in base),
                                   (1.0 - i / length) ** 0.9) for i in range(1, length)]
        return ramp, hot

    def build_columns(self):
        for column in self.columns:
            column.destroy()
        count = max(1, self.w // CELL_W)
        self.rows = max(1, self.h // CELL_H)
        self.columns = [Column(self.canvas, i, self.rows) for i in range(count)]
        self.ramps = {}

    def ramp_for(self, length):
        if length not in self.ramps:
            self.ramps[length] = self.gradients(length)
        return self.ramps[length]

    # --- input --------------------------------------------------------------

    def on_key(self, event):
        if event.keysym == "Return":
            text = self.typed.strip() or random.choice(CLASSICS)
            random.choice(self.columns).send(text.upper())
            self.typed = ""
        elif event.keysym == "BackSpace":
            self.typed = self.typed[:-1]
        elif event.char and event.char.isprintable():
            self.typed = (self.typed + event.char)[-46:]
            # every keystroke also rains down somewhere
            column = random.choice(self.columns)
            if column.message is None:
                column.send(event.char.upper())

    def on_click(self, event):
        """A glitch: nearby columns restart from the cursor."""
        centre = int(event.x // CELL_W)
        row = int(event.y // CELL_H)
        for offset in range(-6, 7):
            index = centre + offset
            if 0 <= index < len(self.columns):
                column = self.columns[index]
                column.reset(self.rows)
                column.head = row - abs(offset)
                column.speed = 1

    def cycle_phosphor(self):
        self.phosphor = (self.phosphor + 1) % len(PHOSPHORS)
        self.ramps = {}
        self.canvas.itemconfig(self.prompt, fill=PHOSPHORS[self.phosphor][1])

    def toggle_heavy(self):
        self.heavy = not self.heavy
        for column in self.columns:
            column.speed = 1 if self.heavy else random.randint(1, 4)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    # --- main loop ----------------------------------------------------------

    def tick(self):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w > 1 and (w, h) != (self.w, self.h):
            self.w, self.h = w, h
            self.build_columns()
            self.canvas.coords(self.prompt, 14, h - 18)
            self.canvas.coords(self.hint, w - 14, h - 18)
            self.canvas.tag_raise(self.prompt)
            self.canvas.tag_raise(self.hint)

        for column in self.columns:
            ramp, hot = self.ramp_for(column.length)
            column.advance(self.rows, ramp, hot)

        for _ in range(6):
            random.choice(self.columns).flicker()

        self.blink = (self.blink + 1) % 20
        self.canvas.itemconfig(
            self.prompt,
            text="> " + self.typed + ("_" if self.blink < 12 else " "))

        self.root.after(FRAME_MS, self.tick)


def main():
    root = tk.Tk()
    root.title("Matrix Rain - type something")
    root.configure(bg=BG)
    MatrixRain(root)
    root.mainloop()


if __name__ == "__main__":
    main()
