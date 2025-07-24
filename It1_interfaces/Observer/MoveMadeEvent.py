from Event import Event
class MoveMadeEvent(Event):
    def __init__(self, piece_type, start_position, end_position,timestamp=None):
        super().__init__("move_made", {
            "piece_type": piece_type,
            "start_position": start_position,
            "end_position": end_position,
            "timestamp": timestamp
        })
