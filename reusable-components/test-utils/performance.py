"""
Performance testing utilities.

Provides tools for measuring and validating execution performance.
"""

import time
from typing import Callable, Any, Dict, Tuple, Optional, List

# Try to import numpy for statistics
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class PerformanceTester:
    """
    Performance testing utilities.
    
    Provides timing, benchmarking, and performance assertions.
    
    Example:
        def test_sensor_performance():
            sensor = BreathSensor()
            audio = gen.white_noise(60.0, 16000)
            
            # Assert completes in reasonable time
            result = PerformanceTester.assert_execution_time(
                sensor.analyze,
                max_seconds=5.0,
                audio_data=audio,
                samplerate=16000
            )
            
            # Benchmark
            stats = PerformanceTester.benchmark(
                sensor.analyze,
                iterations=10,
                audio_data=audio,
                samplerate=16000
            )
    """
    
    @staticmethod
    def measure_execution_time(
        func: Callable,
        *args,
        **kwargs,
    ) -> Tuple[Any, float]:
        """
        Measure function execution time.
        
        Args:
            func: Function to time
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
        
        Returns:
            Tuple of (function result, elapsed time in seconds)
        
        Example:
            result, elapsed = PerformanceTester.measure_execution_time(
                process_data,
                data=my_data
            )
            print(f"Took {elapsed:.3f}s")
        """
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        return result, elapsed
    
    @staticmethod
    def assert_execution_time(
        func: Callable,
        max_seconds: float,
        *args,
        **kwargs,
    ) -> Any:
        """
        Assert function completes within time limit.
        
        Args:
            func: Function to test
            max_seconds: Maximum allowed execution time
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
        
        Returns:
            Function result if it completes in time
        
        Raises:
            AssertionError: If execution exceeds max_seconds
        
        Example:
            result = PerformanceTester.assert_execution_time(
                analyze,
                max_seconds=5.0,
                data=test_data
            )
        """
        result, elapsed = PerformanceTester.measure_execution_time(func, *args, **kwargs)
        assert elapsed < max_seconds, (
            f"Execution took {elapsed:.2f}s, expected < {max_seconds}s"
        )
        return result
    
    @staticmethod
    def benchmark(
        func: Callable,
        iterations: int = 100,
        warmup: int = 5,
        *args,
        **kwargs,
    ) -> Dict[str, float]:
        """
        Benchmark function performance over multiple iterations.
        
        Args:
            func: Function to benchmark
            iterations: Number of timed iterations
            warmup: Number of warmup iterations (not timed)
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
        
        Returns:
            Dictionary with statistics (mean, median, min, max, std)
        
        Example:
            stats = PerformanceTester.benchmark(
                process,
                iterations=100,
                warmup=10,
                data=test_data
            )
            print(f"Mean: {stats['mean']:.3f}s")
        """
        # Warmup runs
        for _ in range(warmup):
            func(*args, **kwargs)
        
        # Timed runs
        times: List[float] = []
        for _ in range(iterations):
            _, elapsed = PerformanceTester.measure_execution_time(func, *args, **kwargs)
            times.append(elapsed)
        
        # Calculate statistics
        if HAS_NUMPY:
            return {
                "mean": float(np.mean(times)),
                "median": float(np.median(times)),
                "min": float(np.min(times)),
                "max": float(np.max(times)),
                "std": float(np.std(times)),
                "iterations": iterations,
            }
        else:
            # Fallback without numpy
            sorted_times = sorted(times)
            n = len(times)
            mean = sum(times) / n
            median = sorted_times[n // 2] if n % 2 == 1 else (sorted_times[n // 2 - 1] + sorted_times[n // 2]) / 2
            variance = sum((t - mean) ** 2 for t in times) / n
            std = variance ** 0.5
            
            return {
                "mean": mean,
                "median": median,
                "min": min(times),
                "max": max(times),
                "std": std,
                "iterations": iterations,
            }
    
    @staticmethod
    def profile_memory(
        func: Callable,
        *args,
        **kwargs,
    ) -> Tuple[Any, Optional[Dict[str, int]]]:
        """
        Profile memory usage of function execution.
        
        Requires tracemalloc module.
        
        Args:
            func: Function to profile
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Tuple of (function result, memory stats dict or None)
        
        Example:
            result, mem_stats = PerformanceTester.profile_memory(process, data=data)
            if mem_stats:
                print(f"Peak memory: {mem_stats['peak'] / 1024 / 1024:.1f} MB")
        """
        try:
            import tracemalloc
            
            tracemalloc.start()
            result = func(*args, **kwargs)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            return result, {
                "current_bytes": current,
                "peak_bytes": peak,
                "current_mb": current / 1024 / 1024,
                "peak_mb": peak / 1024 / 1024,
            }
        except ImportError:
            result = func(*args, **kwargs)
            return result, None
    
    @staticmethod
    def compare_implementations(
        implementations: Dict[str, Callable],
        iterations: int = 100,
        *args,
        **kwargs,
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare performance of multiple implementations.
        
        Args:
            implementations: Dict mapping name to callable
            iterations: Number of iterations per implementation
            *args: Arguments for all implementations
            **kwargs: Keyword arguments for all implementations
        
        Returns:
            Dict mapping implementation names to benchmark stats
        
        Example:
            results = PerformanceTester.compare_implementations(
                {
                    "naive": naive_impl,
                    "optimized": optimized_impl,
                    "vectorized": vectorized_impl,
                },
                iterations=100,
                data=test_data
            )
            
            for name, stats in results.items():
                print(f"{name}: {stats['mean']:.3f}s")
        """
        results = {}
        
        for name, func in implementations.items():
            stats = PerformanceTester.benchmark(func, iterations, *args, **kwargs)
            results[name] = stats
        
        return results
    
    @staticmethod
    def assert_faster_than(
        fast_func: Callable,
        slow_func: Callable,
        margin: float = 0.1,
        iterations: int = 20,
        *args,
        **kwargs,
    ) -> bool:
        """
        Assert that one function is faster than another.
        
        Args:
            fast_func: Function expected to be faster
            slow_func: Function expected to be slower
            margin: Required speedup margin (0.1 = 10% faster)
            iterations: Benchmark iterations
            *args: Arguments for both functions
            **kwargs: Keyword arguments for both functions
        
        Returns:
            True if assertion passes
        
        Raises:
            AssertionError: If fast_func is not faster by margin
        
        Example:
            PerformanceTester.assert_faster_than(
                optimized_impl,
                naive_impl,
                margin=0.2,  # 20% faster
                data=test_data
            )
        """
        fast_stats = PerformanceTester.benchmark(fast_func, iterations, *args, **kwargs)
        slow_stats = PerformanceTester.benchmark(slow_func, iterations, *args, **kwargs)
        
        fast_mean = fast_stats["mean"]
        slow_mean = slow_stats["mean"]
        
        assert fast_mean < slow_mean * (1 - margin), (
            f"Expected {fast_mean:.4f}s < {slow_mean * (1 - margin):.4f}s "
            f"(slow={slow_mean:.4f}s with {margin*100:.0f}% margin)"
        )
        
        return True
