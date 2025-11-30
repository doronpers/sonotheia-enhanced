"""
Tests for Celery Utility Functions
Tests numpy serialization, task results, and helper functions.
"""

import pytest
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.celery_utils import (
    numpy_to_native,
    serialize_result,
    create_task_result,
    estimate_time_remaining,
    validate_audio_data,
)


class TestNumpyToNative:
    """Tests for numpy_to_native conversion function."""
    
    def test_numpy_array_to_list(self):
        """Test numpy array converts to list."""
        arr = np.array([1, 2, 3, 4, 5])
        result = numpy_to_native(arr)
        
        assert isinstance(result, list)
        assert result == [1, 2, 3, 4, 5]
    
    def test_numpy_2d_array_to_nested_list(self):
        """Test 2D numpy array converts to nested list."""
        arr = np.array([[1, 2], [3, 4]])
        result = numpy_to_native(arr)
        
        assert isinstance(result, list)
        assert result == [[1, 2], [3, 4]]
    
    def test_numpy_int_to_python_int(self):
        """Test numpy integer converts to Python int."""
        np_int = np.int64(42)
        result = numpy_to_native(np_int)
        
        assert isinstance(result, int)
        assert result == 42
    
    def test_numpy_float_to_python_float(self):
        """Test numpy float converts to Python float."""
        np_float = np.float64(3.14159)
        result = numpy_to_native(np_float)
        
        assert isinstance(result, float)
        assert abs(result - 3.14159) < 1e-5
    
    def test_numpy_bool_to_python_bool(self):
        """Test numpy bool converts to Python bool."""
        np_bool = np.bool_(True)
        result = numpy_to_native(np_bool)
        
        assert isinstance(result, bool)
        assert result is True
    
    def test_dict_with_numpy_values(self):
        """Test dict with numpy values gets fully converted."""
        data = {
            'array': np.array([1, 2, 3]),
            'scalar': np.float32(1.5),
            'nested': {
                'arr': np.array([4, 5])
            }
        }
        result = numpy_to_native(data)
        
        assert isinstance(result['array'], list)
        assert isinstance(result['scalar'], float)
        assert isinstance(result['nested']['arr'], list)
    
    def test_list_with_numpy_values(self):
        """Test list with numpy values gets fully converted."""
        data = [np.int32(1), np.float64(2.5), np.array([3, 4])]
        result = numpy_to_native(data)
        
        assert all(not isinstance(x, (np.ndarray, np.generic)) for x in result)
        assert result[0] == 1
        assert result[1] == 2.5
        assert result[2] == [3, 4]
    
    def test_datetime_to_isoformat(self):
        """Test datetime converts to ISO format string."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = numpy_to_native(dt)
        
        assert isinstance(result, str)
        assert "2024-01-15" in result
    
    def test_native_types_unchanged(self):
        """Test native Python types pass through unchanged."""
        data = {
            'string': 'hello',
            'int': 42,
            'float': 3.14,
            'bool': True,
            'none': None
        }
        result = numpy_to_native(data)
        
        assert result == data


class TestSerializeResult:
    """Tests for serialize_result function."""
    
    def test_serializes_numpy_in_result(self):
        """Test numpy arrays in result dict are serialized."""
        result = {
            'features': np.array([1.0, 2.0, 3.0]),
            'score': np.float64(0.85)
        }
        serialized = serialize_result(result)
        
        assert isinstance(serialized['features'], list)
        assert isinstance(serialized['score'], float)
        assert '_serialized_at' in serialized
    
    def test_adds_serialization_timestamp(self):
        """Test serialization adds timestamp."""
        result = {'data': 'test'}
        serialized = serialize_result(result)
        
        assert '_serialized_at' in serialized
        # Should be ISO format
        datetime.fromisoformat(serialized['_serialized_at'])


class TestCreateTaskResult:
    """Tests for create_task_result function."""
    
    def test_creates_completed_result(self):
        """Test creating a completed task result."""
        result = create_task_result(
            status='COMPLETED',
            data={'score': 0.95},
            message='Analysis complete'
        )
        
        assert result['status'] == 'COMPLETED'
        assert result['data']['score'] == 0.95
        assert result['message'] == 'Analysis complete'
        assert 'timestamp' in result
    
    def test_creates_failed_result(self):
        """Test creating a failed task result."""
        result = create_task_result(
            status='FAILED',
            error='Audio file corrupted'
        )
        
        assert result['status'] == 'FAILED'
        assert result['error'] == 'Audio file corrupted'
    
    def test_creates_processing_result_with_progress(self):
        """Test creating a processing result with progress."""
        result = create_task_result(
            status='PROCESSING',
            progress=45.5,
            message='Extracting features'
        )
        
        assert result['status'] == 'PROCESSING'
        assert result['progress'] == 45.5
        assert result['message'] == 'Extracting features'
    
    def test_converts_numpy_in_data(self):
        """Test numpy types in data are converted."""
        result = create_task_result(
            status='COMPLETED',
            data={'features': np.array([1, 2, 3])}
        )
        
        assert isinstance(result['data']['features'], list)


class TestEstimateTimeRemaining:
    """Tests for estimate_time_remaining function."""
    
    def test_estimates_remaining_time(self):
        """Test basic time estimation."""
        # 50% progress in 30 seconds -> 30 seconds remaining
        remaining = estimate_time_remaining(50.0, 30.0)
        assert abs(remaining - 30.0) < 0.1
    
    def test_handles_zero_progress(self):
        """Test with zero progress."""
        remaining = estimate_time_remaining(0.0, 10.0)
        assert remaining == 0.0
    
    def test_handles_complete_progress(self):
        """Test with 100% progress."""
        remaining = estimate_time_remaining(100.0, 60.0)
        assert remaining == 0.0
    
    def test_handles_high_progress(self):
        """Test with high progress percentage."""
        # 90% progress in 90 seconds -> ~10 seconds remaining
        remaining = estimate_time_remaining(90.0, 90.0)
        assert abs(remaining - 10.0) < 0.1


class TestValidateAudioData:
    """Tests for validate_audio_data function."""
    
    def test_validates_normal_audio(self):
        """Test validation passes for normal audio."""
        audio_data = b'\x00' * 1000  # 1KB of data
        result = validate_audio_data(audio_data)
        assert result is True
    
    def test_rejects_empty_audio(self):
        """Test validation fails for empty audio."""
        with pytest.raises(ValueError, match="empty"):
            validate_audio_data(b'')
    
    def test_rejects_oversized_audio(self):
        """Test validation fails for oversized audio."""
        # Create data larger than 15MB
        large_data = b'\x00' * (16 * 1024 * 1024)
        with pytest.raises(ValueError, match="exceeds maximum"):
            validate_audio_data(large_data)
    
    def test_custom_max_size(self):
        """Test validation with custom max size."""
        audio_data = b'\x00' * (2 * 1024 * 1024)  # 2MB
        
        # Should pass with 5MB limit
        result = validate_audio_data(audio_data, max_size_mb=5)
        assert result is True
        
        # Should fail with 1MB limit
        with pytest.raises(ValueError):
            validate_audio_data(audio_data, max_size_mb=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
