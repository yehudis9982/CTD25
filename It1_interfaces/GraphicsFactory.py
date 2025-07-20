import pathlib

from Graphics import Graphics


class GraphicsFactory:
    def load(self,
             sprites_dir: pathlib.Path,
             cfg: dict,
             cell_size: tuple[int, int]) -> Graphics:
        """Load graphics from sprites directory with configuration."""
        pass
    