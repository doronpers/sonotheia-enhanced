"""
NumPy Serialization Utilities

Helpers for converting numpy types to native Python for JSON serialization.
"""

import numpy as np
from typing import Any, Dict, List, Union


def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert numpy types to native Python types for JSON serialization.

    Args:
        obj: Object to convert (can be dict, list, numpy types, or primitives)

    Returns:
        Object with all numpy types converted to native Python types

    Example:
        >>> data = {"score": np.float64(0.95), "values": np.array([1, 2, 3])}
        >>> result = convert_numpy_types(data)
        >>> isinstance(result["score"], float)
        True
    """
    if obj is None:
        return None

    # Handle numpy scalar types
    if isinstance(obj, (np.integer, np.int_, np.int8, np.int16, np.int32, np.int64)):
        return int(obj)

    if isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
        return float(obj)

    if isinstance(obj, np.bool_):
        return bool(obj)

    if isinstance(obj, np.str_):
        return str(obj)

    # Handle numpy arrays
    if isinstance(obj, np.ndarray):
        return obj.tolist()

    # Handle dictionaries recursively
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}

    # Handle lists/tuples recursively
    if isinstance(obj, (list, tuple)):
        converted = [convert_numpy_types(item) for item in obj]
        return type(obj)(converted) if isinstance(obj, tuple) else converted

    # Return other types as-is
    return obj


def ensure_serializable(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure all values in a dictionary are JSON serializable.

    Wrapper around convert_numpy_types for convenience.

    Args:
        data: Dictionary to make serializable

    Returns:
        Dictionary with all values converted to JSON-serializable types
    """
    return convert_numpy_types(data)


def safe_array_to_list(arr: Union[np.ndarray, List, None]) -> List:
    """
    Safely convert array-like to list, handling None.

    Args:
        arr: Array to convert or None

    Returns:
        List or empty list if None
    """
    if arr is None:
        return []
    if isinstance(arr, np.ndarray):
        return arr.tolist()
    if isinstance(arr, (list, tuple)):
        return list(arr)
    return [arr]
