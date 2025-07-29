from Observer.EventType import EventType

class Event:
    def __init__(self, event_type: EventType, data=None):
        self.type = event_type
        self.data = data or {}
        
