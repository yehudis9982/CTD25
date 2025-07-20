# mock_img.py
from img import Img

class MockImg(Img):
    """Headless Img that just records calls."""
    traj     : list[tuple[int,int]]  = []   # every draw_on() position
    txt_traj : list[tuple[tuple[int,int],str]] = []

    def __init__(self):                     # override, no cv2 needed
        """Initialize mock image with mock pixels."""
        pass

    # keep the method names identical to Img -------------------------
    def read(self, path, *_, **__):
        """Mock read method that pretends to load an image."""
        pass

    def draw_on(self, other, x, y):
        """Record draw operation position."""
        pass

    def put_text(self, txt, x, y, font_size, *_, **__):
        """Record text placement operation."""
        pass

    def show(self): 
        """Do nothing for show operation."""
        pass

    # helper for tests
    @classmethod
    def reset(cls):
        """Reset the recorded trajectories."""
        pass 