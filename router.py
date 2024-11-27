# mavlink_router.py
from pymavlink import mavutil
import threading

class MavlinkRouter:
    def __init__(self, event_bus, connection_string='udp:0.0.0.0:14550'):
        self.event_bus = event_bus
        self.connection_string = connection_string
        self.mavlink_connection = None
        self.running = False

    def start(self):
        self.mavlink_connection = mavutil.mavlink_connection(self.connection_string)
        self.running = True
        threading.Thread(target=self.listen_to_mavlink, daemon=True).start()

    def listen_to_mavlink(self):
        while self.running:
            msg = self.mavlink_connection.recv_match(blocking=True)
            if msg:
                # Publish the message to the event bus
                self.event_bus.publish(msg.get_type(), msg)

    def send_message(self, message):
        self.mavlink_connection.mav.send(message)
