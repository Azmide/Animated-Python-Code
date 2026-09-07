#!/usr/bin/env python3
"""Fireworks - a clickable fireworks show in a pop-up window.

    python3 fireworks.py

Controls
    Click / drag ..... launch a shell at the cursor
    Space ............ finale barrage
    S ................ smiley-face shell (yes, really)
    H ................ heart shell
    A ................ toggle auto-launch
    F ................ fullscreen on/off
    Esc / Q .......... quit

Standard library only: tkinter, math, random. Nothing to install.
"""

import math
import random
import tkinter as tk

WIDTH, HEIGHT = 900, 650
BG = "#05060f"
FRAME_MS = 20          # ~50 fps
GRAVITY = 0.055
ROCKET_GRAVITY = 0.17  # shells climb fast, sparks drift slowly
DRAG = 0.986
SHAPE_DRAG = 0.962     # shaped shells snap open, then hang in the air
TAU = math.pi * 2

PALETTE = [
    "#ff4d4d", "#ff8a2b", "#ffe94d", "#7cff5e", "#4dd2ff",
    "#8a6bff", "#ff5ede", "#ffffff", "#ff9de2", "#5effc2",
]
GOLD = "#ffcc55"

STYLES = ["sphere", "ring", "double", "palm", "willow", "crackle", "heart", "smiley"]


def rgb_of(color):
    return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))


def shade(rgb, k):
    """Dim an (r, g, b) triple toward black and return a #rrggbb string."""
    k = 0.0 if k < 0.0 else (1.0 if k > 1.0 else k)
    return "#%02x%02x%02x" % (int(rgb[0] * k), int(rgb[1] * k), int(rgb[2] * k))


# --- shell shapes: unit vectors the particles fly out along ------------------

def shape_ring(n=68):
    return [(math.cos(TAU * i / n), math.sin(TAU * i / n)) for i in range(n)]


def shape_heart(n=56):
    pts = []
    for i in range(n):
        t = TAU * i / n
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t)
              - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((x / 17.0, y / 17.0))
    return pts


def shape_smiley():
    pts = [(math.cos(TAU * i / 44), math.sin(TAU * i / 44)) for i in range(44)]
    for eye_x in (-0.36, 0.36):          # two eyes
        for k in range(6):
            a = TAU * k / 6
            pts.append((eye_x + 0.10 * math.cos(a), -0.34 + 0.10 * math.sin(a)))
    for i in range(16):                  # the grin (canvas y grows downward)
        t = math.radians(28 + 124 * i / 15.0)
        pts.append((0.62 * math.cos(t), 0.62 * math.sin(t)))
    return pts


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "life0", "rgb", "size", "shrink",
                 "item", "level", "gravity", "drag", "trail", "crackle", "glitter")

    def __init__(self, canvas, x, y, vx, vy, life, color, size=2.5, shrink=1.0,
                 gravity=GRAVITY, drag=DRAG, trail=False, crackle=False, glitter=False):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.life0 = life
        self.rgb = rgb_of(color)
        self.size, self.shrink = size, shrink
        self.gravity, self.drag = gravity, drag
        self.trail, self.crackle, self.glitter = trail, crackle, glitter
        self.level = 12
        self.item = canvas.create_oval(x - size, y - size, x + size, y + size,
                                       fill=color, outline="")

    def step(self, canvas):
        self.vx *= self.drag
        self.vy = self.vy * self.drag + self.gravity
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.shrink != 1.0:
            self.size *= self.shrink
        s = self.size
        canvas.coords(self.item, self.x - s, self.y - s, self.x + s, self.y + s)

        k = self.life / self.life0
        level = int(k * 12)
        if level != self.level or self.glitter:
            self.level = level
            bright = min(1.0, k * 1.6)
            if self.glitter and random.random() < 0.35:
                bright *= 0.25
            canvas.itemconfig(self.item, fill=shade(self.rgb, bright))
        return self.life > 0


class Rocket:
    """A shell climbing to its burst height, trailing sparks."""

    def __init__(self, canvas, x, y, target_x, target_y, style, colors):
        self.x, self.y = x, y
        rise = max(60.0, y - target_y)
        self.vy = -math.sqrt(2 * ROCKET_GRAVITY * rise) * 1.1
        flight = abs(self.vy) / ROCKET_GRAVITY
        self.vx = (target_x - x) / flight
        self.style, self.colors = style, colors
        self.item = canvas.create_oval(x - 2, y - 3, x + 2, y + 3,
                                       fill=GOLD, outline="")

    def step(self, canvas):
        self.vy += ROCKET_GRAVITY
        self.x += self.vx
        self.y += self.vy
        canvas.coords(self.item, self.x - 2, self.y - 3, self.x + 2, self.y + 3)
        return self.vy < -1.0           # still climbing


class Fireworks:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BG,
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.w, self.h = WIDTH, HEIGHT

        self.particles = []
        self.rockets = []
        self.frame = 0
        self.fuse = 25
        self.shells = 0
        self.auto = True
        self.fullscreen = False
        self.drag_cooldown = 0

        self.sky_seed = [(random.random(), random.random(), random.random())
                         for _ in range(90)]
        self.stars = []
        self.hud = self.canvas.create_text(
            14, HEIGHT - 30, anchor="w", fill="#59607d",
            font=("Helvetica", 11),
            text="click: launch    space: finale    s: smiley    h: heart    "
                 "a: auto    f: fullscreen    esc: quit")
        self.counter = self.canvas.create_text(
            WIDTH - 14, 18, anchor="e", fill="#39405c", font=("Helvetica", 11),
            text="0 shells")

        root.bind("<Button-1>", self.on_click)
        root.bind("<B1-Motion>", self.on_drag)
        root.bind("<space>", lambda e: self.finale())
        root.bind("<KeyPress-s>", lambda e: self.launch(style="smiley"))
        root.bind("<KeyPress-h>", lambda e: self.launch(style="heart"))
        root.bind("<KeyPress-a>", lambda e: self.toggle_auto())
        root.bind("<KeyPress-f>", lambda e: self.toggle_fullscreen())
        root.bind("<Escape>", lambda e: root.destroy())
        root.bind("<KeyPress-q>", lambda e: root.destroy())
        self.canvas.focus_set()

        self.redraw_stars()
        self.tick()

    # --- scenery ------------------------------------------------------------

    def redraw_stars(self):
        for item in self.stars:
            self.canvas.delete(item)
        self.stars = [
            self.canvas.create_oval(sx * self.w, sy * self.h * 0.8,
                                    sx * self.w + 1.6, sy * self.h * 0.8 + 1.6,
                                    fill=shade((255, 255, 255), 0.25 + 0.55 * b),
                                    outline="")
            for sx, sy, b in self.sky_seed
        ]

    # --- launching ----------------------------------------------------------

    def launch(self, target_x=None, target_y=None, style=None):
        if target_x is None:
            target_x = random.uniform(0.15, 0.85) * self.w
        if target_y is None:
            target_y = random.uniform(0.22, 0.5) * self.h
        target_y = max(0.2 * self.h, target_y)
        target_x = min(max(target_x, 0.1 * self.w), 0.9 * self.w)
        style = style or random.choice(STYLES)
        colors = random.sample(PALETTE, 2)
        self.rockets.append(Rocket(self.canvas, random.uniform(0.3, 0.7) * self.w,
                                   self.h + 6, target_x, target_y, style, colors))

    def finale(self):
        for _ in range(9):
            self.launch(random.uniform(0.08, 0.92) * self.w,
                        random.uniform(0.08, 0.5) * self.h)

    def on_click(self, event):
        self.launch(event.x, event.y)

    def on_drag(self, event):
        if self.drag_cooldown <= 0:
            self.drag_cooldown = 7
            self.launch(event.x, event.y)

    def toggle_auto(self):
        self.auto = not self.auto

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    # --- explosions ---------------------------------------------------------

    def add(self, x, y, vx, vy, life, color, **kw):
        self.particles.append(Particle(self.canvas, x, y, vx, vy, life, color, **kw))

    def burst(self, x, y, style, colors):
        self.shells += 1
        a_color, b_color = colors
        power = random.uniform(3.4, 4.6)

        # the flash at the moment of detonation
        self.add(x, y, 0, 0, 9, "#ffffff", size=17, shrink=0.74,
                 gravity=0.0, drag=0.86)

        if style in ("ring", "double", "heart", "smiley"):
            reach = 1.25 * (1.0 - SHAPE_DRAG) / SHAPE_DRAG   # speed per pixel of radius
            if style == "ring":
                pts, grav, life, size, radius = shape_ring(), GRAVITY, 78, 2.5, 125
            elif style == "double":
                pts, grav, life, size, radius = shape_ring(52), GRAVITY, 78, 2.5, 125
                for dx, dy in shape_ring(34):
                    sp = 62 * reach
                    self.add(x, y, dx * sp, dy * sp, 66, b_color, size=2.0,
                             drag=SHAPE_DRAG)
            elif style == "heart":
                pts, grav, life, size, radius = shape_heart(), 0.022, 110, 3.0, 130
            else:
                pts, grav, life, size, radius = shape_smiley(), 0.016, 120, 2.8, 135
            for dx, dy in pts:
                sp = radius * reach * random.uniform(0.95, 1.05)
                self.add(x, y, dx * sp, dy * sp, life + random.randint(-6, 6),
                         a_color, size=size, gravity=grav, drag=SHAPE_DRAG)

        elif style == "palm":
            for _ in range(26):
                a = random.uniform(0, TAU)
                sp = power * random.uniform(0.85, 1.2)
                self.add(x, y, math.cos(a) * sp, math.sin(a) * sp,
                         random.randint(80, 105), GOLD, size=3.6,
                         gravity=0.075, trail=True, glitter=True)

        elif style == "willow":
            for _ in range(60):
                a = random.uniform(0, TAU)
                sp = power * 0.65 * math.sqrt(random.random())
                self.add(x, y, math.cos(a) * sp, math.sin(a) * sp,
                         random.randint(110, 150), GOLD, size=2.2,
                         gravity=0.085, drag=0.975, glitter=True)

        elif style == "crackle":
            for _ in range(70):
                a = random.uniform(0, TAU)
                sp = power * math.sqrt(random.random())
                self.add(x, y, math.cos(a) * sp, math.sin(a) * sp,
                         random.randint(55, 80), a_color, size=2.6, crackle=True)

        else:   # sphere
            for _ in range(92):
                a = random.uniform(0, TAU)
                sp = power * math.sqrt(random.random())
                color = a_color if random.random() < 0.7 else b_color
                self.add(x, y, math.cos(a) * sp, math.sin(a) * sp,
                         random.randint(55, 85), color,
                         size=random.uniform(2.0, 3.2))

    # --- main loop ----------------------------------------------------------

    def tick(self):
        self.frame += 1
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w > 1 and (w, h) != (self.w, self.h):
            self.w, self.h = w, h
            self.redraw_stars()
            self.canvas.coords(self.hud, 14, h - 30)
            self.canvas.coords(self.counter, w - 14, 18)

        if self.drag_cooldown > 0:
            self.drag_cooldown -= 1

        if self.auto:
            self.fuse -= 1
            if self.fuse <= 0:
                self.fuse = random.randint(38, 85)
                self.launch()

        still_flying = []
        for rocket in self.rockets:
            if rocket.step(self.canvas) and rocket.y > -20:
                still_flying.append(rocket)
                if self.frame % 2 == 0:
                    self.add(rocket.x, rocket.y, random.uniform(-0.3, 0.3), 0.2,
                             14, GOLD, size=1.6, gravity=0.02)
            else:
                self.canvas.delete(rocket.item)
                self.burst(rocket.x, rocket.y, rocket.style, rocket.colors)
        self.rockets = still_flying

        alive = []
        for p in self.particles:
            if p.step(self.canvas) and p.y < self.h + 40:
                alive.append(p)
                if p.trail and self.frame % 2 == 0:
                    self.add(p.x, p.y, 0, 0.05, 16, GOLD, size=1.4, gravity=0.03)
                elif p.crackle and p.life == 14:
                    for _ in range(6):
                        a = random.uniform(0, TAU)
                        sp = random.uniform(0.4, 1.5)
                        self.add(p.x, p.y, math.cos(a) * sp, math.sin(a) * sp,
                                 12, "#ffffff", size=1.5, gravity=0.02)
            else:
                self.canvas.delete(p.item)
        self.particles = alive

        if self.frame % 15 == 0:
            self.canvas.itemconfig(self.counter, text="%d shells" % self.shells)

        self.root.after(FRAME_MS, self.tick)


def main():
    root = tk.Tk()
    root.title("Fireworks - click anywhere")
    root.configure(bg=BG)
    Fireworks(root)
    root.mainloop()


if __name__ == "__main__":
    main()
