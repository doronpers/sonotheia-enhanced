"""
Core module initialization
"""
from .module_registry import ModuleRegistry, get_registry, is_module_enabled

__all__ = ['ModuleRegistry', 'get_registry', 'is_module_enabled']
