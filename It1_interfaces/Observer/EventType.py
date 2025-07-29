from enum import Enum

class EventType(Enum):
    """סוגי ארועים במשחק"""
    GAME_START = "game_start"
    MOVE_MADE = "move_made"
    PIECE_CAPTURE = "piece_capture"
    GAME_OVER = "game_over"
    PAWN_PROMOTION = "pawn_promotion"
    PIECE_SELECTED = "piece_selected"
    INVALID_MOVE = "invalid_move"
    GAME_OVER_BLACK = "game_over_black"
    GAME_OVER_WHITE = "game_over_white"
    
    def __str__(self):
        return self.value
