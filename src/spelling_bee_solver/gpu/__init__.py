"""
GPU acceleration modules for enhanced performance.

This subpackage contains GPU-accelerated components for:
- CUDA-enabled NLTK processing
- GPU word filtering with spaCy
- Multi-tier GPU puzzle solving
"""

from .cuda_nltk import CudaNLTKProcessor, get_cuda_nltk_processor
from .gpu_puzzle_solver import GPUPuzzleSolver
from .gpu_word_filtering import GPUWordFilter, get_gpu_filter

__all__ = [
    "get_cuda_nltk_processor",
    "CudaNLTKProcessor",
    "GPUWordFilter",
    "get_gpu_filter",
    "GPUPuzzleSolver",
]
