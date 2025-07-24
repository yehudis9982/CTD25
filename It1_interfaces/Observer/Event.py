class Event:
    def __init__(self, event_type, data=None):
        self.type = event_type
        self.data = data or {}
        
