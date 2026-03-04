import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlite3
import os
from datetime import datetime

os.chdir(project_root)


def format_timestamp(ts):
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return ts


conn = sqlite3.connect('database/traffic.db')
cursor = conn.cursor()

print("=" * 80)
print(f"TALLINN TRAFFIC ANALYSIS")
print("=" * 80)

cursor.execute('SELECT COUNT(*) FROM detections')
total = cursor.fetchone()[0]

cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM detections')
date_range = cursor.fetchone()

print(f"\nData Collection:")
print(f"  Total records: {total:,}")
print(f"  First record:  {format_timestamp(date_range[0])}")
print(f"  Latest record: {format_timestamp(date_range[1])}")

if total == 0:
    print("\nNo data yet - run the collector first!")
    conn.close()
    exit()

print(f"\n{'Camera Performance':^80}")
print("-" * 80)
cursor.execute('''
    SELECT 
        camera_name,
        COUNT(*) as samples,
        AVG(vehicle_count) as avg_traffic,
        MAX(vehicle_count) as peak_traffic,
        SUM(vehicle_count) as total_vehicles
    FROM detections
    GROUP BY camera_name
    ORDER BY avg_traffic DESC
''')

print(f"{'Camera':<30} {'Samples':>10} {'Avg':>8} {'Peak':>8} {'Total':>10}")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row[0]:<30} {row[1]:>10,} {row[2]:>8.1f} {row[3]:>8} {row[4]:>10,}")

cursor.execute('SELECT COUNT(DISTINCT DATE(timestamp)) FROM detections')
days = cursor.fetchone()[0]

if days > 0:
    print(f"\n{'Traffic by Hour of Day':^80}")
    print("-" * 80)
    cursor.execute('''
        SELECT 
            CAST(strftime('%H', timestamp) AS INTEGER) as hour,
            AVG(vehicle_count) as avg_traffic,
            COUNT(*) as samples
        FROM detections
        GROUP BY hour
        ORDER BY hour
    ''')

    print(f"{'Hour':>6} {'Avg Traffic':>12} {'Samples':>10}")
    print("-" * 80)

    for row in cursor.fetchall():
        hour, avg_traffic, samples = row
        print(f"{hour:>6}:00 {avg_traffic:>12.1f} {samples:>10,}")

print(f"\n{'Peak Traffic Events (Top 10)':^80}")
print("-" * 80)
cursor.execute('''
    SELECT timestamp, camera_name, vehicle_count, cars, buses
    FROM detections
    ORDER BY vehicle_count DESC
    LIMIT 10
''')

print(f"{'Time':<20} {'Camera':<30} {'Total':>8} {'Cars':>6} {'Buses':>6}")
print("-" * 80)
for row in cursor.fetchall():
    time_str = format_timestamp(row[0])
    print(f"{time_str:<20} {row[1]:<30} {row[2]:>8} {row[3]:>6} {row[4]:>6}")

print(f"\n{'Vehicle Composition':^80}")
print("-" * 80)
cursor.execute('''
    SELECT 
        SUM(cars) as total_cars,
        SUM(buses) as total_buses,
        SUM(vehicle_count) as total_vehicles
    FROM detections
''')
row = cursor.fetchone()
total_cars, total_buses, total_vehicles = row
car_pct = (total_cars / total_vehicles * 100) if total_vehicles > 0 else 0
bus_pct = (total_buses / total_vehicles * 100) if total_vehicles > 0 else 0

print(f"  Cars:   {total_cars:>10,} ({car_pct:>5.1f}%)")
print(f"  Buses:  {total_buses:>10,} ({bus_pct:>5.1f}%)")
print(f"  Total:  {total_vehicles:>10,}")

print(f"\n{'Data Quality':^80}")
print("-" * 80)
cursor.execute('''
    SELECT 
        camera_name,
        COUNT(*) as samples,
        MIN(timestamp) as first_seen,
        MAX(timestamp) as last_seen
    FROM detections
    GROUP BY camera_name
''')

for row in cursor.fetchall():
    camera, samples, first, last = row
    first_time = format_timestamp(first).split()[1]
    last_time = format_timestamp(last).split()[1]
    print(f"{camera:<30} {samples:>6,} samples  ({first_time} to {last_time})")

conn.close()

print("\n" + "=" * 80)