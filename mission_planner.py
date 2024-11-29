from pymavlink import mavutil
import time

class MissionPlanner:
    def __init__(self, mavlink_connection, config, logger):
        self.mavlink_connection = mavlink_connection
        self.logger = logger
        self.config = config

    def create_and_upload_mission(self):
        # Define mission waypoints from config
        waypoints = self.create_mission_waypoints()

        # Clear existing mission
        self.clear_mission()

        # Upload mission waypoints
        self.upload_mission(waypoints)

    def create_mission_waypoints(self):
        # Retrieve waypoints from config
        waypoint_configs = self.config.get_section('mission_planner').get('waypoints', [])
        waypoints = []

        for wp in waypoint_configs:
            waypoint = mavutil.mavlink.MAVLink_mission_item_message(
                target_system=self.mavlink_connection.target_system,
                target_component=self.mavlink_connection.target_component,
                seq=wp.get('seq', 0),
                frame=wp.get('frame', mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT),
                command=wp.get('command', mavutil.mavlink.MAV_CMD_NAV_WAYPOINT),
                current=wp.get('current', 0),
                autocontinue=wp.get('autocontinue', 1),
                param1=wp.get('param1', 0),
                param2=wp.get('param2', 0),
                param3=wp.get('param3', 0),
                param4=wp.get('param4', 0),
                x=wp.get('x', 0),
                y=wp.get('y', 0),
                z=wp.get('z', 10)
            )
            waypoints.append(waypoint)
            self.logger.debug(f"Created waypoint: Seq {wp.get('seq', 0)}")

        self.logger.info(f"Total waypoints created: {len(waypoints)}")
        return waypoints

    def clear_mission(self):
        self.logger.info("Clearing existing missions")
        self.mavlink_connection.mav.mission_clear_all_send(
            self.mavlink_connection.target_system,
            self.mavlink_connection.target_component
        )
        time.sleep(1)  # Wait for the mission to be cleared
        self.logger.debug("Mission cleared successfully")

    def upload_mission(self, waypoints):
        self.logger.info("Uploading mission")
        # Send mission count
        self.mavlink_connection.mav.mission_count_send(
            self.mavlink_connection.target_system,
            self.mavlink_connection.target_component,
            len(waypoints)
        )

        for waypoint in waypoints:
            # Wait for MISSION_REQUEST message
            msg = self.mavlink_connection.recv_match(type=['MISSION_REQUEST'], blocking=True, timeout=30)
            if not msg:
                self.logger.error("Failed to receive MISSION_REQUEST")
                return
            seq = msg.seq
            if seq >= len(waypoints):
                self.logger.error(f"Received invalid waypoint sequence: {seq}")
                return
            # Send the waypoint
            self.mavlink_connection.mav.send(waypoints[seq])
            self.logger.info(f"Sent waypoint {seq}")

        # Wait for mission acknowledgment
        ack = self.mavlink_connection.recv_match(type=['MISSION_ACK'], blocking=True, timeout=30)
        if ack and ack.type == mavutil.mavlink.MAV_MISSION_ACCEPTED:
            self.logger.info("Mission upload acknowledged")
        else:
            self.logger.error("Mission upload failed or was rejected")
