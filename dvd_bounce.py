#!/usr/bin/env python3
"""DVD Bounce - the bouncing logo, and the corner hit you have waited your whole life for.

    python3 dvd_bounce.py

Controls
    Click ............ drop another logo where you clicked
    Backspace ........ remove one logo
    Up / Down ........ faster / slower
    C ................ cheat (aim every logo straight at a corner)
    Space ............ pause
    R ................ reset the counters
    F ................ fullscreen on/off
    Esc / Q .......... quit

Standard library only: tkinter, math, random, time. Nothing to install.
"""

import math
import random
import time
import tkinter as tk

WIDTH, HEIGHT = 900, 600
BG = "#0b0b14"
FRAME_MS = 16
LOGO_W, LOGO_H = 132, 74
CORNER_SLOP = 7           # px from a corner that still counts as a corner hit
NEAR_MISS_SLOP = 45

COLORS = [
    "#ff4d6d", "#ffb03b", "#ffe45e", "#8bff6b", "#4cd7ff",
    "#9d7bff", "#ff6bd6", "#ffffff", "#5effc2", "#ff8f5e",
]

BRAGS = [
    "You may now die happy.",
    "Nobody will believe you.",
    "Screenshot it. Nobody will believe you.",
    "That's it. That's the whole game.",
    "Frame it and hang it in a museum.",
    "Your ancestors are proud.",
]


class Logo:
    """One bouncing logo: a few canvas items that travel together."""

    def __init__(self, canvas, x, y, speed):
        self.canvas = canvas
        self.x, self.y = x, y
        angle = random.uniform(0.5, 1.1) * random.choice([1, -1])
        self.vx = speed * math.cos(angle) * random.choice([1, -1])
        self.vy = speed * math.sin(angle)
        self.color = random.choice(COLORS)

        w, h = LOGO_W, LOGO_H
        self.oval = canvas.create_oval(x + 4, y + h * 0.52, x + w - 4, y + h - 2,
                                       outline=self.color, width=3)
        self.word = canvas.create_text(x + w / 2, y + h * 0.31, text="DVD",
                                       fill=self.color, font=("Helvetica", 30, "bold"))
        self.small = canvas.create_text(x + w / 2, y + h * 0.76, text="PYTHON",
                                        fill=self.color, font=("Helvetica", 9, "bold"))
        self.items = (self.oval, self.word, self.small)

    def recolor(self):
        previous = self.color
        while self.color == previous:
            self.color = random.choice(COLORS)
        self.canvas.itemconfig(self.oval, outline=self.color)
        self.canvas.itemconfig(self.word, fill=self.color)
        self.canvas.itemconfig(self.small, fill=self.color)

    def move_to(self, x, y):
        self.canvas.move(self.oval, x - self.x, y - self.y)
        self.canvas.move(self.word, x - self.x, y - self.y)
        self.canvas.move(self.small, x - self.x, y - self.y)
        self.x, self.y = x, y

    def destroy(self):
        for item in self.items:
            self.canvas.delete(item)

    def aim_at_nearest_corner(self, w, h):
        """The cheat: point this logo at whichever corner it can reach."""
        cx = 0 if self.vx < 0 else w - LOGO_W
        cy = 0 if self.vy < 0 else h - LOGO_H
        dx, dy = cx - self.x, cy - self.y
        if dx == 0 and dy == 0:
            return
        speed = math.hypot(self.vx, self.vy)
        length = math.hypot(dx, dy)
        self.vx = speed * dx / length
        self.vy = speed * dy / length


class Confetti:
    __slots__ = ("x", "y", "vx", "vy", "life", "item")

    def __init__(self, canvas, x, y):
        self.x, self.y = x, y
        angle = random.uniform(0, math.tau)
        speed = random.uniform(2, 11)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 3
        self.life = random.randint(45, 90)
        size = random.uniform(2, 5)
        self.item = canvas.create_rectangle(x, y, x + size, y + size * 1.8,
                                            fill=random.choice(COLORS), outline="")

    def step(self, canvas):
        self.vy += 0.22
        self.vx *= 0.99
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        canvas.move(self.item, self.vx, self.vy)
        return self.life > 0


class Screensaver:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BG,
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.w, self.h = WIDTH, HEIGHT

        self.speed = 4.0
        self.paused = False
        self.fullscreen = False
        self.bounces = 0
        self.corners = 0
        self.near_misses = 0
        self.started = time.time()
        self.shout = None
        self.shout_ttl = 0
        self.confetti = []
        self.logos = [Logo(self.canvas, WIDTH / 2, HEIGHT / 2, self.speed)]

        self.stats = self.canvas.create_text(14, 14, anchor="nw", fill="#565f80",
                                             font=("Helvetica", 12), justify="left")
        self.hint = self.canvas.create_text(
            14, HEIGHT - 26, anchor="w", fill="#3c4360", font=("Helvetica", 10),
            text="click: another logo    backspace: remove    up/down: speed    "
                 "c: cheat    space: pause    r: reset    f: fullscreen    esc: quit")

        root.bind("<Button-1>", self.on_click)
        root.bind("<BackSpace>", lambda e: self.remove_logo())
        root.bind("<Up>", lambda e: self.change_speed(1.25))
        root.bind("<Down>", lambda e: self.change_speed(0.8))
        root.bind("<KeyPress-c>", lambda e: self.cheat())
        root.bind("<space>", lambda e: self.toggle_pause())
        root.bind("<KeyPress-r>", lambda e: self.reset())
        root.bind("<KeyPress-f>", lambda e: self.toggle_fullscreen())
        root.bind("<Escape>", lambda e: root.destroy())
        root.bind("<KeyPress-q>", lambda e: root.destroy())
        self.canvas.focus_set()

        self.tick()

    # --- input --------------------------------------------------------------

    def on_click(self, event):
        if len(self.logos) < 24:
            x = min(max(event.x - LOGO_W / 2, 0), self.w - LOGO_W)
            y = min(max(event.y - LOGO_H / 2, 0), self.h - LOGO_H)
            self.logos.append(Logo(self.canvas, x, y, self.speed))

    def remove_logo(self):
        if len(self.logos) > 1:
            self.logos.pop().destroy()

    def change_speed(self, factor):
        self.speed = min(22.0, max(0.6, self.speed * factor))
        for logo in self.logos:
            current = math.hypot(logo.vx, logo.vy) or 1.0
            logo.vx *= self.speed / current
            logo.vy *= self.speed / current

    def cheat(self):
        for logo in self.logos:
            logo.aim_at_nearest_corner(self.w, self.h)
        self.say("cheating is fine, nobody is watching", "#7f88b0")

    def toggle_pause(self):
        self.paused = not self.paused

    def reset(self):
        self.bounces = self.corners = self.near_misses = 0
        self.started = time.time()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    # --- celebration --------------------------------------------------------

    def say(self, text, color, size=16, ttl=110):
        if self.shout is not None:
            self.canvas.delete(self.shout)
        self.shout = self.canvas.create_text(self.w / 2, self.h * 0.2, text=text,
                                             fill=color, font=("Helvetica", size, "bold"))
        self.shout_ttl = ttl
        self.canvas.tag_raise(self.shout)

    def celebrate(self, x, y):
        self.corners += 1
        self.say("CORNER HIT #%d\n%s" % (self.corners, random.choice(BRAGS)),
                 "#ffe45e", size=30, ttl=200)
        for _ in range(160):
            self.confetti.append(Confetti(self.canvas, x, y))
        self.canvas.configure(bg="#2a2352")
        self.root.after(70, lambda: self.canvas.configure(bg=BG))

    # --- physics ------------------------------------------------------------

    def bounce(self, logo):
        """Move one logo, reflect it off the walls, notice corners."""
        x = logo.x + logo.vx
        y = logo.y + logo.vy
        hit_x = hit_y = False

        if x <= 0:
            x, logo.vx, hit_x = 0, -logo.vx, True
        elif x >= self.w - LOGO_W:
            x, logo.vx, hit_x = self.w - LOGO_W, -logo.vx, True
        if y <= 0:
            y, logo.vy, hit_y = 0, -logo.vy, True
        elif y >= self.h - LOGO_H:
            y, logo.vy, hit_y = self.h - LOGO_H, -logo.vy, True

        logo.move_to(x, y)
        if not (hit_x or hit_y):
            return

        self.bounces += 1
        logo.recolor()

        gap_x = min(x, self.w - LOGO_W - x)
        gap_y = min(y, self.h - LOGO_H - y)
        if (hit_x and hit_y) or max(gap_x, gap_y) <= CORNER_SLOP:
            self.celebrate(x + LOGO_W / 2, y + LOGO_H / 2)
        elif max(gap_x, gap_y) <= NEAR_MISS_SLOP:
            self.near_misses += 1
            self.say("SO CLOSE (%d px)" % int(max(gap_x, gap_y)), "#ff8f5e", size=18, ttl=70)

    # --- main loop ----------------------------------------------------------

    def tick(self):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w > 1 and (w, h) != (self.w, self.h):
            self.w, self.h = w, h
            self.canvas.coords(self.hint, 14, h - 26)
            for logo in self.logos:
                logo.move_to(min(logo.x, w - LOGO_W), min(logo.y, h - LOGO_H))

        if not self.paused:
            for logo in self.logos:
                self.bounce(logo)

        alive = []
        for bit in self.confetti:
            if bit.step(self.canvas) and bit.y < self.h + 30:
                alive.append(bit)
            else:
                self.canvas.delete(bit.item)
        self.confetti = alive

        if self.shout_ttl > 0:
            self.shout_ttl -= 1
            self.canvas.coords(self.shout, self.w / 2, self.h * 0.2)
            if self.shout_ttl == 0:
                self.canvas.delete(self.shout)
                self.shout = None

        wasted = int(time.time() - self.started)
        self.canvas.itemconfig(self.stats, text=(
            "bounces: %d\ncorner hits: %d\nnear misses: %d\nlife wasted: %02d:%02d%s"
            % (self.bounces, self.corners, self.near_misses,
               wasted // 60, wasted % 60, "   (PAUSED)" if self.paused else "")))

        self.root.after(FRAME_MS, self.tick)


def main():
    root = tk.Tk()
    root.title("DVD Bounce - waiting for the corner")
    root.configure(bg=BG)
    Screensaver(root)
    root.mainloop()


if __name__ == "__main__":
    main()
