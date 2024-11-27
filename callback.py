# drone_functions.py (updated)
import threading

class MavlinkCallBack:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.messages = {}
        self.lock = threading.Lock()

        # Subscribe to all messages
        self.event_bus.subscribe('ALL', self.handle_message)

        # Subscribe to specific messages
        self.event_bus.subscribe('HEARTBEAT', self.handle_heartbeat)
        self.event_bus.subscribe('ATTITUDE', self.handle_attitude)

        # Store specific data
        self.system_status = None
        self.attitude = None

    def handle_message(self, msg):
        with self.lock:
            self.messages[msg.get_type()] = msg

    def handle_heartbeat(self, msg):
        with self.lock:
            self.system_status = {
                'type': msg.type,
                'autopilot': msg.autopilot,
                'base_mode': msg.base_mode,
                'custom_mode': msg.custom_mode,
                'system_status': msg.system_status
            }

    def handle_attitude(self, msg):
        with self.lock:
            self.attitude = {
                'roll': msg.roll,
                'pitch': msg.pitch,
                'yaw': msg.yaw,
                'rollspeed': msg.rollspeed,
                'pitchspeed': msg.pitchspeed,
                'yawspeed': msg.yawspeed
            }

    def get_system_status(self):
        with self.lock:
            return self.system_status

    def get_attitude(self):
        with self.lock:
            return self.attitude
