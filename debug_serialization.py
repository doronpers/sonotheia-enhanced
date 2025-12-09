
import sys
import os
import json
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path.cwd()))

try:
    from backend.utils.serialization import convert_numpy_types
    print("Successfully imported convert_numpy_types")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_serialization():
    data = {
        "float32": np.float32(0.95),
        "int64": np.int64(42),
        "nested": {
            "array": np.array([1.0, 2.0], dtype=np.float32),
            "score": np.float32(0.123)
        }
    }
    
    print(f"Original types: {type(data['float32'])}")
    
    try:
        cleaned = convert_numpy_types(data)
        print("Conversion successful")
        print(f"Converted float32 type: {type(cleaned['float32'])}")
        
        json_output = json.dumps(cleaned, indent=2)
        print("JSON dumps successful:")
        print(json_output)
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_serialization()
