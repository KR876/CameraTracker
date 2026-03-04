import concurrent.futures
import json
import requests
import time
from datetime import datetime
from ultralytics import YOLO
import logging
from pathlib import Path
import urllib3
import math
import threading

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

Path('logs').mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/collector.log'),
        logging.StreamHandler()
    ]
)

class TrafficCollector:
    def __init__(self):
        project_root = Path(__file__).parent.parent
        config_path = project_root / 'config' / 'cameras.json'

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.cameras = config['cameras']
        self.interval = config['collection_interval']

        self.temp_dir = Path('temp')
        self.temp_dir.mkdir(exist_ok=True)

        self.model = YOLO('yolov8l.pt')

        self.detection_history = {}
        self.max_history_frames = 20
        self.history_lock = threading.Lock()

        from database.db_manager import DatabaseManager
        self.db = DatabaseManager()

        logging.info(f"Monitoring {len(self.cameras)} cameras")

    def get_box_center(self, box):
        """Get center point of bounding box"""
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def calculate_distance(self, point1, point2):
        """Euclidean distance between two points"""
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def is_parked(self, current_box, history, threshold=30):
        """
        Check if vehicle has been stationary for 20+ frames (permanently parked)
        Returns True if parked, False if moving or temporarily stopped (e.g. red light)
        """
        if not history or len(history) < self.max_history_frames:
            return False

        curr_center = self.get_box_center(current_box)
        stationary_count = 0 # Not enough history, assume moving

        for frame_boxes in history[-self.max_history_frames:]:
            found_match = False
            for old_box in frame_boxes:
                old_center = self.get_box_center(old_box)
                distance = self.calculate_distance(curr_center, old_center)

                if distance < threshold:
                    stationary_count += 1
                    found_match = True
                    break

            if not found_match:
                stationary_count = 0

        # Only consider parked if stationary for all 20 frames
        return stationary_count >= self.max_history_frames

    def detect_vehicles(self, image_path, camera_id):
        results = self.model(image_path, verbose=False)
        boxes = results[0].boxes

        with self.history_lock:
            if camera_id not in self.detection_history:
                self.detection_history[camera_id] = []
            history = self.detection_history[camera_id].copy()

        # COCO class IDs: 2=car, 5=bus, 7=truck
        counts = {'total': 0, 'cars': 0, 'buses': 0}

        for box in boxes:
            if self.is_parked(box, history, threshold=30):
                continue

            cls = int(box.cls)

            if cls == 2 or cls == 7:  # Car or truck counts as car, buses are kept separate
                counts['cars'] += 1
                counts['total'] += 1
            elif cls == 5:  # Bus, but also seems to track trams
                counts['buses'] += 1
                counts['total'] += 1

        with self.history_lock:
            self.detection_history[camera_id].append(boxes)
            if len(self.detection_history[camera_id]) > self.max_history_frames:
                self.detection_history[camera_id].pop(0)

        if len(history) > self.max_history_frames:
            history.pop(0)

        return counts

    def collect_from_camera(self, camera):
        try:
            url = camera['url']
            response = requests.get(url, timeout=1, verify=False)

            if response.status_code == 200:
                temp_file = self.temp_dir / f"{camera['id']}.jpg"
                with open(temp_file, 'wb') as f:
                    f.write(response.content)

                counts = self.detect_vehicles(str(temp_file), camera['id'])

                timestamp = datetime.now().strftime('%H:%M:%S')
                logging.info(
                    f"{timestamp} | {camera['name']}: {counts['total']} moving vehicles "
                    f"(cars: {counts['cars']}, buses: {counts['buses']})"
                )

                self.db.insert_detection(
                    datetime.now().isoformat(),
                    camera['id'],
                    camera['name'],
                    counts
                )

                return counts

        except Exception as e:
            logging.error(f"Error with {camera['name']}: {e}")
            return None

    def run(self):
        logging.info("=" * 70)
        logging.info("Monitoring System Started")
        logging.info("=" * 70)

        try:
            while True:
                start_time = time.time()

                with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.cameras)) as executor:
                    executor.map(self.collect_from_camera, self.cameras)

                elapsed = time.time() - start_time
                logging.info(f"--- Cycle completed in {elapsed:.2f}s ---\n")

                sleep_time = max(0, self.interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            logging.info("\n" + "=" * 70)
            logging.info("Collection stopped by user")
            logging.info("=" * 70)


if __name__ == "__main__":
    collector = TrafficCollector()
    collector.run()