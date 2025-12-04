"""
Secure file handling utilities for the Sonotheia backend.

This module provides robust temporary file handling with proper
file descriptor management and secure cleanup to prevent leaks
and race conditions.
"""

import os
import tempfile
import logging
from contextlib import contextmanager
from typing import Iterator, Tuple, Optional

logger = logging.getLogger(__name__)


@contextmanager
def secure_tempfile(
    suffix: str = ".tmp",
    prefix: str = "sonotheia_",
    dir: Optional[str] = None,
) -> Iterator[Tuple[int, str]]:
    """
    Context manager for secure temporary file handling.

    Uses tempfile.mkstemp() for secure file creation and ensures proper
    cleanup of file descriptors and file paths in all cases (success or error).

    This avoids issues with NamedTemporaryFile on Windows and Docker containers
    related to file locking and cleanup.

    Args:
        suffix: File suffix/extension (e.g., ".wav", ".npy")
        prefix: File prefix (e.g., "sonotheia_", "calibration_")
        dir: Directory for the temporary file. Uses system temp if None.

    Yields:
        Tuple of (file_descriptor, file_path)

    Note:
        If you transfer the file descriptor to a file object using os.fdopen(),
        the fd becomes owned by that file object. When the context manager exits,
        it will safely attempt to close the fd, but this is handled gracefully
        if the fd was already closed (e.g., when the file object was closed or
        went out of scope).

    Example:
        with secure_tempfile(suffix=".wav", prefix="audio_") as (fd, path):
            # Option 1: Close fd first and use regular file operations
            os.close(fd)
            with open(path, 'wb') as f:
                f.write(audio_data)

            # Option 2: Use os.fdopen (fd ownership transfers to file object)
            with os.fdopen(fd, 'wb') as f:
                f.write(audio_data)
            # Process the file at 'path'
        # File is automatically cleaned up when exiting the context
    """
    fd: Optional[int] = None
    path: Optional[str] = None

    try:
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
        yield fd, path
    finally:
        # Always clean up the file descriptor if still open
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                # fd may already be closed (e.g., via os.fdopen)
                pass

        # Always clean up the file path if it exists
        if path is not None:
            try:
                if os.path.exists(path):
                    os.unlink(path)
                    logger.debug(f"Cleaned up temporary file: {path}")
            except OSError as e:
                logger.warning(f"Failed to clean up temporary file {path}: {e}")


@contextmanager
def secure_tempfile_write(
    suffix: str = ".tmp",
    prefix: str = "sonotheia_",
    dir: Optional[str] = None,
    mode: str = "wb",
) -> Iterator[Tuple[object, str]]:
    """
    Context manager for secure temporary file writing.

    Opens the temporary file for writing and yields the file object
    and path. Ensures proper cleanup of file handles and file paths.

    Args:
        suffix: File suffix/extension (e.g., ".wav", ".npy")
        prefix: File prefix (e.g., "sonotheia_", "calibration_")
        dir: Directory for the temporary file. Uses system temp if None.
        mode: File open mode (default: "wb" for binary write)

    Yields:
        Tuple of (file_object, file_path). The file object type depends
        on the mode: BinaryIO for binary modes, TextIO for text modes.

    Example:
        with secure_tempfile_write(suffix=".wav") as (f, path):
            f.write(audio_bytes)
        # File is closed and cleaned up when exiting the context
    """
    fd: Optional[int] = None
    path: Optional[str] = None
    file_obj = None

    try:
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
        # Transfer fd ownership to file object
        file_obj = os.fdopen(fd, mode)
        fd = None  # fd is now owned by file_obj
        yield file_obj, path
    finally:
        # Close the file object if open
        if file_obj is not None:
            try:
                file_obj.close()
            except (OSError, IOError) as e:
                logger.debug(f"Expected error closing file object: {e}")

        # Close fd if it wasn't transferred to file_obj
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass

        # Clean up the file path
        if path is not None:
            try:
                if os.path.exists(path):
                    os.unlink(path)
                    logger.debug(f"Cleaned up temporary file: {path}")
            except OSError as e:
                logger.warning(f"Failed to clean up temporary file {path}: {e}")


def cleanup_temp_file(path: str) -> None:
    """
    Clean up a temporary file.

    This is a standalone cleanup function for cases where the context
    manager pattern cannot be used (e.g., async operations across tasks).

    Args:
        path: Path to the temporary file
    """
    try:
        if os.path.exists(path):
            os.unlink(path)
            logger.debug(f"Cleaned up temporary file: {path}")
    except OSError as e:
        logger.warning(f"Failed to clean up temporary file {path}: {e}")


def secure_mkstemp(suffix: str = ".tmp", prefix: str = "sonotheia_") -> Tuple[int, str]:
    """
    Create a temporary file securely.

    This is a wrapper around tempfile.mkstemp() for cases where
    the context manager pattern cannot be used. Caller is responsible
    for cleanup using cleanup_temp_file().

    Args:
        suffix: File suffix/extension
        prefix: File prefix

    Returns:
        Tuple of (file_descriptor, file_path)
    """
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    return fd, path
