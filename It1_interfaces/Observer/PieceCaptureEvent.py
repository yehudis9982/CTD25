from .Event import Event
from .EventType import EventType

class PieceCaptureEvent(Event):
    def __init__(self, piece_type, captured_by):
        super().__init__(EventType.PIECE_CAPTURE, {"piece_type": piece_type, "captured_by": captured_by})
