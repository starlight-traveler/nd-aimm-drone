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
   
    def get_message(self, msg_type):
        with self.lock:
            return self.messages.get(msg_type, None)

    def get_all_messages(self):
        with self.lock:
            return dict(self.messages)
             
    def handle_message(self, msg):
        with self.lock:
            # Store the latest message of each type
            self.messages[msg.get_type()] = msg
            # Update landed status if it's a relevant message
            if msg.get_type() == 'GLOBAL_POSITION_INT':
                self.drone_commands.update_landed_status(msg)

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
