from .Subscriber import Subscriber
class ScoreTracker(Subscriber):
    def __init__(self):
        self.score = {"white": 0, "black": 0}
        self.piece_values = {
            'P': 1,
            'N': 3,
            'B': 3,
            'R': 5,
            'Q': 9,
            'K': 0  # King is invaluable, but we can track captures
        }
    def update(self, event):
        if(event.type != "piece_capture"):
            return
        piece_type = event.data.get('piece_type', '')
        captured_by = event.data.get('captured_by', '')
        value = self.piece_values.get(piece_type, 0)
        self.score[captured_by] += value
        print(f"Score updated: {captured_by} captured {piece_type} (+{value} points). Total scores: {self.score}")
    
    def get_score(self, player_color):
        return self.score.get(player_color, 0)
    def reset(self):
        """Reset the score tracker for a new game"""
        self.score = {"white": 0, "black": 0}
        