from Event import Event


class GameOverEvent(Event):
    """Event indicating the game is over"""
    def __init__(self, winner):
        super().__init__("game_over", {"winner": winner})
        # The winner can be "white", "black", or "draw"
    