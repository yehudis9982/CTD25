from Observer.Event import Event
from Observer.EventType import EventType

class GameOverEvent(Event):
    """Event שנשלח כשהמשחק מסתיים"""
    
    def __init__(self, winner=None, reason=None):
        super().__init__(EventType.GAME_OVER, {
            "winner": winner,
            "reason": reason
        })
    
    def __str__(self):
        return f"GameOverEvent(winner={self.data.get('winner')}, reason={self.data.get('reason')})"
    