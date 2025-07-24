class Subscriber:
    def update(self,event):
        raise NotImplementedError("Subclass must implement abstract method")
    def reset(self):
        raise NotImplementedError("Subclass must implement abstract method")