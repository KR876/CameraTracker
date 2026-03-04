CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    camera_id TEXT NOT NULL,
    camera_name TEXT,
    vehicle_count INTEGER,
    cars INTEGER,
    buses INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_timestamp ON detections(timestamp);
CREATE INDEX IF NOT EXISTS idx_camera ON detections(camera_id);
CREATE INDEX IF NOT EXISTS idx_camera_timestamp ON detections(camera_id, timestamp);