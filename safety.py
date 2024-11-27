# safety.py
import threading

class SafetyMonitor:
    def __init__(self, event_bus, drone_commands, logger):
        self.event_bus = event_bus
        self.drone_commands = drone_commands
        self.logger = logger
        self.lock = threading.Lock()
        self.battery_status = None

        # Subscribe to battery status messages
        self.event_bus.subscribe('SYS_STATUS', self.handle_sys_status)
        threading.Thread(target=self.monitor_safety, daemon=True).start()

    def handle_sys_status(self, msg):
        with self.lock:
            self.battery_status = {
                'voltage_battery': msg.voltage_battery,
                'current_battery': msg.current_battery,
                'battery_remaining': msg.battery_remaining
            }

    def monitor_safety(self):
        while True:
            with self.lock:
                if self.battery_status and self.battery_status['battery_remaining'] < 20:
                    self.logger.warning("Low battery! Initiating RTL.")
                    self.drone_commands.return_to_launch()
                    break
            time.sleep(1)
