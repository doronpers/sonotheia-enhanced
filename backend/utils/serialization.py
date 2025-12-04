"""
Centralized serialization utilities for the Sonotheia backend.

This module provides utilities for converting numpy types to native Python types
for JSON serialization. Scientific audio libraries (numpy, scipy, librosa) return
data types like numpy.float32 or numpy.int64, which standard Python json.dumps
(and by extension FastAPI) cannot serialize.

NOTE: When returning API responses that contain sensor results or numpy values,
always use convert_numpy_types() to convert numpy types (np.float64, np.int32, etc.)
to native Python types before JSON serialization.
"""

from typing import Any
import numpy as np


def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert numpy types to Python native types for JSON serialization.

    This function handles:
    - np.integer/np.floating -> int/float
    - np.ndarray -> list
    - np.bool_ -> bool
    - Nested dicts and lists

    Args:
        obj: Any Python object that may contain numpy types

    Returns:
        Object with all numpy types converted to native Python types

    Examples:
        >>> import numpy as np
        >>> convert_numpy_types(np.float32(1.5))
        1.5
        >>> convert_numpy_types({"value": np.int64(10)})
        {"value": 10}
        >>> convert_numpy_types([np.float64(1.0), np.int32(2)])
        [1.0, 2]
    """
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj
