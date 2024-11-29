# main.py
import time
import os
import logging  # Needed for log level conversion
import yaml  # Assuming you use YAML for config
from lib.event_bus import EventBus
from router import MavlinkRouter
from callback import MavlinkCallBack
from lib.logger import setup_logger
from commands import MavlinkCommands
from safety import SafetyMonitor
from data_recorder import DataRecorder
from mission_planner import MissionPlanner
from precision_landing import PrecisionLanding


class DroneApplication:
    def __init__(self, config_path='start/config.yaml'):
        """
        Initializes the DroneApplication with the given configuration file.

        Parameters:
        - config_path (str): Path to the YAML configuration file.
        """
        self.config_path = config_path
        self.config = {}
        self.logger = None
        self.event_bus = None
        self.mavlink_router = None
        self.drone_commands = None
        self.drone = None
        self.data_recorder = None
        self.safety_monitor = None
        self.mission_planner = None
        self.precision_landing = None

    def load_config(self):
        """
        Loads the configuration from the YAML file.
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file {self.config_path} not found.")
        with open(self.config_path, 'r') as config_file:
            self.config = yaml.safe_load(config_file)
        if not self.config:
            raise ValueError("Configuration file is empty or invalid.")
        print(f"Configuration loaded from {self.config_path}")

    def setup_logging(self):
        """
        Sets up the logger using the configuration settings.
        """
        log_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            self.config['logging'].get('log_file', 'start/drone.log')
        )
        log_level_str = self.config['logging'].get('level', 'DEBUG').upper()
        log_level = getattr(logging, log_level_str, logging.DEBUG)  # Convert string to logging level
        self.logger = setup_logger(log_file=log_file, level=log_level, config=self.config['logging'])
        self.logger.info("=========================")
        self.logger.info("Logger initialized.")

    def initialize_components(self):
        """
        Initializes all necessary components for the drone application.
        """
        # Initialize Event Bus
        self.event_bus = EventBus()
        self.logger.debug("EventBus initialized.")

        # Retrieve MAVLink configuration
        port = self.config['mavlink_router'].get('port', '/dev/ttyUSB0')
        baudrate = self.config['mavlink_router'].get('baudrate', 57600)

        # Initialize MAVLink router with correct parameters and logger
        self.mavlink_router = MavlinkRouter(
            event_bus=self.event_bus,
            logger=self.logger,
            port=port,
            baudrate=baudrate
        )
        self.mavlink_router.start()
        self.logger.debug(f"MAVLink router attempt on {port} at {baudrate} baud.")

        # Wait for MAVLink connection to be established
        timeout = 10  # seconds
        start_time = time.time()
        while not self.mavlink_router.mavlink_connection:
            if time.time() - start_time > timeout:
                self.logger.error("MAVLink connection could not be established within timeout.")
                raise ConnectionError("Failed to establish MAVLink connection.")
            self.logger.debug("Waiting for MAVLink connection...")
            time.sleep(1)

        # Initialize MAVLink commands with connection and logger
        self.drone_commands = MavlinkCommands(self.mavlink_router.mavlink_connection, self.logger)
        self.logger.debug("MavlinkCommands initialized.")

        # Initialize MAVLink callback
        self.drone = MavlinkCallBack(self.event_bus)
        self.logger.debug("MavlinkCallBack initialized.")

        # Initialize data recorder with event bus and logger
        self.data_recorder = DataRecorder(self.event_bus, self.logger)
        self.logger.debug("DataRecorder initialized.")

        # Initialize safety monitor with event bus, commands, and logger
        battery_threshold = self.config['safety'].get('battery_threshold', 20)
        self.safety_monitor = SafetyMonitor(
            event_bus=self.event_bus,
            drone_commands=self.drone_commands,
            logger=self.logger,
            battery_threshold=battery_threshold
        )
        self.logger.debug("SafetyMonitor initialized.")

        # Initialize mission planner with connection, config, and logger
        self.mission_planner = MissionPlanner(self.mavlink_router.mavlink_connection, self.config, self.logger)
        self.logger.debug("MissionPlanner initialized.")

        # Initialize precision landing with callback, commands, config, and logger
        self.precision_landing = PrecisionLanding(self.drone, self.drone_commands, self.config, self.logger)
        self.logger.debug("PrecisionLanding initialized.")

    def run_mission(self):
        """
        Creates, uploads the mission, arms the drone, and starts monitoring.
        """
        # Create and upload the mission
        self.logger.info("Creating and uploading mission.")
        self.mission_planner.create_and_upload_mission()

        # Set the drone to AUTO mode to start the mission
        self.drone_commands.set_mode('AUTO')
        self.logger.info("Set mode to AUTO.")

        # Arm the drone
        self.drone_commands.arm()
        self.logger.info("Armed the drone.")

        # Monitor the mission progress
        try:
            while True:
                # Check current waypoint
                current_wp = self.drone.get_message('MISSION_CURRENT')
                if current_wp and current_wp.seq == 1:
                    self.logger.info("Reached target waypoint, initiating precision landing.")
                    # Switch to precision landing
                    self.precision_landing.start()
                    break

                # Sleep briefly to reduce CPU usage
                time.sleep(1)

            # Keep the main thread alive while precision landing is in progress
            while self.precision_landing.is_running():
                time.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("Interrupted by user.")

    def cleanup(self):
        """
        Ensures all components are properly shut down.
        """
        self.logger.info("Commencing cleanup.")

        # Ensure precision landing is stopped if still running
        if self.precision_landing.is_running():
            self.precision_landing.stop()
            self.logger.info("Stopped precision landing.")

        # Stop the safety monitor
        if self.safety_monitor:
            self.safety_monitor.stop()
            self.logger.info("SafetyMonitor stopped.")

        # Land the drone if not already landed
        if self.drone_commands and not self.drone_commands.is_landed():
            self.drone_commands.land()
            self.logger.info("Initiated landing.")
            time.sleep(10)  # Give some time for landing

        # Disarm the drone
        if self.drone_commands:
            self.drone_commands.disarm()
            self.logger.info("Disarmed the drone.")

        # Stop the MAVLink router
        if self.mavlink_router:
            self.mavlink_router.stop()
            self.logger.info("MAVLink router stopped.")

        # Stop the data recorder
        if self.data_recorder:
            self.data_recorder.close()
            self.logger.info("Data recorder closed.")

        # Indicate the application is finished
        self.logger.info("Drone application finished.")

    def run(self):
        """
        Executes the drone application lifecycle.
        """
        try:
            self.load_config()
            self.setup_logging()
            self.initialize_components()
            self.run_mission()
        except Exception as e:
            if self.logger:
                self.logger.exception(f"An unexpected error occurred: {e}")
            else:
                print(f"An unexpected error occurred: {e}")
        finally:
            self.cleanup()


if __name__ == "__main__":
    app = DroneApplication()
    app.run()
