import pathlib
from typing import List, Dict, Optional
import copy
from CTD25.It1_interfaces.img import Img
from CTD25.It1_interfaces.Command import Command
from CTD25.It1_interfaces.Board import Board


class Graphics:
    def __init__(self,
                 sprites_folder: pathlib.Path,
                 board: Board,
                 loop: bool = True,
                 fps: float = 6.0):
        """
        Initialize graphics with sprites folder, cell size, loop setting, and FPS.
        טוען את כל התמונות מהתיקייה (לפי סדר שמות הקבצים).
        """
        self.sprites_folder = sprites_folder
        self.board = board
        self.loop = loop
        self.fps = fps
        self.frame_time_ms = int(1000 / fps)
        self.frames: List[Img] = self._load_frames()
        self.current_frame = 0
        self.last_update = 0
        self.running = True

    def _load_frames(self) -> List[Img]:
        frames = []
        for img_path in sorted(self.sprites_folder.glob("*.png")):
            img = Img()
            img.read(str(img_path), size=(80, 80))  # ודא שזה תואם לגודל התא שלך
            frames.append(img)
        return frames if frames else [Img()]  # לפחות פריים ריק

    def copy(self):
        """Create a shallow copy of the graphics object."""
        new_gfx = Graphics(self.sprites_folder, self.board, self.loop, self.fps)
        new_gfx.current_frame = self.current_frame
        new_gfx.last_update = self.last_update
        new_gfx.running = self.running
        return new_gfx

    def reset(self, cmd: Command = None):
        """Reset the animation with a new command."""
        self.current_frame = 0
        self.last_update = 0
        self.running = True

    def update(self, now_ms: int):
        """Advance animation frame based on game-loop time, not wall time."""
        if not self.running or len(self.frames) == 1:
            return
        if self.last_update == 0:
            self.last_update = now_ms
            return
        if now_ms - self.last_update >= self.frame_time_ms:
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.running = False
            self.last_update = now_ms

    def get_img(self) -> Img:
        """Get the current frame image."""
        return self.frames[self.current_frame]
