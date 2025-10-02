"""
GPU acceleration modules for enhanced performance.

This subpackage contains GPU-accelerated components for:
- GPU word filtering with spaCy
"""

from .gpu_word_filtering import GPUWordFilter, get_gpu_filter

__all__ = [
    "GPUWordFilter",
    "get_gpu_filter",
]
