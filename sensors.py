# sensors.py
import threading

class SensorData:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.imu_data = None
        self.gps_data = None
        self.lock = threading.Lock()

        self.event_bus.subscribe('RAW_IMU', self.handle_imu)
        self.event_bus.subscribe('GPS_RAW_INT', self.handle_gps)

    def handle_imu(self, msg):
        with self.lock:
            self.imu_data = {
                'xacc': msg.xacc,
                'yacc': msg.yacc,
                'zacc': msg.zacc,
                'xgyro': msg.xgyro,
                'ygyro': msg.ygyro,
                'zgyro': msg.zgyro,
            }

    def handle_gps(self, msg):
        with self.lock:
            self.gps_data = {
                'lat': msg.lat / 1e7,
                'lon': msg.lon / 1e7,
                'alt': msg.alt / 1e3,
                'eph': msg.eph,
                'epv': msg.epv,
            }

    def get_imu_data(self):
        with self.lock:
            return self.imu_data

    def get_gps_data(self):
        with self.lock:
            return self.gps_data
