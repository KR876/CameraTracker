# CameraTracker

A Python system that automatically fetches frames from Tallinn traffic cameras, detects and counts vehicles using YOLOv8, and stores the results in a SQLite database for traffic pattern analysis.

## Features

- **Live image fetching**: pulls JPEG frames directly from `ristmikud.tallinn.ee` camera URLs
- **YOLOv8 object detection**: detects and counts vehicles in each frame
- **Parked vehicle filtering**: tracks bounding boxes across frames, excludes stationary vehicles from counts
- **SQLite storage**: every detection is logged with camera ID, timestamp, and vehicle type breakdown
- **CLI statistics**: per-camera averages, hourly breakdowns, and peak traffic events

## Monitored Cameras

5 Tallinn intersections configured by default:

- Viru väljak
- Estonia pst
- Pärnu mnt
- Ahtri tn
- Reidi tee

## Usage

```bash
pip install ultralytics requests

# Start collecting data
python scripts/start_collection.py

# View statistics
python scripts/view_stats.py
```

## Database Schema

```sql
CREATE TABLE detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    camera_id TEXT NOT NULL,
    camera_name TEXT,
    vehicle_count INTEGER,
    cars INTEGER,
    buses INTEGER
);
```

Indexed on `camera_id` and `timestamp` for fast querying.

## How It Works

**Image fetching** — each camera serves a JPEG at a static URL that refreshes every ~3 seconds. The collector downloads frames via HTTP GET with no browser required.

**Detection** — YOLOv8l runs on each frame, filtering COCO classes down to cars, buses, and trucks.

**Parked vehicle filtering** — each detected vehicle gets a tracking object. If its bounding box remains unchanged for `N` consecutive frames, it is marked as stationary and excluded from the active count.

**Collection interval** — configurable in `config/cameras.json`, default is 3 seconds per camera.

## Tech Stack

- Python 3.10+
- [YOLOv8](https://github.com/ultralytics/ultralytics) (`ultralytics`)
- `requests`, `Pillow`
- SQLite (`sqlite3`)
