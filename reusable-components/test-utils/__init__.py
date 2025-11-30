"""
Test Utilities - Reusable testing patterns and helpers.

Collection of test utilities, fixtures, and patterns for comprehensive testing.
Originally designed for audio analysis systems but adaptable to other domains.

Exports:
    - AudioGenerator: Test audio data generation
    - AudioSpec: Audio specification dataclass
    - BoundaryTester: Boundary condition testing
    - EdgeCase: Edge case enumeration
    - EdgeCaseGenerator: Edge case data generation
    - AssertHelpers: Common assertion patterns
    - PerformanceTester: Performance testing utilities
"""

from .generators import AudioGenerator, AudioSpec
from .boundary import BoundaryTester
from .edge_cases import EdgeCase, EdgeCaseGenerator
from .assertions import AssertHelpers
from .performance import PerformanceTester

__all__ = [
    # Generators
    "AudioGenerator",
    "AudioSpec",
    # Testing patterns
    "BoundaryTester",
    "EdgeCase",
    "EdgeCaseGenerator",
    # Assertions
    "AssertHelpers",
    # Performance
    "PerformanceTester",
]

__version__ = "1.0.0"
