#!/usr/bin/env python3
"""Flying Toasters - the 1991 screensaver, rebuilt in tkinter, now with breakfast.

    python3 flying_toasters.py

Controls
    Click a toaster .. pop its toast
    Click the sky .... release another toaster
    Space ............ TOASTER STORM
    T ................ make it rain toast
    B ................ burnt mode (regrettable)
    Up / Down ........ faster / slower
    F ................ fullscreen on/off
    Esc / Q .......... quit

Standard library only: tkinter, math, random. Nothing to install.
"""

import math
import random
import tkinter as tk

WIDTH, HEIGHT = 900, 620
BG = "#10102e"
FRAME_MS = 22
TAU = math.pi * 2

CHROME = "#d8dbe6"
CHROME_DARK = "#8f93a8"
GOLD = "#ffd35c"
BREAD = "#e8bd7a"
CRUST = "#a9702f"
BURNT = "#3a2c22"

POPS = ["POP!", "DING!", "BREAKFAST!", "TOAST!", "SPROING!", "BRUNCH!"]


def rounded_rect(x0, y0, x1, y1, r):
    return [x0 + r, y0, x1 - r, y0, x1, y0 + r, x1, y1 - r,
            x1 - r, y1, x0 + r, y1, x0, y1 - r, x0, y0 + r]


class Toast:
    """A slice, tumbling gently through the void."""

    SHAPE = [(-17, -3), (-16, -11), (-11, -18), (-4, -17), (0, -12),
             (4, -17), (11, -18), (16, -11), (17, -3), (17, 19), (-17, 19)]

    def __init__(self, canvas, x, y, vx, vy, burnt=False, scale=1.0):
        self.canvas = canvas
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.scale = scale
        self.angle = random.uniform(0, TAU)
        self.spin = random.uniform(-0.05, 0.05)
        fill = BURNT if burnt else BREAD
        outline = "#241a12" if burnt else CRUST
        self.item = canvas.create_polygon(*([0, 0] * len(self.SHAPE)),
                                          fill=fill, outline=outline, width=2)
        self.butter = canvas.create_polygon(*([0, 0] * 4),
                                            fill="#fff3c4" if not burnt else "#6b5a3e",
                                            outline="", smooth=True)
        self.draw()

    def draw(self):
        cos_a, sin_a = math.cos(self.angle), math.sin(self.angle)
        s = self.scale
        points = []
        for lx, ly in self.SHAPE:
            points.append(self.x + (lx * cos_a - ly * sin_a) * s)
            points.append(self.y + (lx * sin_a + ly * cos_a) * s)
        self.canvas.coords(self.item, *points)
        pat = []
        for lx, ly in ((-6, -2), (5, -4), (7, 5), (-4, 6)):     # a melting pat
            pat.append(self.x + (lx * cos_a - ly * sin_a) * s)
            pat.append(self.y + (lx * sin_a + ly * cos_a) * s)
        self.canvas.coords(self.butter, *pat)

    def step(self, gravity=0.06):
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy
        self.angle += self.spin
        self.draw()

    def destroy(self):
        self.canvas.delete(self.item)
        self.canvas.delete(self.butter)


class Toaster:
    """Chrome, two slots, and a pair of wings it absolutely should not have."""

    def __init__(self, canvas, x, y, scale, speed, golden=False):
        self.canvas = canvas
        self.x, self.y = x, y
        self.scale = scale
        self.golden = golden
        self.vx = -speed
        self.vy = speed * 0.55
        self.phase = random.uniform(0, TAU)
        self.flap_rate = random.uniform(0.18, 0.30)
        self.tag = "toaster%d" % id(self)

        s = scale
        body = GOLD if golden else CHROME
        w, h = 66 * s, 46 * s
        self.w, self.h = w, h
        self.wings = [canvas.create_polygon(*([0, 0] * 6), fill="#eef1f9",
                                            outline=CHROME_DARK, width=2,
                                            tags=(self.tag,)) for _ in range(2)]
        self.body = canvas.create_polygon(*rounded_rect(x, y, x + w, y + h, 9 * s),
                                          fill=body, outline=CHROME_DARK, width=2,
                                          smooth=True, tags=(self.tag,))
        self.slot = canvas.create_polygon(
            *rounded_rect(x + 10 * s, y + 7 * s, x + w - 16 * s, y + 14 * s, 3 * s),
            fill="#2b2b3d", outline="", smooth=True, tags=(self.tag,))
        self.shine = canvas.create_line(x + 12 * s, y + 22 * s, x + 12 * s, y + h - 10 * s,
                                        fill="#ffffff", width=max(1, int(2 * s)),
                                        tags=(self.tag,))
        self.lever = canvas.create_line(x + w - 8 * s, y + 20 * s,
                                        x + w - 8 * s, y + 30 * s,
                                        fill=CHROME_DARK, width=max(2, int(3 * s)),
                                        tags=(self.tag,))
        self.knob = canvas.create_oval(x + w - 12 * s, y + 28 * s,
                                       x + w - 4 * s, y + 36 * s,
                                       fill="#e05c3e", outline=CHROME_DARK,
                                       tags=(self.tag,))
        self.flap()

    def flap(self):
        """Two feathered wings sweeping off the back of the toaster."""
        s = self.scale
        root_x = self.x + self.w - 8 * s
        for i, wing in enumerate(self.wings):
            lift = math.sin(self.phase + i * 0.6) * 20 * s
            base_y = self.y + (10 + 20 * i) * s
            tip_y = base_y - 12 * s - lift
            self.canvas.coords(
                wing,
                root_x, base_y,
                root_x + 16 * s, tip_y - 4 * s,
                root_x + 34 * s, tip_y,
                root_x + 30 * s, tip_y + 8 * s,
                root_x + 38 * s, tip_y + 9 * s,
                root_x + 10 * s, base_y + 10 * s)

    def step(self, wind):
        self.phase += self.flap_rate
        dx, dy = self.vx * wind, self.vy * wind
        self.x += dx
        self.y += dy
        self.canvas.move(self.tag, dx, dy)
        self.flap()

    def contains(self, px, py):
        return (self.x - 6 <= px <= self.x + self.w + 30 * self.scale
                and self.y - 10 <= py <= self.y + self.h + 10)

    def slot_mouth(self):
        return self.x + self.w / 2 - 3 * self.scale, self.y + 6 * self.scale

    def destroy(self):
        self.canvas.delete(self.tag)


class Kitchen:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BG,
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.w, self.h = WIDTH, HEIGHT

        self.toasters = []
        self.toast = []
        self.popups = []
        self.wind = 1.0
        self.burnt = False
        self.served = 0
        self.fullscreen = False
        self.frame = 0

        self.stars = []
        self.star_seed = [(random.random(), random.random(), random.random())
                          for _ in range(70)]
        self.draw_stars()

        self.stats = self.canvas.create_text(14, 14, anchor="nw", fill="#6f74a8",
                                             font=("Helvetica", 12), justify="left")
        self.hint = self.canvas.create_text(
            14, HEIGHT - 20, anchor="w", fill="#454a78", font=("Helvetica", 10),
            text="click a toaster: pop toast    click the sky: more toasters    "
                 "space: storm    t: toast rain    b: burnt    esc: quit")

        for _ in range(7):
            self.spawn_toaster(edge=True)

        root.bind("<Button-1>", self.on_click)
        root.bind("<space>", lambda e: [self.spawn_toaster(edge=True) for _ in range(12)])
        root.bind("<KeyPress-t>", lambda e: self.toast_rain())
        root.bind("<KeyPress-b>", lambda e: self.toggle_burnt())
        root.bind("<Up>", lambda e: self.change_wind(1.3))
        root.bind("<Down>", lambda e: self.change_wind(0.75))
        root.bind("<KeyPress-f>", lambda e: self.toggle_fullscreen())
        root.bind("<Escape>", lambda e: root.destroy())
        root.bind("<KeyPress-q>", lambda e: root.destroy())
        self.canvas.focus_set()

        self.tick()

    # --- scenery ------------------------------------------------------------

    def draw_stars(self):
        for star in self.stars:
            self.canvas.delete(star)
        self.stars = []
        for sx, sy, b in self.star_seed:
            x, y = sx * self.w, sy * self.h
            grey = int(90 + 130 * b)
            self.stars.append(self.canvas.create_oval(
                x, y, x + 1.8, y + 1.8, outline="",
                fill="#%02x%02x%02x" % (grey, grey, min(255, grey + 25))))

    # --- population ---------------------------------------------------------

    def spawn_toaster(self, x=None, y=None, edge=False):
        if len(self.toasters) > 60:
            return
        scale = random.uniform(0.65, 1.3)
        speed = (0.9 + scale * 1.9) * random.uniform(0.85, 1.15)
        golden = random.random() < 0.04
        if edge or x is None:
            if random.random() < 0.5:
                x, y = random.uniform(0, self.w), -70
            else:
                x, y = self.w + random.uniform(0, 260), random.uniform(-60, self.h * 0.7)
        self.toasters.append(Toaster(self.canvas, x, y, scale, speed, golden))

    def toast_rain(self):
        for _ in range(12):
            self.toast.append(Toast(self.canvas, random.uniform(0, self.w), -30,
                                    random.uniform(-1.5, 0.5), random.uniform(0, 2),
                                    burnt=self.burnt, scale=random.uniform(0.8, 1.3)))

    def pop(self, toaster):
        x, y = toaster.slot_mouth()
        for _ in range(2):
            self.toast.append(Toast(self.canvas, x, y,
                                    random.uniform(-1.6, 0.4), random.uniform(-8, -5.5),
                                    burnt=self.burnt, scale=toaster.scale))
        self.served += 2
        word = "GOLDEN TOAST!" if toaster.golden else random.choice(POPS)
        colour = GOLD if toaster.golden else "#ffe9a8"
        item = self.canvas.create_text(x, y - 26, text=word, fill=colour,
                                       font=("Helvetica", 16, "bold"))
        self.popups.append([item, 40])
        if self.burnt:
            for _ in range(10):
                puff = self.canvas.create_oval(x - 6, y - 6, x + 6, y + 6,
                                               fill="#4a4a63", outline="")
                self.canvas.move(puff, random.uniform(-14, 14), random.uniform(-24, 4))
                self.popups.append([puff, random.randint(14, 34)])

    # --- input --------------------------------------------------------------

    def on_click(self, event):
        for toaster in reversed(self.toasters):
            if toaster.contains(event.x, event.y):
                self.pop(toaster)
                return
        self.spawn_toaster(event.x - 30, event.y - 20)

    def toggle_burnt(self):
        self.burnt = not self.burnt

    def change_wind(self, factor):
        self.wind = min(4.0, max(0.25, self.wind * factor))

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    # --- main loop ----------------------------------------------------------

    def tick(self):
        self.frame += 1
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w > 1 and (w, h) != (self.w, self.h):
            self.w, self.h = w, h
            self.draw_stars()
            self.canvas.coords(self.hint, 14, h - 20)

        if self.frame % 55 == 0 and len(self.toasters) < 14:
            self.spawn_toaster(edge=True)

        for toaster in list(self.toasters):
            toaster.step(self.wind)
            if toaster.x + toaster.w < -60 or toaster.y > self.h + 80:
                toaster.destroy()
                self.toasters.remove(toaster)
                if len(self.toasters) < 9:
                    self.spawn_toaster(edge=True)

        for slice_ in list(self.toast):
            slice_.step()
            if slice_.y > self.h + 60 or slice_.x < -60:
                slice_.destroy()
                self.toast.remove(slice_)

        for popup in list(self.popups):
            popup[1] -= 1
            self.canvas.move(popup[0], 0, -0.8)
            if popup[1] <= 0:
                self.canvas.delete(popup[0])
                self.popups.remove(popup)

        self.canvas.itemconfig(self.stats, text=(
            "toasters aloft: %d\nslices served: %d\nwind: x%.1f%s"
            % (len(self.toasters), self.served, self.wind,
               "\nmode: BURNT" if self.burnt else "")))
        self.canvas.tag_raise(self.stats)
        self.canvas.tag_raise(self.hint)

        self.root.after(FRAME_MS, self.tick)


def main():
    root = tk.Tk()
    root.title("Flying Toasters - breakfast is airborne")
    root.configure(bg=BG)
    Kitchen(root)
    root.mainloop()


if __name__ == "__main__":
    main()
