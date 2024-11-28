# safety.py
import threading
import time  # Added import for time module

class SafetyMonitor:
    def __init__(self, event_bus, drone_commands, logger, battery_threshold=20):
        """
        Initializes the SafetyMonitor.

        :param event_bus: The event bus for subscribing to MAVLink messages.
        :param drone_commands: The drone commands interface for controlling the drone.
        :param logger: The logger instance for logging messages.
        :param battery_threshold: Battery percentage threshold to trigger safety actions.
        """
        self.event_bus = event_bus
        self.drone_commands = drone_commands
        self.logger = logger
        self.lock = threading.Lock()
        self.battery_status = None
        self.battery_threshold = battery_threshold  # Configurable threshold
        self.running = True  # Flag to control the monitoring loop

        # Subscribe to battery status messages
        self.event_bus.subscribe('SYS_STATUS', self.handle_sys_status)
        threading.Thread(target=self.monitor_safety, daemon=True).start()

    def handle_sys_status(self, msg):
        """
        Handles incoming SYS_STATUS MAVLink messages.

        :param msg: The SYS_STATUS message containing battery information.
        """
        with self.lock:
            self.battery_status = {
                'voltage_battery': msg.voltage_battery,
                'current_battery': msg.current_battery,
                'battery_remaining': msg.battery_remaining
            }
            self.logger.debug(f"Updated battery status: {self.battery_status}")

    def monitor_safety(self):
        """
        Continuously monitors the battery status and initiates safety actions if necessary.
        """
        self.logger.info("SafetyMonitor thread started.")
        while self.running:
            try:
                with self.lock:
                    if self.battery_status:
                        battery_remaining = self.battery_status['battery_remaining']
                        self.logger.debug(f"Current battery remaining: {battery_remaining}%")
                        if battery_remaining < self.battery_threshold:
                            self.logger.warning(f"Low battery ({battery_remaining}%)! Initiating RTL.")
                            self.drone_commands.return_to_launch()
                            self.running = False  # Stop monitoring after initiating RTL
                time.sleep(1)  # Sleep to reduce CPU usage
            except Exception as e:
                self.logger.error(f"Exception in SafetyMonitor.monitor_safety: {e}")
                time.sleep(1)  # Sleep before retrying

    def stop(self):
        """
        Stops the SafetyMonitor monitoring loop and unsubscribes from event bus.
        """
        self.running = False
        self.event_bus.unsubscribe('SYS_STATUS', self.handle_sys_status)
        self.logger.info("SafetyMonitor stopped.")
