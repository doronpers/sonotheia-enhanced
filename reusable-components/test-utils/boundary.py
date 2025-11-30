"""
Boundary testing utilities.

Provides systematic boundary condition testing patterns.
"""

from typing import Callable


class BoundaryTester:
    """
    Systematic boundary testing utility.
    
    Hybrid design: Static methods as pure testing functions.
    
    Example:
        def test_breath_sensor_boundaries():
            MAX_PHONATION = 14.0
            
            def test_phonation(duration):
                sensor = BreathSensor(max_phonation_seconds=MAX_PHONATION)
                audio = gen.sine_wave(440, duration, 16000)
                result = sensor.analyze(audio, 16000)
                return result.passed
            
            BoundaryTester.test_all_boundaries(
                test_phonation,
                threshold=MAX_PHONATION,
                passes_when_below=True
            )
    """
    
    @staticmethod
    def test_at_threshold(
        test_func: Callable[[float], bool],
        threshold: float,
        should_pass: bool = True,
        tolerance: float = 0.0,
    ) -> None:
        """
        Test behavior exactly at threshold.
        
        Args:
            test_func: Function that takes a value and returns pass/fail
            threshold: The threshold value to test
            should_pass: Expected result at threshold
            tolerance: Floating point tolerance
        
        Raises:
            AssertionError: If test fails
        
        Example:
            BoundaryTester.test_at_threshold(
                test_func=lambda x: x <= 14.0,
                threshold=14.0,
                should_pass=True
            )
        """
        result = test_func(threshold + tolerance)
        assert result == should_pass, (
            f"At threshold {threshold}: expected {should_pass}, got {result}"
        )
    
    @staticmethod
    def test_just_below_threshold(
        test_func: Callable[[float], bool],
        threshold: float,
        delta: float = 0.01,
        should_pass: bool = True,
    ) -> None:
        """
        Test behavior just below threshold.
        
        Args:
            test_func: Function that takes a value and returns pass/fail
            threshold: The threshold value
            delta: How far below threshold to test
            should_pass: Expected result below threshold
        
        Raises:
            AssertionError: If test fails
        
        Example:
            BoundaryTester.test_just_below_threshold(
                test_func=lambda x: x <= 14.0,
                threshold=14.0,
                should_pass=True
            )
        """
        result = test_func(threshold - delta)
        assert result == should_pass, (
            f"Just below threshold ({threshold - delta}): "
            f"expected {should_pass}, got {result}"
        )
    
    @staticmethod
    def test_just_above_threshold(
        test_func: Callable[[float], bool],
        threshold: float,
        delta: float = 0.01,
        should_pass: bool = False,
    ) -> None:
        """
        Test behavior just above threshold.
        
        Args:
            test_func: Function that takes a value and returns pass/fail
            threshold: The threshold value
            delta: How far above threshold to test
            should_pass: Expected result above threshold
        
        Raises:
            AssertionError: If test fails
        
        Example:
            BoundaryTester.test_just_above_threshold(
                test_func=lambda x: x <= 14.0,
                threshold=14.0,
                should_pass=False
            )
        """
        result = test_func(threshold + delta)
        assert result == should_pass, (
            f"Just above threshold ({threshold + delta}): "
            f"expected {should_pass}, got {result}"
        )
    
    @classmethod
    def test_all_boundaries(
        cls,
        test_func: Callable[[float], bool],
        threshold: float,
        passes_when_below: bool = True,
        delta: float = 0.01,
    ) -> None:
        """
        Run complete boundary test suite.
        
        Tests at, below, and above threshold with appropriate expectations.
        
        Args:
            test_func: Function that takes a value and returns pass/fail
            threshold: The threshold value to test around
            passes_when_below: If True, expects pass when value < threshold
            delta: Distance from threshold for above/below tests
        
        Raises:
            AssertionError: If any boundary test fails
        
        Example:
            BoundaryTester.test_all_boundaries(
                test_func=lambda x: sensor.check(x),
                threshold=14.0,
                passes_when_below=True
            )
        """
        if passes_when_below:
            cls.test_just_below_threshold(test_func, threshold, delta, should_pass=True)
            cls.test_at_threshold(test_func, threshold, should_pass=True)
            cls.test_just_above_threshold(test_func, threshold, delta, should_pass=False)
        else:
            cls.test_just_below_threshold(test_func, threshold, delta, should_pass=False)
            cls.test_at_threshold(test_func, threshold, should_pass=False)
            cls.test_just_above_threshold(test_func, threshold, delta, should_pass=True)
    
    @staticmethod
    def test_range(
        test_func: Callable[[float], bool],
        min_value: float,
        max_value: float,
        should_pass_in_range: bool = True,
        delta: float = 0.01,
    ) -> None:
        """
        Test that values within a range pass/fail as expected.
        
        Args:
            test_func: Function that takes a value and returns pass/fail
            min_value: Minimum of valid range
            max_value: Maximum of valid range
            should_pass_in_range: Expected result for values in range
            delta: Distance outside range to test
        
        Example:
            BoundaryTester.test_range(
                test_func=lambda x: 0 <= x <= 1.0,
                min_value=0.0,
                max_value=1.0,
                should_pass_in_range=True
            )
        """
        # Test below minimum
        result = test_func(min_value - delta)
        assert result != should_pass_in_range, (
            f"Below min ({min_value - delta}): should {'fail' if should_pass_in_range else 'pass'}"
        )
        
        # Test at minimum
        result = test_func(min_value)
        assert result == should_pass_in_range, (
            f"At min ({min_value}): expected {should_pass_in_range}, got {result}"
        )
        
        # Test middle
        middle = (min_value + max_value) / 2
        result = test_func(middle)
        assert result == should_pass_in_range, (
            f"At middle ({middle}): expected {should_pass_in_range}, got {result}"
        )
        
        # Test at maximum
        result = test_func(max_value)
        assert result == should_pass_in_range, (
            f"At max ({max_value}): expected {should_pass_in_range}, got {result}"
        )
        
        # Test above maximum
        result = test_func(max_value + delta)
        assert result != should_pass_in_range, (
            f"Above max ({max_value + delta}): should {'fail' if should_pass_in_range else 'pass'}"
        )
