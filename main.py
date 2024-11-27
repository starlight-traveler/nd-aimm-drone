# main.py
import time
from event_bus import EventBus
from router import MavlinkRouter
from callback import MavlinkCallBack
from logger import setup_logger
from commands import MavlinkCommands
from safety import SafetyMonitor
from data_recorder import DataRecorder

def main():
    # Initialize components
    logger = setup_logger()
    logger.info("Starting the drone application")

    event_bus = EventBus()
    mavlink_router = MavlinkRouter(
        event_bus,
        port='/dev/ttyUSB0',  # Adjust the serial port as needed
        baudrate=57600        # Match this with your Pixhawk's baud rate
    )
    drone = MavlinkCallBack(event_bus)
    drone_commands = MavlinkCommands(mavlink_router.mavlink_connection)
    data_recorder = DataRecorder(event_bus)
    safety_monitor = SafetyMonitor(event_bus, drone_commands, logger)

    # Start the MAVLink router
    mavlink_router.start()

    # Arm the drone
    drone_commands.arm()
    logger.info("Armed the drone")

    # Takeoff to 10 meters altitude
    drone_commands.takeoff(10)
    logger.info("Initiated takeoff to 10 meters")

    # Monitor for a certain duration
    duration = 30  # seconds
    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            # Example: Accessing specific data
            attitude = drone.get_message('ATTITUDE')
            if attitude:
                roll = attitude.roll
                pitch = attitude.pitch
                yaw = attitude.yaw
                logger.info(f"Attitude - Roll: {roll:.2f}, Pitch: {pitch:.2f}, Yaw: {yaw:.2f}")

            # Sleep briefly to reduce CPU usage
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    finally:
        # Land the drone
        drone_commands.land()
        logger.info("Initiated landing")

        # Give some time for landing
        time.sleep(10)

        # Disarm the drone
        drone_commands.disarm()
        logger.info("Disarmed the drone")

        # Stop the data recorder
        data_recorder.close()
        logger.info("Data recorder closed")

        # Indicate the application is finished
        logger.info("Drone application finished")

if __name__ == "__main__":
    main()
