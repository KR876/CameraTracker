import sqlite3
from pathlib import Path


class DatabaseManager:
    def __init__(self, db_path='database/traffic.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create database and tables if they don't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)

        schema_path = Path(__file__).parent / 'schema.sql'
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())

        conn.close()

    def insert_detection(self, timestamp, camera_id, camera_name, counts):
        """Insert a detection record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO detections 
            (timestamp, camera_id, camera_name, vehicle_count, cars, buses)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            camera_id,
            camera_name,
            counts['total'],
            counts['cars'],
            counts['buses']
        ))
        conn.commit()
        conn.close()

    def get_stats(self):
        """Get basic statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM detections')
        total = cursor.fetchone()[0]

        cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM detections')
        date_range = cursor.fetchone()

        conn.close()

        return {
            'total_records': total,
            'start_date': date_range[0],
            'end_date': date_range[1]
        }