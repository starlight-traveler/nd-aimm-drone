# router.py
from pymavlink import mavutil
import threading

class MavlinkRouter:
    def __init__(self, event_bus, logger, port='/dev/ttyUSB0', baudrate=57600):
        """
        Initializes the MavlinkRouter.

        :param event_bus: The event bus for publishing MAVLink messages.
        :param logger: The logger instance for logging messages.
        :param port: Serial port for MAVLink connection.
        :param baudrate: Baud rate for MAVLink connection.
        """
        self.event_bus = event_bus
        self.logger = logger
        self.port = port
        self.baudrate = baudrate
        self.mavlink_connection = None
        self.running = False

    def start(self):
        """
        Starts the MAVLink connection and begins listening for messages.
        """
        try:
            self.mavlink_connection = mavutil.mavlink_connection(
                self.port,
                baud=self.baudrate,
                autoreconnect=True
            )
            self.running = True
            threading.Thread(target=self.listen_to_mavlink, daemon=True).start()
            self.logger.info(f"MAVLink connection started on {self.port} at {self.baudrate} baud.")
        except Exception as e:
            self.logger.error(f"Failed to start MAVLink connection: {e}")

    def listen_to_mavlink(self):
        """
        Listens for incoming MAVLink messages and publishes them to the event bus.
        """
        while self.running:
            try:
                msg = self.mavlink_connection.recv_match(blocking=True)
                if msg:
                    # Publish the MAVLink message type and message to the event bus
                    self.event_bus.publish(msg.get_type(), msg)
            except Exception as e:
                self.logger.error(f"Error receiving MAVLink message: {e}")

    def send_message(self, message):
        """
        Sends a MAVLink message.

        :param message: The MAVLink message to send.
        """
        try:
            self.mavlink_connection.mav.send(message)
            self.logger.info(f"Sent message: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")

    def stop(self):
        """
        Stops the MAVLink connection and cleans up resources.
        """
        self.running = False
        if self.mavlink_connection:
            self.mavlink_connection.close()
            self.logger.info("MAVLink connection closed.")
