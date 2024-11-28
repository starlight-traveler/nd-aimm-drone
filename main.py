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
from config import Config

def main():
    # Get the absolute path of the directory where main.py resides
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct absolute path for config.yaml
    config_path = os.path.join(script_dir, 'start', 'config.yaml')
    
    # Load configuration
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)

    # Initialize logger with configuration settings
    log_file = os.path.join(script_dir, config['logging'].get('log_file', 'start/drone.log'))
    log_level_str = config['logging'].get('level', 'DEBUG').upper()
    log_level = getattr(logging, log_level_str, logging.DEBUG)  # Convert string to logging level
    logger = setup_logger(log_file=log_file, level=log_level, config=config['logging'])
    logger.info("Starting the drone application")

    # Initialize event bus
    event_bus = EventBus()

    # Retrieve MAVLink configuration
    port = config['mavlink_router'].get('port', '/dev/ttyUSB0')
    baudrate = config['mavlink_router'].get('baudrate', 57600)

    # Initialize MAVLink router with correct parameters and logger
    mavlink_router = MavlinkRouter(
        event_bus=event_bus,
        logger=logger,
        port=port,
        baudrate=baudrate
    )

    # Start the MAVLink router before using the connection
    mavlink_router.start()

    # Initialize MAVLink commands with connection and logger
    drone_commands = MavlinkCommands(mavlink_router.mavlink_connection, logger)

    # Initialize MAVLink callback
    drone = MavlinkCallBack(event_bus)

    # Initialize data recorder with event bus and logger
    data_recorder = DataRecorder(event_bus, logger)

    # Initialize safety monitor with event bus, commands, and logger
    battery_threshold = config['safety'].get('battery_threshold', 20)
    safety_monitor = SafetyMonitor(
        event_bus=event_bus,
        drone_commands=drone_commands,
        logger=logger,
        battery_threshold=battery_threshold
    )

    # Initialize mission planner with connection, config, and logger
    mission_planner = MissionPlanner(mavlink_router.mavlink_connection, config, logger)

    # Initialize precision landing with callback, commands, config, and logger
    precision_landing = PrecisionLanding(drone, drone_commands, config, logger)

    # Create and upload the mission
    logger.info("Creating and uploading mission")
    mission_planner.create_and_upload_mission()

    # Set the drone to AUTO mode to start the mission
    drone_commands.set_mode('AUTO')
    logger.info("Set mode to AUTO")

    # Arm the drone
    drone_commands.arm()
    logger.info("Armed the drone")

    # Monitor the mission progress
    try:
        while True:
            # Check current waypoint
            current_wp = drone.get_message('MISSION_CURRENT')
            if current_wp and current_wp.seq == 1:
                logger.info("Reached target waypoint, initiating precision landing")
                # Switch to precision landing
                precision_landing.start()
                break

            # Sleep briefly to reduce CPU usage
            time.sleep(1)

        # Keep the main thread alive while precision landing is in progress
        while precision_landing.is_running():
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    finally:
        # Ensure precision landing is stopped if still running
        if precision_landing.is_running():
            precision_landing.stop()
            logger.info("Stopped precision landing")

        # Stop the safety monitor
        safety_monitor.stop()
        logger.info("SafetyMonitor stopped.")

        # Land the drone if not already landed
        if not drone_commands.is_landed():
            drone_commands.land()
            logger.info("Initiated landing")

            # Give some time for landing
            time.sleep(10)

        # Disarm the drone
        drone_commands.disarm()
        logger.info("Disarmed the drone")

        # Stop the MAVLink router
        mavlink_router.stop()

        # Stop the data recorder
        data_recorder.close()
        logger.info("Data recorder closed")

        # Indicate the application is finished
        logger.info("Drone application finished")

if __name__ == "__main__":
    main()
