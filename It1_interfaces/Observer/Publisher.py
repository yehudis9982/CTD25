from .Subscriber import Subscriber
class Publisher:
    def __init__(self):
        self.subscribers = []

    def subscribe(self, subscriber: Subscriber):
        self.subscribers.append(subscriber)

    def unsubscribe(self, subscriber: Subscriber):
        self.subscribers.remove(subscriber)

    def notify(self, event):
        for subscriber in self.subscribers:
            subscriber.update(event)