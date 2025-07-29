from Observer.Event import Event
from Observer.EventType import EventType

class GameStartEvent(Event):
    """Event שנשלח כשהמשחק מתחיל"""
    
    def __init__(self):
        super().__init__(EventType.GAME_START)
    
    def __str__(self):
        return f"GameStartEvent(type={self.type})"