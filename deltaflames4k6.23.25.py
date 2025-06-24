#!/usr/bin/env python3
# ===============================================================
#  DELTA ENGINE – Flames Co. Edition
#  Single‑file demo game skeleton for Pygame + Tkinter, 600×400
#  Author:  Cat‑Sama (with a little help from ChatGPT‑o3)
#  License: MIT (code) – you must provide/replace all assets
# ===============================================================

import sys
import json
import pathlib
import pygame as pg
import tkinter as tk
from tkinter import filedialog, messagebox

# ----------------------- CONFIG & CONSTANTS --------------------
WIN_W, WIN_H = 600, 400
FPS       = 60
SAVE_PATH = pathlib.Path("delta_save.json")  # simple JSON save
TITLE     = "DELTA ENGINE – Flames Co. Edition"

# Palette placeholder (RGB tuples)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE= (120,  30, 200)

# ---------------------- SAVE‑FILE UTILITIES --------------------
def load_save():
    if SAVE_PATH.exists():
        try:
            return json.loads(SAVE_PATH.read_text())
        except Exception as e:
            print("Save corrupt:", e)
    return {"chapter": 1, "player": {"x": 50, "y": 50}}

def write_save(data):
    SAVE_PATH.write_text(json.dumps(data, indent=2))

# --------------------------- TK LAUNCHER -----------------------
def run_launcher():
    """
    Tiny Tk window that lets the player launch, toggle flags, etc.
    Keeps the whole engine a single file while providing UI flexibility.
    """
    root = tk.Tk()
    root.title("Delta Engine Launcher")
    root.geometry("240x180")
    tk.Label(root, text="Δ Engine Launcher", font=("Helvetica", 14, "bold")).pack(pady=6)

    state = load_save()

    def play():
        root.destroy()
        DeltaGame(state).run()

    def erase():
        if messagebox.askyesno("Erase Save",
                               "Delete save file and restart from Chapter 1?"):
            state.update({"chapter": 1, "player": {"x": 50, "y": 50}})
            write_save(state)
            messagebox.showinfo("Save Reset", "Save data cleared!")

    tk.Button(root, text="▶ Play (Chapter {})".format(state["chapter"]),
              command=play, width=20).pack(pady=4)
    tk.Button(root, text="🗑 Erase Save", command=erase, width=20).pack(pady=4)
    tk.Button(root, text="📂 Open Save Dir",
              command=lambda: filedialog.askopenfilename(initialdir=".")).pack(pady=4)
    tk.Button(root, text="Quit", command=root.destroy).pack(pady=4)
    root.mainloop()

# --------------------------- CORE ENGINE -----------------------
class SceneBase:
    """Abstract scene: override update, draw, handle_event."""

    def __init__(self, game):
        self.game = game

    def start(self):        pass  # called when scene becomes active
    def stop(self):         pass  # called when scene is exited
    def update(self, dt):   pass
    def draw(self, surf):   pass
    def handle_event(self, ev): pass

# --------------------------- SCENES ----------------------------
class TitleScene(SceneBase):
    def start(self):
        self.timer = 0

    def update(self, dt):
        self.timer += dt
        # auto‑advance to saved chapter after 2 s
        if self.timer > 2000:
            saved_ch = self.game.save["chapter"]
            self.game.change_scene(ChapterScene.make(saved_ch))

    def draw(self, surf):
        surf.fill(BLACK)
        font = self.game.font_large
        text = font.render("Δ ENGINE", True, PURPLE)
        rect = text.get_rect(center=(WIN_W//2, WIN_H//2))
        surf.blit(text, rect)

class ChapterScene(SceneBase):
    """
    Generic chapter template. `chapter_no` chooses logic/graphics.
    Use ChapterScene.make(n) factory to get a subclass instance.
    """

    def __init__(self, game, chapter_no):
        super().__init__(game)
        self.chapter_no = chapter_no
        self.player = pg.Rect(50, 50, 16, 24)
        self.speed  = 120

    # ---------- Factory ----------
    @staticmethod
    def make(ch):
        mapping = {1: ChapterOne, 2: ChapterTwo,
                   3: ChapterThree, 4: ChapterFour}
        return mapping.get(ch, ChapterScene)(game=None, chapter_no=ch)

    # ---------- Scene logic -------
    def start(self):
        self.world_color = (50* self.chapter_no,   # fun placeholder effect
                            20* self.chapter_no,
                            60* self.chapter_no)
    def update(self, dt):
        keys = pg.key.get_pressed()
        if keys[pg.K_ESCAPE]:
            self.game.change_scene(TitleScene(self.game))
        dx = dy = 0
        if keys[pg.K_a]: dx -= self.speed * dt/1000
        if keys[pg.K_d]: dx += self.speed * dt/1000
        if keys[pg.K_w]: dy -= self.speed * dt/1000
        if keys[pg.K_s]: dy += self.speed * dt/1000
        self.player.move_ip(dx, dy)

    def draw(self, surf):
        surf.fill(self.world_color)
        pg.draw.rect(surf, WHITE, self.player)
        txt = self.game.font_small.render(f"Chapter {self.chapter_no}", True, WHITE)
        surf.blit(txt, (4, 4))

    def stop(self):
        # persist minimal position → save file
        self.game.save["chapter"] = self.chapter_no
        self.game.save["player"]["x"] = self.player.x
        self.game.save["player"]["y"] = self.player.y
        write_save(self.game.save)

# ----- Concrete per‑chapter subclasses (extend as desired) -----
class ChapterOne (ChapterScene):  pass
class ChapterTwo (ChapterScene):  pass
class ChapterThree(ChapterScene): pass
class ChapterFour (ChapterScene): pass

# --------------------------- GAME LOOP -------------------------
class DeltaGame:
    def __init__(self, save_data):
        pg.init()
        self.screen = pg.display.set_mode((WIN_W, WIN_H))
        pg.display.set_caption(TITLE)
        self.clock   = pg.time.Clock()
        self.font_small = pg.font.SysFont("consolas", 14)
        self.font_large = pg.font.SysFont("consolas", 48, bold=True)
        self.save = save_data
        self.scene = TitleScene(self)
        self.scene.start()

    # ----- Scene management ------
    def change_scene(self, new_scene):
        self.scene.stop()
        new_scene.game = self        # factory may not have .game yet
        self.scene = new_scene
        self.scene.start()

    # -------- Main loop ----------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)  # milliseconds since last frame
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    running = False
                    break
                self.scene.handle_event(ev)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pg.display.flip()
        pg.quit()

# ----------------------------- MAIN ----------------------------
if __name__ == "__main__":
    # Optional CLI arg “--nosplash” skips Tk launcher (helps during rapid dev)
    if "--nosplash" in sys.argv:
        DeltaGame(load_save()).run()
    else:
        run_launcher()
