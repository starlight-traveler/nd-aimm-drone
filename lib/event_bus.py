# event_bus.py
import threading

class EventBus:
    def __init__(self):
        self.subscribers = {}
        self.lock = threading.Lock()

    def subscribe(self, event_type, callback):
        with self.lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)

    def publish(self, event_type, data):
        with self.lock:
            callbacks = self.subscribers.get(event_type, [])
        for callback in callbacks:
            callback(data)
