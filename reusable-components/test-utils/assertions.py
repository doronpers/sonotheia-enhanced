"""
Assertion helpers for testing.

Provides reusable assertion patterns for common test scenarios.
"""

from typing import Dict, List, Any, Optional, Union


class AssertHelpers:
    """
    Reusable assertion patterns for testing.
    
    Static methods provide consistent assertion logic across tests.
    
    Example:
        def test_sensor_result():
            result = sensor.analyze(data, context)
            AssertHelpers.assert_sensor_result_valid(result)
            AssertHelpers.assert_value_in_range(result.value, 0.0, 1.0)
    """
    
    @staticmethod
    def assert_sensor_result_valid(result: Any) -> None:
        """
        Assert that a SensorResult has valid structure.
        
        Args:
            result: Object to validate (should have sensor result attributes)
        
        Raises:
            AssertionError: If result is missing required attributes or has invalid types
        
        Example:
            result = sensor.analyze(data, context)
            AssertHelpers.assert_sensor_result_valid(result)
        """
        required_attrs = ["sensor_name", "value", "threshold"]
        for attr in required_attrs:
            assert hasattr(result, attr), f"Missing attribute: {attr}"
        
        assert isinstance(result.value, (int, float)), f"value must be numeric, got {type(result.value)}"
        assert isinstance(result.threshold, (int, float)), f"threshold must be numeric, got {type(result.threshold)}"
        
        if hasattr(result, "passed") and result.passed is not None:
            assert isinstance(result.passed, bool), f"passed must be bool or None, got {type(result.passed)}"
    
    @staticmethod
    def assert_dict_contains_keys(d: Dict, keys: List[str]) -> None:
        """
        Assert that a dictionary contains all specified keys.
        
        Args:
            d: Dictionary to check
            keys: List of required keys
        
        Raises:
            AssertionError: If any key is missing
        
        Example:
            AssertHelpers.assert_dict_contains_keys(
                response,
                ["verdict", "detail", "evidence"]
            )
        """
        for key in keys:
            assert key in d, f"Missing key: '{key}' in dictionary"
    
    @staticmethod
    def assert_value_in_range(
        value: float,
        min_val: float,
        max_val: float,
        inclusive: bool = True,
        field_name: str = "value",
    ) -> None:
        """
        Assert that a value is within a specified range.
        
        Args:
            value: Value to check
            min_val: Minimum of range
            max_val: Maximum of range
            inclusive: If True, range includes endpoints
            field_name: Name for error messages
        
        Raises:
            AssertionError: If value is outside range
        
        Example:
            AssertHelpers.assert_value_in_range(score, 0.0, 1.0, field_name="score")
        """
        if inclusive:
            assert min_val <= value <= max_val, (
                f"{field_name} {value} not in range [{min_val}, {max_val}]"
            )
        else:
            assert min_val < value < max_val, (
                f"{field_name} {value} not in range ({min_val}, {max_val})"
            )
    
    @staticmethod
    def assert_api_response_structure(
        response: Dict,
        required_fields: Optional[List[str]] = None,
    ) -> None:
        """
        Assert that an API response has the expected structure.
        
        Args:
            response: Response dictionary to check
            required_fields: Custom list of required fields
        
        Raises:
            AssertionError: If structure is invalid
        
        Example:
            response = client.post("/api/analyze", ...).json()
            AssertHelpers.assert_api_response_structure(response)
        """
        if required_fields is None:
            required_fields = ["verdict", "detail", "processing_time_seconds", "evidence"]
        
        AssertHelpers.assert_dict_contains_keys(response, required_fields)
        
        # Verify types if standard fields
        if "verdict" in response:
            assert isinstance(response["verdict"], str), "verdict must be string"
        if "detail" in response:
            assert isinstance(response["detail"], str), "detail must be string"
        if "processing_time_seconds" in response:
            assert isinstance(response["processing_time_seconds"], (int, float)), (
                "processing_time_seconds must be numeric"
            )
        if "evidence" in response:
            assert isinstance(response["evidence"], dict), "evidence must be dict"
    
    @staticmethod
    def assert_error_response(
        response: Dict,
        expected_type: Optional[str] = None,
    ) -> None:
        """
        Assert that an error response has valid structure.
        
        Args:
            response: Error response dictionary
            expected_type: Expected error type (optional)
        
        Raises:
            AssertionError: If error response is invalid
        
        Example:
            response = client.post("/api/analyze", ...).json()
            AssertHelpers.assert_error_response(response, expected_type="validation_error")
        """
        assert "error" in response, "Error response must have 'error' key"
        error = response["error"]
        
        assert "type" in error, "Error must have 'type'"
        assert "detail" in error or "message" in error, "Error must have 'detail' or 'message'"
        
        if expected_type:
            assert error["type"] == expected_type, (
                f"Expected error type '{expected_type}', got '{error['type']}'"
            )
    
    @staticmethod
    def assert_list_length(
        lst: List,
        expected_length: int = None,
        min_length: int = None,
        max_length: int = None,
        list_name: str = "list",
    ) -> None:
        """
        Assert that a list has expected length constraints.
        
        Args:
            lst: List to check
            expected_length: Exact expected length
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            list_name: Name for error messages
        
        Raises:
            AssertionError: If length constraints are violated
        
        Example:
            AssertHelpers.assert_list_length(items, min_length=1, max_length=100)
        """
        actual_length = len(lst)
        
        if expected_length is not None:
            assert actual_length == expected_length, (
                f"{list_name} length {actual_length} != expected {expected_length}"
            )
        
        if min_length is not None:
            assert actual_length >= min_length, (
                f"{list_name} length {actual_length} < minimum {min_length}"
            )
        
        if max_length is not None:
            assert actual_length <= max_length, (
                f"{list_name} length {actual_length} > maximum {max_length}"
            )
    
    @staticmethod
    def assert_type(
        obj: Any,
        expected_type: Union[type, tuple],
        field_name: str = "object",
    ) -> None:
        """
        Assert that an object is of expected type(s).
        
        Args:
            obj: Object to check
            expected_type: Expected type or tuple of types
            field_name: Name for error messages
        
        Raises:
            AssertionError: If type doesn't match
        
        Example:
            AssertHelpers.assert_type(result, SensorResult, "result")
            AssertHelpers.assert_type(value, (int, float), "value")
        """
        assert isinstance(obj, expected_type), (
            f"{field_name} must be {expected_type}, got {type(obj)}"
        )
    
    @staticmethod
    def assert_not_empty(
        obj: Any,
        field_name: str = "object",
    ) -> None:
        """
        Assert that an object is not empty.
        
        Works for strings, lists, dicts, and other containers.
        
        Args:
            obj: Object to check
            field_name: Name for error messages
        
        Raises:
            AssertionError: If object is empty
        
        Example:
            AssertHelpers.assert_not_empty(results, "results")
        """
        assert obj, f"{field_name} must not be empty"
        
        if hasattr(obj, "__len__"):
            assert len(obj) > 0, f"{field_name} must have length > 0"
