from .Event import Event
from .EventType import EventType

class MoveMadeEvent(Event):
    def __init__(self, piece_type, start_position, end_position, player_color, timestamp=None):
        super().__init__(EventType.MOVE_MADE, {
            "piece_type": piece_type,
            "start_position": start_position,
            "end_position": end_position,
            "player_color": player_color,
            "timestamp": timestamp
        })
