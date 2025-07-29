from .MoveMadeEvent import MoveMadeEvent
from .Subscriber import Subscriber
from .EventType import EventType

class MoveLogger(Subscriber):
    def __init__(self):
        self.moves = {"white": [], "black": []}
   
    def update(self, event):
        if event.type == EventType.MOVE_MADE:
            move_data = {
                "time": event.data.get("timestamp").strftime("%H:%M:%S") if event.data.get("timestamp") else "unknown",
                "move": f"{event.data['piece_type']} {event.data['start_position']} -> {event.data['end_position']}"
            }
            player_color = event.data.get("player_color", "unknown")
            self.moves[player_color].append(move_data)
    def get_moves(self, player_color):
        return self.moves[player_color]


    def reset(self):
        """Reset the move logger for a new game"""
        self.moves = {"white": [], "black": []}
