import pathlib
from typing import List, Dict, Optional
import copy
from img import Img
from Command import Command
from Board import Board


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
        
        # שמור את תיקיית המצבים לשינוי sprites
        self.piece_states_dir = sprites_folder.parent.parent  # מ-idle/sprites ל-states
        
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

    def switch_to_state(self, state_name: str):
        """החלף לאנימציה של מצב ספציפי"""
        folder_map = {
            "idle": "idle",
            "move": "move", 
            "jump": "jump",
            "short_rest": "short_rest",
            "long_rest": "long_rest"
        }
        
        folder_name = folder_map.get(state_name, "idle")
        new_sprites_dir = self.piece_states_dir / folder_name / "sprites"
        config_path = self.piece_states_dir / folder_name / "config.json"
        
        # דיבוג רק לקפיצה
        if state_name == "jump":
            print(f"🎬 Starting JUMP animation: {folder_name}")
        
        if new_sprites_dir.exists():
            # קרא את הקונפיגורציה של המצב החדש
            graphics_cfg = {}
            if config_path.exists():
                import json
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        full_cfg = json.load(f)
                        graphics_cfg = full_cfg.get("graphics", {})
                except:
                    pass
            
            # עדכן fps ו-loop מהקונפיגורציה החדשה
            new_fps = graphics_cfg.get("frames_per_sec", self.fps)
            new_loop = graphics_cfg.get("is_loop", self.loop)
            
            self.fps = new_fps
            self.loop = new_loop
            self.frame_time_ms = int(1000 / new_fps)
            
            self.sprites_folder = new_sprites_dir
            self.frames = self._load_frames()
            self.current_frame = 0
            self.last_update = 0
            self.running = True

    def update(self, now_ms: int):
        """Advance animation frame based on game-loop time, not wall time."""
        if not self.running or len(self.frames) <= 1:
            return
        if self.last_update == 0:
            self.last_update = now_ms
            return
        if now_ms - self.last_update >= self.frame_time_ms:
            # דיבוג רק לקפיצה
            state_name = self.sprites_folder.parent.name if self.sprites_folder.parent else "unknown"
            if state_name == "jump":
                print(f"🎞️ JUMP frame: {self.current_frame}/{len(self.frames)} (fps={self.fps})")
            
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                    if state_name == "jump":
                        print(f"🔄 JUMP loop reset")
                else:
                    self.current_frame = len(self.frames) - 1
                    self.running = False
                    if state_name == "jump":
                        print(f"⏹️ JUMP finished")
            self.last_update = now_ms

    def get_img(self) -> Img:
        """Get the current frame image."""
        return self.frames[self.current_frame]
