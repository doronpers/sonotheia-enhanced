"""
Edge case testing utilities.

Provides enumeration and generation of common edge cases.
"""

from enum import Enum
from typing import List, Tuple, Any

# Try to import numpy, but make it optional
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class EdgeCase(Enum):
    """
    Enumeration of common edge cases for testing.
    
    Each case represents a specific boundary or unusual input scenario.
    
    Example:
        @pytest.mark.parametrize("case,data", EdgeCaseGenerator.all_cases())
        def test_handles_edge_cases(case, data):
            result = my_function(data)
            assert result is not None
    """
    EMPTY = "empty"
    SINGLE_SAMPLE = "single_sample"
    VERY_SHORT = "very_short"
    VERY_LONG = "very_long"
    ALL_ZEROS = "all_zeros"
    ALL_ONES = "all_ones"
    CONSTANT = "constant"
    ALTERNATING = "alternating"
    DC_OFFSET = "dc_offset"
    NAN_VALUES = "nan_values"
    INF_VALUES = "inf_values"
    NEGATIVE_ONLY = "negative_only"
    MAX_VALUES = "max_values"


class EdgeCaseGenerator:
    """
    Generate edge case test data.
    
    Factory for creating arrays with specific edge case characteristics.
    Useful for parametrized testing.
    
    Example:
        @pytest.mark.parametrize("case,audio", EdgeCaseGenerator.all_cases())
        def test_sensor_handles_edge_cases(case, audio):
            sensor = MySensor()
            result = sensor.analyze(audio, 16000)
            assert result is not None
    """
    
    @staticmethod
    def generate(case: EdgeCase, samplerate: int = 16000) -> Any:
        """
        Generate data for a specific edge case.
        
        Args:
            case: The edge case to generate
            samplerate: Sample rate (for duration-based cases)
        
        Returns:
            numpy array with the specified edge case characteristics
        
        Example:
            empty_data = EdgeCaseGenerator.generate(EdgeCase.EMPTY)
            zeros = EdgeCaseGenerator.generate(EdgeCase.ALL_ZEROS, samplerate=16000)
        """
        if not HAS_NUMPY:
            raise ImportError("numpy is required for EdgeCaseGenerator")
        
        generators = {
            EdgeCase.EMPTY: lambda: np.array([], dtype=np.float32),
            EdgeCase.SINGLE_SAMPLE: lambda: np.array([0.5], dtype=np.float32),
            EdgeCase.VERY_SHORT: lambda: np.ones(10, dtype=np.float32) * 0.5,
            EdgeCase.VERY_LONG: lambda: np.ones(samplerate * 300, dtype=np.float32) * 0.5,
            EdgeCase.ALL_ZEROS: lambda: np.zeros(samplerate, dtype=np.float32),
            EdgeCase.ALL_ONES: lambda: np.ones(samplerate, dtype=np.float32),
            EdgeCase.CONSTANT: lambda: np.full(samplerate, 0.5, dtype=np.float32),
            EdgeCase.ALTERNATING: lambda: np.tile([1.0, -1.0], samplerate // 2).astype(np.float32),
            EdgeCase.DC_OFFSET: lambda: np.ones(samplerate, dtype=np.float32) * 0.5,
            EdgeCase.NAN_VALUES: lambda: np.array([np.nan, 0.5, np.nan, 0.5], dtype=np.float32),
            EdgeCase.INF_VALUES: lambda: np.array([np.inf, 0.5, -np.inf, 0.5], dtype=np.float32),
            EdgeCase.NEGATIVE_ONLY: lambda: -np.abs(np.random.randn(samplerate)).astype(np.float32),
            EdgeCase.MAX_VALUES: lambda: np.full(samplerate, np.finfo(np.float32).max, dtype=np.float32),
        }
        
        if case not in generators:
            raise ValueError(f"Unknown edge case: {case}")
        
        return generators[case]()
    
    @classmethod
    def all_cases(
        cls,
        samplerate: int = 16000,
        exclude: List[EdgeCase] = None,
    ) -> List[Tuple[EdgeCase, Any]]:
        """
        Generate all edge cases for parametrized testing.
        
        Args:
            samplerate: Sample rate for generated data
            exclude: List of cases to exclude
        
        Returns:
            List of (EdgeCase, data) tuples
        
        Example:
            @pytest.mark.parametrize("case,data", EdgeCaseGenerator.all_cases())
            def test_all_edges(case, data):
                # Test with each edge case
                pass
        """
        exclude = exclude or []
        
        return [
            (case, cls.generate(case, samplerate))
            for case in EdgeCase
            if case not in exclude
        ]
    
    @classmethod
    def safe_cases(cls, samplerate: int = 16000) -> List[Tuple[EdgeCase, Any]]:
        """
        Generate safe edge cases (no NaN, Inf, or extreme values).
        
        Useful for testing functions that may not handle special values.
        
        Args:
            samplerate: Sample rate for generated data
        
        Returns:
            List of (EdgeCase, data) tuples excluding problematic cases
        """
        unsafe = [
            EdgeCase.NAN_VALUES,
            EdgeCase.INF_VALUES,
            EdgeCase.MAX_VALUES,
        ]
        return cls.all_cases(samplerate, exclude=unsafe)
    
    @staticmethod
    def generate_custom(
        size: int,
        fill_value: float = 0.0,
        pattern: str = "constant",
    ) -> Any:
        """
        Generate custom edge case data with specific patterns.
        
        Args:
            size: Number of samples
            fill_value: Value to fill (for constant pattern)
            pattern: Pattern type ("constant", "linear", "random")
        
        Returns:
            numpy array with specified pattern
        
        Example:
            custom = EdgeCaseGenerator.generate_custom(1000, fill_value=0.5)
        """
        if not HAS_NUMPY:
            raise ImportError("numpy is required")
        
        if pattern == "constant":
            return np.full(size, fill_value, dtype=np.float32)
        elif pattern == "linear":
            return np.linspace(0, fill_value, size, dtype=np.float32)
        elif pattern == "random":
            return (np.random.randn(size) * fill_value).astype(np.float32)
        else:
            raise ValueError(f"Unknown pattern: {pattern}")
