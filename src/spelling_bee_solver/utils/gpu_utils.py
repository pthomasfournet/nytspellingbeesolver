"""GPU acceleration utilities for NYT Spelling Bee Solver.

This module provides centralized GPU detection and utilities for:
- cuDF (RAPIDS): GPU-accelerated string operations and DataFrames
- CuPy: GPU-accelerated numerical operations

Automatically detects GPU availability and provides fallback to CPU
when GPU is not available or when batch size is too small for GPU benefits.

Example:
    >>> from spelling_bee_solver.utils import gpu_utils
    >>>
    >>> if gpu_utils.GPU_AVAILABLE:
    ...     print(f"GPU detected: {gpu_utils.get_gpu_info()}")
    >>>
    >>> # Filter candidates on GPU
    >>> filtered = gpu_utils.filter_strings_gpu(
    ...     words, min_length=4, required_char='a'
    ... )
"""

import logging
from typing import List, Optional, Set

logger = logging.getLogger(__name__)

# GPU detection and configuration
GPU_AVAILABLE = False
GPU_BATCH_SIZE = 10000  # Optimal batch size for GPU operations
GPU_MIN_BATCH_SIZE = 1000  # Minimum batch size for GPU benefit (below this, CPU is faster)

try:
    import cudf
    import cupy as cp
    import pandas as pd

    GPU_AVAILABLE = True
    logger.debug("GPU acceleration enabled (cuDF + CuPy)")

except ImportError as e:
    logger.debug(f"GPU acceleration disabled: {e}")
    GPU_AVAILABLE = False


def get_gpu_info() -> dict:
    """Get information about available GPU.

    Returns:
        Dictionary with GPU information, or empty dict if no GPU available
    """
    if not GPU_AVAILABLE:
        return {}

    try:
        import cupy as cp

        device = cp.cuda.Device()
        props = cp.cuda.runtime.getDeviceProperties(device.id)

        return {
            'name': props['name'].decode() if isinstance(props['name'], bytes) else props['name'],
            'compute_capability': f"{props['major']}.{props['minor']}",
            'total_memory_gb': props['totalGlobalMem'] / (1024**3),
            'multiprocessor_count': props['multiProcessorCount'],
            'cuda_cores': _estimate_cuda_cores(props['major'], props['multiProcessorCount']),
        }
    except Exception as e:
        logger.debug(f"Failed to get GPU info: {e}")
        return {}


def _estimate_cuda_cores(compute_capability_major: int, mp_count: int) -> int:
    """Estimate number of CUDA cores based on compute capability.

    Args:
        compute_capability_major: Major version of compute capability
        mp_count: Number of multiprocessors

    Returns:
        Estimated CUDA core count
    """
    # Cores per multiprocessor by compute capability
    cores_per_mp = {
        2: 32,   # Fermi
        3: 192,  # Kepler
        5: 128,  # Maxwell
        6: 64,   # Pascal (GP100), 128 (GP10x)
        7: 64,   # Volta/Turing
        8: 64,   # Ampere (GA100), 128 (GA10x)
        9: 128,  # Hopper
    }

    return cores_per_mp.get(compute_capability_major, 64) * mp_count


def should_use_gpu(data_size: int, min_size: int = GPU_MIN_BATCH_SIZE) -> bool:
    """Determine if GPU acceleration should be used for given data size.

    GPU has overhead from data transfer (CPU ↔ GPU). For small datasets,
    CPU is actually faster. Only use GPU for large batches.

    Args:
        data_size: Number of items to process
        min_size: Minimum size to benefit from GPU (default: 1000)

    Returns:
        True if GPU should be used
    """
    return GPU_AVAILABLE and data_size >= min_size


def filter_strings_gpu(
    words: List[str],
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    required_char: Optional[str] = None,
    allowed_chars: Optional[Set[str]] = None,
    batch_size: int = GPU_BATCH_SIZE
) -> List[str]:
    """GPU-accelerated string filtering with cuDF.

    Filters a list of strings based on multiple criteria using vectorized
    GPU operations. Automatically falls back to CPU for small batches.

    Args:
        words: List of strings to filter
        min_length: Minimum string length (inclusive)
        max_length: Maximum string length (inclusive)
        required_char: Character that must be present
        allowed_chars: Set of allowed characters (all chars must be in this set)
        batch_size: GPU batch size (default: 10000)

    Returns:
        Filtered list of strings

    Example:
        >>> words = ['apple', 'bat', 'count', 'dog', 'elephant']
        >>> filter_strings_gpu(words, min_length=4, required_char='o')
        ['count', 'dog']
    """
    if not should_use_gpu(len(words)):
        # CPU fallback for small batches
        return _filter_strings_cpu(
            words, min_length, max_length, required_char, allowed_chars
        )

    import cudf

    results = []

    # Process in batches to manage GPU memory
    for i in range(0, len(words), batch_size):
        batch = words[i:i + batch_size]

        # Create GPU DataFrame
        df = cudf.DataFrame({'word': batch})

        # Apply filters
        if min_length is not None:
            df = df[df['word'].str.len() >= min_length]

        if max_length is not None:
            df = df[df['word'].str.len() <= max_length]

        if required_char is not None:
            df = df[df['word'].str.contains(required_char, regex=False)]

        # Transfer to CPU and convert to list
        batch_results = df['word'].to_pandas().tolist()

        # Character set filtering (CPU - complex for GPU)
        if allowed_chars is not None:
            batch_results = [
                word for word in batch_results
                if set(word).issubset(allowed_chars)
            ]

        results.extend(batch_results)

    return results


def _filter_strings_cpu(
    words: List[str],
    min_length: Optional[int],
    max_length: Optional[int],
    required_char: Optional[str],
    allowed_chars: Optional[Set[str]]
) -> List[str]:
    """CPU fallback for string filtering.

    Used when GPU is unavailable or batch is too small for GPU benefit.
    """
    results = []

    for word in words:
        # Length checks
        if min_length is not None and len(word) < min_length:
            continue
        if max_length is not None and len(word) > max_length:
            continue

        # Required character
        if required_char is not None and required_char not in word:
            continue

        # Allowed characters
        if allowed_chars is not None and not set(word).issubset(allowed_chars):
            continue

        results.append(word)

    return results


def batch_set_membership_gpu(
    words: List[str],
    target_set: Set[str],
    batch_size: int = GPU_BATCH_SIZE
) -> List[bool]:
    """GPU-accelerated set membership checking.

    Check if each word in a list is present in a target set using
    vectorized GPU operations.

    Args:
        words: List of words to check
        target_set: Set to check membership against
        batch_size: GPU batch size

    Returns:
        List of boolean values indicating membership

    Example:
        >>> words = ['apple', 'banana', 'cherry']
        >>> valid_set = {'apple', 'cherry', 'date'}
        >>> batch_set_membership_gpu(words, valid_set)
        [True, False, True]
    """
    if not should_use_gpu(len(words)):
        # CPU fallback
        return [word in target_set for word in words]

    import cudf

    results = []

    # Convert set to GPU Series once (amortize cost)
    target_series = cudf.Series(list(target_set))

    # Process in batches
    for i in range(0, len(words), batch_size):
        batch = words[i:i + batch_size]

        # Create GPU DataFrame
        df = cudf.DataFrame({'word': batch})

        # Check membership
        df['in_set'] = df['word'].isin(target_series)

        # Transfer to CPU
        batch_results = df['in_set'].to_pandas().tolist()
        results.extend(batch_results)

    return results


def log_gpu_status():
    """Log GPU availability and configuration to logger."""
    if GPU_AVAILABLE:
        info = get_gpu_info()
        logger.info("✓ GPU acceleration ENABLED (cuDF + CuPy)")
        if info:
            logger.info(f"  GPU: {info.get('name', 'Unknown')}")
            logger.info(f"  CUDA cores: {info.get('cuda_cores', 'Unknown'):,}")
            logger.info(f"  Memory: {info.get('total_memory_gb', 0):.1f} GB")
            logger.info(f"  Batch size: {GPU_BATCH_SIZE:,} items")
    else:
        logger.info("✗ GPU acceleration disabled (CPU mode)")
