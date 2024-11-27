# data_recorder.py
import csv
import threading

class DataRecorder:
    def __init__(self, event_bus, filename='flight_data.csv'):
        self.event_bus = event_bus
        self.filename = filename
        self.lock = threading.Lock()
        self.file = open(self.filename, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.header_written = False

        self.event_bus.subscribe('ALL', self.record_message)

    def record_message(self, msg):
        with self.lock:
            data = msg.to_dict()
            if not self.header_written:
                self.writer.writerow(data.keys())
                self.header_written = True
            self.writer.writerow(data.values())

    def close(self):
        with self.lock:
            self.file.close()
