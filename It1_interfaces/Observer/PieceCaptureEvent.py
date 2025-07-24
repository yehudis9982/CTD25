from .Event import Event
class PieceCaptureEvent(Event):
    def __init__(self, piece_type, captured_by):
        super().__init__("piece_capture", {"piece_type": piece_type, "captured_by": captured_by})
