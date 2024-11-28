# lib/event_bus.py
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

    def unsubscribe(self, event_type, callback):
        with self.lock:
            if event_type in self.subscribers:
                self.subscribers[event_type].remove(callback)
                if not self.subscribers[event_type]:
                    del self.subscribers[event_type]

    def publish(self, event_type, data):
        with self.lock:
            subscribers = self.subscribers.get(event_type, []).copy()
        for callback in subscribers:
            try:
                callback(data)
            except Exception as e:
                # Optionally, log the exception
                pass
