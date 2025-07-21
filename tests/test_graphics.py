import pathlib
import tempfile
import shutil
import os
import pytest

class DummyBoard:
    def cell_to_pixel(self, cell):
        return (0, 0)

class DummyImg:
    def __init__(self):
        self.loaded = False
    def load(self, path):
        self.loaded = True

def create_dummy_sprites_folder(num=3):
    tmpdir = tempfile.mkdtemp()
    for i in range(num):
        with open(os.path.join(tmpdir, f"{i}.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")  # header only
    return pathlib.Path(tmpdir)

def test_load_frames_and_reset(monkeypatch):
    sprites = create_dummy_sprites_folder(3)
    board = DummyBoard()
    monkeypatch.setattr("CTD25.It1_interfaces.Graphics.Img", DummyImg)
    from CTD25.It1_interfaces.Graphics import Graphics
    gfx = Graphics(sprites, board, loop=True, fps=2.0)
    assert len(gfx.frames) == 3
    assert gfx.current_frame == 0
    gfx.current_frame = 2
    gfx.reset()
    assert gfx.current_frame == 0
    shutil.rmtree(sprites)

def test_update_and_loop(monkeypatch):
    sprites = create_dummy_sprites_folder(2)
    board = DummyBoard()
    monkeypatch.setattr("CTD25.It1_interfaces.Graphics.Img", DummyImg)
    from CTD25.It1_interfaces.Graphics import Graphics
    gfx = Graphics(sprites, board, loop=True, fps=2.0)
    gfx.update(0)
    assert gfx.current_frame == 0
    gfx.update(500)
    assert gfx.current_frame == 1
    gfx.update(1000)
    assert gfx.current_frame == 0  # looped
    shutil.rmtree(sprites)

def test_update_no_loop(monkeypatch):
    sprites = create_dummy_sprites_folder(2)
    board = DummyBoard()
    monkeypatch.setattr("CTD25.It1_interfaces.Graphics.Img", DummyImg)
    from CTD25.It1_interfaces.Graphics import Graphics
    gfx = Graphics(sprites, board, loop=False, fps=2.0)
    gfx.update(1)      # מאתחל last_update ל-1
    gfx.update(501)    # 501-1=500ms, מחליף פריים
    assert gfx.current_frame == 1
    gfx.update(1001)
    assert gfx.current_frame == 1  # stays on last frame
    assert not gfx.running
    shutil.rmtree(sprites)

def test_copy(monkeypatch):
    sprites = create_dummy_sprites_folder(1)
    board = DummyBoard()
    monkeypatch.setattr("CTD25.It1_interfaces.Graphics.Img", DummyImg)
    from CTD25.It1_interfaces.Graphics import Graphics
    gfx = Graphics(sprites, board, loop=True, fps=2.0)
    gfx.current_frame = 1
    gfx.last_update = 123
    gfx.running = False
    gfx2 = gfx.copy()
    assert gfx2.current_frame == 1
    assert gfx2.last_update == 123
    assert gfx2.running is False
    shutil.rmtree(sprites)

def test_update_and_loop(monkeypatch):
    sprites = create_dummy_sprites_folder(2)
    board = DummyBoard()
    monkeypatch.setattr("CTD25.It1_interfaces.Graphics.Img", DummyImg)
    from CTD25.It1_interfaces.Graphics import Graphics
    gfx = Graphics(sprites, board, loop=True, fps=2.0)
    gfx.update(1)
    gfx.update(501)
    assert gfx.current_frame == 1
    shutil.rmtree(sprites)