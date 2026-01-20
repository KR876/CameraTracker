import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
os.chdir(project_root)

from data_collection.collector import TrafficCollector

if __name__ == "__main__":
    print("Traffic Monitoring System")
    print("=" * 50)
    collector = TrafficCollector()
    collector.run()