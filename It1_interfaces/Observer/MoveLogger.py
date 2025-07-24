from MoveMadeEvent import MoveMadeEvent
from Subscriber import Subscriber

class MoveLogger(Subscriber):
    def __init__(self):
        self.moves = {"white": [], "black": []}
   
    def update(self, event):
        if isinstance(event, MoveMadeEvent):
            move_data = {
                "time": event.data.get("timestamp").strftime("%H:%M:%S") if event.data.get("timestamp") else "unknown",
                "move": f"{event.data['piece_type']} from {event.data['start_position']} to {event.data['end_position']}"
            }
            self.moves[event.data["piece_type"]].append(move_data)
    def get_moves(self, player_coler):
        return self.moves[player_coler]


    def reset(self):
        """Reset the move logger for a new game"""
        self.moves = {"white": [], "black": []}
