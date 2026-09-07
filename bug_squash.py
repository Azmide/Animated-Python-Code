#!/usr/bin/env python3
"""Bug Squash - the bugs escaped the codebase and are now on your screen.

    python3 bug_squash.py

Controls
    Click ............ squash a bug (missing makes them panic)
    Space ............ bug spray, area of effect, long cooldown
    B ................ summon more bugs, for people who like problems
    R ................ fresh start, clean screen
    F ................ fullscreen on/off
    Esc / Q .......... quit

Standard library only: tkinter, math, random. Nothing to install.
"""

import math
import random
import tkinter as tk

WIDTH, HEIGHT = 900, 620
BG = "#efe7d3"
FRAME_MS = 28
TAU = math.pi * 2
INK = "#241f1c"
MAX_BUGS = 34
SPRAY_COOLDOWN = 500          # frames

BUG_COLORS = ["#4b3621", "#6b3f2a", "#2f4f4f", "#5c4033", "#3d3b30", "#704214"]
SPLAT_WORDS = ["SPLAT!", "SQUISH!", "BONK!", "OOF!", "YIKES!", "POP!", "GOTCHA!"]
MISS_WORDS = ["MISS!", "TOO SLOW!", "HA!", "NICE TRY", "SWING AND A MISS"]
GOO = ["#7f9b3f", "#8fae4a", "#6e8836", "#a3bd63"]


def rotated_text(canvas, x, y, **kwargs):
    """create_text with a random tilt, falling back on ancient Tk."""
    angle = random.uniform(-22, 22)
    try:
        return canvas.create_text(x, y, angle=angle, **kwargs)
    except tk.TclError:
        return canvas.create_text(x, y, **kwargs)


class Bug:
    """A beetle drawn from a polygon body, a head, six legs and two antennae."""

    def __init__(self, canvas, x, y, boss=False):
        self.canvas = canvas
        self.x, self.y = x, y
        self.boss = boss
        self.scale = 1.9 if boss else random.uniform(0.75, 1.15)
        self.hp = 3 if boss else 1
        self.angle = random.uniform(0, TAU)
        self.speed = random.uniform(1.0, 2.2) * (0.85 if boss else 1.0)
        self.base_speed = self.speed
        self.phase = random.uniform(0, TAU)
        self.scare = 0
        self.pause = 0
        self.color = "#5b2c6f" if boss else random.choice(BUG_COLORS)

        s = self.scale
        self.body = canvas.create_polygon(*([0, 0] * 12), fill=self.color,
                                          outline=INK, width=1.4, smooth=True)
        self.head = canvas.create_oval(0, 0, 0, 0, fill=self.color, outline=INK)
        width = max(1, int(1.6 * s))
        self.legs = [canvas.create_line(0, 0, 0, 0, 0, 0, fill=INK, width=width)
                     for _ in range(6)]
        self.antennae = [canvas.create_line(0, 0, 0, 0, fill=INK, width=1)
                         for _ in range(2)]
        self.seam = canvas.create_line(0, 0, 0, 0, fill="#12100e", width=width)
        self.eyes = [canvas.create_oval(0, 0, 0, 0, fill="#f5f0e6", outline="")
                     for _ in range(2)]
        self.crown = canvas.create_text(0, 0, text="BOSS", fill="#c0392b",
                                        font=("Helvetica", 9, "bold")) if boss else None
        self.parts = ([self.body, self.head, self.seam]
                      + self.legs + self.antennae + self.eyes)
        if self.crown:
            self.parts.append(self.crown)

    # --- geometry -----------------------------------------------------------

    def local_to_world(self, lx, ly):
        cos_a, sin_a = math.cos(self.angle), math.sin(self.angle)
        s = self.scale
        return (self.x + (lx * cos_a - ly * sin_a) * s,
                self.y + (lx * sin_a + ly * cos_a) * s)

    def draw(self):
        points = []
        for i in range(12):
            t = TAU * i / 12
            points.extend(self.local_to_world(-2 + 12 * math.cos(t), 8 * math.sin(t)))
        self.canvas.coords(self.body, *points)

        hx, hy = self.local_to_world(12, 0)
        r = 5.5 * self.scale
        self.canvas.coords(self.head, hx - r, hy - r, hx + r, hy + r)

        er = 1.4 * self.scale
        for i, side in enumerate((1, -1)):
            ex, ey = self.local_to_world(14, 2.6 * side)
            self.canvas.coords(self.eyes[i], ex - er, ey - er, ex + er, ey + er)

        sx1, sy1 = self.local_to_world(8, 0)
        sx2, sy2 = self.local_to_world(-13, 0)
        self.canvas.coords(self.seam, sx1, sy1, sx2, sy2)

        for i, (lx, side) in enumerate([(6, 1), (0, 1), (-6, 1),
                                        (6, -1), (0, -1), (-6, -1)]):
            wiggle = math.sin(self.phase + i * 1.7) * 4.5
            x1, y1 = self.local_to_world(lx, 4 * side)
            kx, ky = self.local_to_world(lx + wiggle * 0.6 + 3 * side, 12 * side)
            x2, y2 = self.local_to_world(lx + wiggle, 19 * side)
            self.canvas.coords(self.legs[i], x1, y1, kx, ky, x2, y2)

        for i, side in enumerate((1, -1)):
            wiggle = math.sin(self.phase * 0.7 + i) * 2.5
            x1, y1 = self.local_to_world(13, 2.5 * side)
            x2, y2 = self.local_to_world(21 + wiggle, 8 * side)
            self.canvas.coords(self.antennae[i], x1, y1, x2, y2)

        if self.crown:
            cx, cy = self.local_to_world(0, -16)
            self.canvas.coords(self.crown, cx, cy)

    # --- behaviour ----------------------------------------------------------

    def update(self, w, h, mouse):
        self.phase += 0.45 + self.speed * 0.2

        if self.pause > 0:                      # a bug, thinking
            self.pause -= 1
            self.draw()
            return

        if self.scare > 0:
            self.scare -= 1
            self.speed = self.base_speed * 2.6
        else:
            self.speed = self.base_speed

        mx, my = mouse
        dx, dy = self.x - mx, self.y - my
        distance = math.hypot(dx, dy)
        if distance < 90:                       # the hand is coming, run
            flee = math.atan2(dy, dx)
            self.angle += math.atan2(math.sin(flee - self.angle),
                                     math.cos(flee - self.angle)) * 0.28
            self.speed *= 1.75
        elif random.random() < 0.05:
            self.angle += random.uniform(-0.5, 0.5)
        elif random.random() < 0.004:
            self.pause = random.randint(8, 30)

        margin = 26
        if self.x < margin or self.x > w - margin or self.y < margin or self.y > h - margin:
            home = math.atan2(h / 2 - self.y, w / 2 - self.x)
            self.angle += math.atan2(math.sin(home - self.angle),
                                     math.cos(home - self.angle)) * 0.25

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.x = min(max(self.x, 12), w - 12)
        self.y = min(max(self.y, 12), h - 12)
        self.draw()

    def hit_by(self, x, y):
        return math.hypot(self.x - x, self.y - y) < 23 * self.scale

    def destroy(self):
        for part in self.parts:
            self.canvas.delete(part)


class Popup:
    """A short-lived word or fading mark."""

    __slots__ = ("item", "life", "life0", "canvas", "rise")

    def __init__(self, canvas, item, life, rise=0.0):
        self.canvas, self.item, self.life, self.life0 = canvas, item, life, life
        self.rise = rise

    def step(self):
        self.life -= 1
        if self.rise:
            self.canvas.move(self.item, 0, self.rise)
        if self.life <= 0:
            self.canvas.delete(self.item)
            return False
        return True


class BugSquash:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BG,
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.w, self.h = WIDTH, HEIGHT
        self.mouse = (WIDTH / 2, -500)
        self.fullscreen = False

        self.bugs = []
        self.popups = []
        self.splats = []
        self.squashed = 0
        self.missed = 0
        self.spray = 0
        self.frame = 0
        self.spawn_timer = 60
        self.boss_at = 12

        self.stats = self.canvas.create_text(14, 12, anchor="nw", fill="#6b5f4f",
                                             font=("Helvetica", 12), justify="left")
        self.hint = self.canvas.create_text(
            14, HEIGHT - 20, anchor="w", fill="#a3937c", font=("Helvetica", 10),
            text="click: squash    space: bug spray    b: more bugs    "
                 "r: restart    f: fullscreen    esc: quit")
        self.banner = None

        root.bind("<Button-1>", self.on_click)
        root.bind("<Motion>", self.on_motion)
        root.bind("<space>", lambda e: self.use_spray())
        root.bind("<KeyPress-b>", lambda e: [self.spawn() for _ in range(5)])
        root.bind("<KeyPress-r>", lambda e: self.reset())
        root.bind("<KeyPress-f>", lambda e: self.toggle_fullscreen())
        root.bind("<Escape>", lambda e: root.destroy())
        root.bind("<KeyPress-q>", lambda e: root.destroy())
        self.canvas.focus_set()

        for _ in range(4):
            self.spawn()
        self.tick()

    # --- world --------------------------------------------------------------

    def spawn(self, boss=False):
        if len(self.bugs) >= MAX_BUGS:
            return
        edge = random.randrange(4)
        if edge == 0:
            x, y = random.uniform(0, self.w), 14
        elif edge == 1:
            x, y = random.uniform(0, self.w), self.h - 14
        elif edge == 2:
            x, y = 14, random.uniform(0, self.h)
        else:
            x, y = self.w - 14, random.uniform(0, self.h)
        self.bugs.append(Bug(self.canvas, x, y, boss=boss))

    def reset(self):
        for bug in self.bugs:
            bug.destroy()
        for popup in self.popups:
            self.canvas.delete(popup.item)
        for splat in self.splats:
            self.canvas.delete(splat)
        self.bugs, self.popups, self.splats = [], [], []
        self.squashed = self.missed = 0
        self.spray = 0
        self.spawn_timer = 60
        self.boss_at = 12
        self.clear_banner()
        for _ in range(4):
            self.spawn()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    # --- squashing ----------------------------------------------------------

    def word(self, x, y, text, color, size=17):
        item = rotated_text(self.canvas, x, y, text=text, fill=color,
                            font=("Helvetica", size, "bold"))
        self.popups.append(Popup(self.canvas, item, 34, rise=-1.1))

    def splat(self, x, y, scale):
        for _ in range(int(7 * scale)):
            radius = random.uniform(3, 9) * scale
            ox = x + random.uniform(-12, 12) * scale
            oy = y + random.uniform(-12, 12) * scale
            self.splats.append(self.canvas.create_oval(
                ox - radius, oy - radius, ox + radius, oy + radius,
                fill=random.choice(GOO), outline=""))
        while len(self.splats) > 220:            # keep the mess bounded
            self.canvas.delete(self.splats.pop(0))
        for item in self.splats[-int(7 * scale):]:
            self.canvas.tag_lower(item)

    def kill(self, bug):
        self.splat(bug.x, bug.y, bug.scale)
        bug.destroy()
        self.bugs.remove(bug)
        self.squashed += 1
        if bug.boss:
            self.word(bug.x, bug.y - 26, "BOSS DOWN!", "#c0392b", size=24)

    def on_click(self, event):
        for bug in sorted(self.bugs, key=lambda b: math.hypot(b.x - event.x,
                                                              b.y - event.y)):
            if bug.hit_by(event.x, event.y):
                bug.hp -= 1
                if bug.hp <= 0:
                    self.word(bug.x, bug.y - 18, random.choice(SPLAT_WORDS), "#2d572c")
                    self.kill(bug)
                else:
                    bug.base_speed *= 1.35
                    bug.scare = 60
                    self.word(bug.x, bug.y - 30, "%d HP LEFT" % bug.hp, "#c0392b", 14)
                return
        self.missed += 1
        self.word(event.x, event.y - 12, random.choice(MISS_WORDS), "#b07d3a", 15)
        for bug in self.bugs:                    # they saw that
            bug.scare = 45
        if self.missed % 3 == 0:
            self.spawn()

    def use_spray(self):
        if self.spray > 0:
            self.word(self.w / 2, self.h / 2, "SPRAY EMPTY (%ds)"
                      % (self.spray * FRAME_MS // 1000), "#8a7b5f", 18)
            return
        self.spray = SPRAY_COOLDOWN
        mx, my = self.mouse
        for _ in range(90):
            angle, radius = random.uniform(0, TAU), random.uniform(0, 190)
            px = mx + math.cos(angle) * radius
            py = my + math.sin(angle) * radius
            dot = self.canvas.create_oval(px - 3, py - 3, px + 3, py + 3,
                                          fill="#a9d5c1", outline="")
            self.popups.append(Popup(self.canvas, dot, random.randint(12, 30),
                                     rise=random.uniform(-1.5, 0.4)))
        for bug in list(self.bugs):
            if math.hypot(bug.x - mx, bug.y - my) < 190:
                self.kill(bug)
        self.word(mx, my - 40, "PSSSSHT", "#3d7a63", 22)

    def on_motion(self, event):
        self.mouse = (event.x, event.y)

    # --- banner -------------------------------------------------------------

    def clear_banner(self):
        if self.banner is not None:
            for item in self.banner:
                self.canvas.delete(item)
            self.banner = None

    def show_banner(self):
        if self.banner is not None:
            return
        self.banner = [
            self.canvas.create_rectangle(0, self.h / 2 - 60, self.w, self.h / 2 + 60,
                                         fill="#2b2119", outline=""),
            self.canvas.create_text(self.w / 2, self.h / 2 - 16,
                                    text="THE BUGS HAVE WON", fill="#ffd479",
                                    font=("Helvetica", 34, "bold")),
            self.canvas.create_text(self.w / 2, self.h / 2 + 24,
                                    text="ship it anyway   -   press R to try again",
                                    fill="#e8dcc0", font=("Helvetica", 14)),
        ]

    # --- main loop ----------------------------------------------------------

    def tick(self):
        self.frame += 1
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w > 1 and (w, h) != (self.w, self.h):
            self.w, self.h = w, h
            self.canvas.coords(self.hint, 14, h - 20)

        if self.spray > 0:
            self.spray -= 1

        infested = len(self.bugs) >= MAX_BUGS
        if infested:
            self.show_banner()
        else:
            self.clear_banner()
            self.spawn_timer -= 1
            if self.spawn_timer <= 0:
                self.spawn_timer = max(35, 130 - self.squashed * 3)
                self.spawn()
            if self.squashed >= self.boss_at:
                self.boss_at += 15
                self.spawn(boss=True)

        for bug in self.bugs:
            bug.update(self.w, self.h, self.mouse)

        self.popups = [p for p in self.popups if p.step()]

        accuracy = 100.0 * self.squashed / max(1, self.squashed + self.missed)
        self.canvas.itemconfig(self.stats, text=(
            "squashed: %d\nmissed: %d\naccuracy: %d%%\non screen: %d\nspray: %s"
            % (self.squashed, self.missed, accuracy, len(self.bugs),
               "ready" if self.spray == 0 else "%ds" % (self.spray * FRAME_MS // 1000))))
        self.canvas.tag_raise(self.stats)
        self.canvas.tag_raise(self.hint)

        self.root.after(FRAME_MS, self.tick)


def main():
    root = tk.Tk()
    root.title("Bug Squash - they are in the build again")
    root.configure(bg=BG)
    BugSquash(root)
    root.mainloop()


if __name__ == "__main__":
    main()
