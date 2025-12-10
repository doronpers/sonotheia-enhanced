
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.utils.config import get_sensor_thresholds, get_threshold

print("Debug Config Loading:")
try:
    thresholds = get_sensor_thresholds()
    print(f"Loaded all thresholds keys: {list(thresholds.keys())}")
    
    pv = thresholds.get('pitch_velocity', {})
    print(f"Pitch Velocity Config: {pv}")
    
    val = get_threshold("pitch_velocity", "max_velocity_threshold", 999.0)
    print(f"get_threshold value: {val}")
    
except Exception as e:
    print(f"Error: {e}")
