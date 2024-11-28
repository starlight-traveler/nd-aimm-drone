# precision_landing.py
import threading
import time
import cv2
import depthai as dai
import numpy as np
from lib.pid_controller import PIDController

class PrecisionLanding:
    def __init__(self, drone_callback, drone_commands, config, logger):
        self.drone = drone_callback
        self.drone_commands = drone_commands
        self.config = config
        self.logger = logger
        self.running = False
        self.thread = None

        # Camera parameters
        self.frame_width = 640
        self.frame_height = 480
        self.camera_initialized = False

        # Initialize PID controllers for x and y axes
        pid_config = self.config.get('precision_landing', {}).get('pid', {})
        self.pid_x = PIDController(
            kp=pid_config.get('kp', 0.5),
            ki=pid_config.get('ki', 0.0),
            kd=pid_config.get('kd', 0.1),
            output_limits=(-pid_config.get('max_output', 1.0), pid_config.get('max_output', 1.0))
        )
        self.pid_y = PIDController(
            kp=pid_config.get('kp', 0.5),
            ki=pid_config.get('ki', 0.0),
            kd=pid_config.get('kd', 0.1),
            output_limits=(-pid_config.get('max_output', 1.0), pid_config.get('max_output', 1.0))
        )

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run_precision_landing, daemon=True)
            self.thread.start()
            self.logger.info("Precision landing thread started.")

    def run_precision_landing(self):
        self.logger.info("Starting precision landing using computer vision")

        # Switch to GUIDED mode for manual control
        desired_mode = self.config.get('precision_landing', {}).get('mode', 'GUIDED')
        self.drone_commands.set_mode(desired_mode)
        time.sleep(2)  # Allow mode switch to take effect

        # Initialize the camera
        if not self.camera_initialized:
            self.init_camera()

        # Start the camera stream
        with dai.Device(self.pipeline) as device:
            self.logger.info("DepthAI camera initialized.")
            # Start data queues
            q_video = device.getOutputQueue(name="video", maxSize=4, blocking=False)

            last_time = time.time()

            while self.running:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                in_video = q_video.tryGet()
                if in_video is not None:
                    frame = in_video.getCvFrame()
                    # Process the frame to detect the landing pad
                    landing_condition_met, offset_x, offset_y = self.process_frame(frame)

                    if landing_condition_met:
                        self.logger.info("Landing condition met, initiating landing")
                        self.drone_commands.land()
                        break
                    else:
                        # Adjust drone position based on offset
                        self.adjust_drone_position(offset_x, offset_y, dt)

                # Sleep briefly to reduce CPU usage
                time.sleep(0.1)

        self.running = False
        self.logger.info("Precision landing completed")

    def init_camera(self):
        # Create pipeline
        self.pipeline = dai.Pipeline()

        # Define sources and outputs
        cam_rgb = self.pipeline.create(dai.node.ColorCamera)
        xout_video = self.pipeline.create(dai.node.XLinkOut)

        xout_video.setStreamName("video")

        # Properties
        cam_rgb.setPreviewSize(self.frame_width, self.frame_height)
        cam_rgb.setInterleaved(False)
        cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)

        # Linking
        cam_rgb.preview.link(xout_video.input)

        self.camera_initialized = True

    def process_frame(self, frame):
        # Convert to HSV color space
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Define color range for white detection
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])

        # Create mask to isolate white colors
        mask = cv2.inRange(hsv, lower_white, upper_white)

        # Remove noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=2)

        # Apply the mask to the original image
        masked_frame = cv2.bitwise_and(frame, frame, mask=mask)

        # Convert to grayscale
        gray = cv2.cvtColor(masked_frame, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        # Use Hough Circle Transform to detect circles
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=50,
            param1=50,
            param2=20,  # Adjust param2 as needed
            minRadius=10,
            maxRadius=0
        )

        if circles is not None:
            # Convert circles to integer values
            circles = np.round(circles[0, :]).astype("int")

            # Find the largest circle assuming it's the landing pad
            largest_circle = max(circles, key=lambda c: c[2])  # c[2] is the radius
            x, y, radius = largest_circle

            # Calculate offsets from the center of the image
            offset_x = x - self.frame_width / 2
            offset_y = y - self.frame_height / 2

            # Normalize offsets
            offset_x /= self.frame_width / 2  # Now ranges from -1 to 1
            offset_y /= self.frame_height / 2

            self.logger.debug(f"Detected landing pad at offset ({offset_x:.2f}, {offset_y:.2f}), radius: {radius}")

            # Check if the pad is centered enough to land
            threshold = self.config.get('precision_landing', {}).get('center_threshold', 0.05)
            if abs(offset_x) < threshold and abs(offset_y) < threshold:
                # Optionally, check if the drone is close enough based on radius
                min_radius = self.config.get('precision_landing', {}).get('min_landing_radius', 50)
                if radius >= min_radius:
                    return True, offset_x, offset_y
            return False, offset_x, offset_y

        # If no circle is found
        return False, 0, 0

    def adjust_drone_position(self, offset_x, offset_y, dt):
        # Use the offsets to adjust the drone's position using PID controllers

        # Update PID controllers for x and y axes
        vx = self.pid_x.update(-offset_y, dt)
        vy = self.pid_y.update(-offset_x, dt)
        vz = 0  # Maintain current altitude

        self.logger.debug(f"Adjusting position with PID: vx={vx:.2f}, vy={vy:.2f}, vz={vz:.2f}")
        self.drone_commands.send_velocity_command(vx, vy, vz)

    def is_running(self):
        return self.running

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
            self.logger.info("Stopped precision landing thread")
