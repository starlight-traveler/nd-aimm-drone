# commands.py
from pymavlink import mavutil
import time

class MavlinkCommands:
    def __init__(self, mavlink_connection, logger):
        self.mav = mavlink_connection.mav
        self.connection = mavlink_connection
        self.logger = logger
        self.landed = False

    def arm(self):
        self.logger.info("Sending ARM command")
        self.mav.command_long_send(
            self.connection.target_system,
            self.connection.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            1, 0, 0, 0, 0, 0, 0
        )

    def disarm(self):
        self.logger.info("Sending DISARM command")
        self.mav.command_long_send(
            self.connection.target_system,
            self.connection.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            0, 0, 0, 0, 0, 0, 0
        )
        self.landed = True  # Assume disarmed means landed

    def takeoff(self, altitude):
        self.logger.info(f"Sending TAKEOFF command to {altitude} meters")
        self.mav.command_long_send(
            self.connection.target_system,
            self.connection.target_component,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            0,
            0, 0, 0, 0, 0, 0, altitude
        )

    def land(self):
        self.logger.info("Sending LAND command")
        self.mav.command_long_send(
            self.connection.target_system,
            self.connection.target_component,
            mavutil.mavlink.MAV_CMD_NAV_LAND,
            0,
            0, 0, 0, 0, 0, 0, 0
        )

    def set_mode(self, mode):
        self.logger.info(f"Setting mode to {mode}")
        # Map mode string to mode ID based on ArduPilot's mode mappings
        # These mode IDs are placeholders. Replace them with actual mode numbers as per your firmware.
        mode_mapping = {
            'AUTO': 4,       # Example ID, adjust based on actual mappings
            'GUIDED': 7,
            'STABILIZE': 2,
            'RTL': 6,
            'LAND': 9
            # Add other modes as needed
        }
        if mode not in mode_mapping:
            self.logger.error(f"Unknown mode: {mode}")
            return

        mode_id = mode_mapping[mode]
        self.mav.set_mode_send(
            self.connection.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id
        )
        self.logger.info(f"Set mode to {mode}")

    def return_to_launch(self):
        self.logger.info("Sending RETURN_TO_LAUNCH command")
        self.mav.command_long_send(
            self.connection.target_system,
            self.connection.target_component,
            mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
            0,
            0, 0, 0, 0, 0, 0, 0
        )
        
    def send_velocity_command(self, vx, vy, vz):
            self.logger.debug(f"Sending velocity command: vx={vx}, vy={vy}, vz={vz}")
            # Use the SET_POSITION_TARGET_LOCAL_NED message
            self.mav.set_position_target_local_ned_send(
                0,  # time_boot_ms (not used)
                self.connection.target_system,
                self.connection.target_component,
                mavutil.mavlink.MAV_FRAME_BODY_NED,
                0b0000111111000111,  # Bitmask to indicate which fields are valid (vx, vy, vz)
                0, 0, 0,  # x, y, z positions (not used)
                vx, vy, vz,  # Velocity in m/s
                0, 0, 0,  # Accelerations (not used)
                0, 0  # Yaw, yaw rate (not used)
        )
            
    def update_landed_status(self, msg):
        # Update landed status based on incoming MAVLink messages
        # Example: Check altitude and velocity
        if msg.get_type() == 'GLOBAL_POSITION_INT':
            altitude = msg.relative_alt / 1000.0  # Convert mm to meters
            self.logger.debug(f"Current altitude: {altitude} meters")
            if altitude < 0.5:
                self.landed = True

    def is_landed(self):
        return self.landed
