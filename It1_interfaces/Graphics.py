import pathlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
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
        """Initialize graphics with sprites folder, cell size, loop setting, and FPS."""
        pass

    def copy(self):
        """Create a shallow copy of the graphics object."""
        pass

    def reset(self, cmd: Command):
        """Reset the animation with a new command."""
        pass

    def update(self, now_ms: int):
        """Advance animation frame based on game-loop time, not wall time."""
        pass

    def get_img(self) -> Img:
        """Get the current frame image."""
        pass
