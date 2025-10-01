"""
Custom exception classes for the Spelling Bee Solver.

This module defines a comprehensive hierarchy of specific exceptions that provide
better error handling, more informative error messages, and improved debugging
capabilities throughout the Spelling Bee Solver application.

The exception hierarchy follows Python best practices with a common base exception
and specialized subclasses for different types of errors. Each exception includes
context-specific information to aid in troubleshooting and error recovery.

Exception Hierarchy:
    SpellingBeeSolverError (Base)
    ├── InvalidInputError (User input validation)
    ├── ConfigurationError (Configuration file issues)
    ├── DictionaryError (Dictionary loading/processing)
    ├── GPUError (GPU and CUDA operations)
    ├── NetworkError (HTTP downloads and connectivity)
    └── CacheError (File caching operations)

Design Principles:
    - Specific exception types for different failure modes
    - Rich context information for debugging
    - Optional details parameter for additional information
    - Consistent error message formatting
    - Easy integration with logging systems

Usage Examples:
    Input validation::

        try:
            solver.solve_puzzle("", "")
        except InvalidInputError as e:
            print(f"Invalid input: {e.message}")
            if e.input_value:
                print(f"Problematic value: {e.input_value}")

    Configuration handling::

        try:
            config = load_config("missing.json")
        except ConfigurationError as e:
            print(f"Config error: {e.message}")
            if e.config_path:
                print(f"Config file: {e.config_path}")

    Network operations::

        try:
            words = download_dictionary(url)
        except NetworkError as e:
            print(f"Download failed: {e.message}")
            if e.url and e.status_code:
                print(f"URL: {e.url}, Status: {e.status_code}")

Error Context:
    Each exception type captures relevant context information:

    - InvalidInputError: The problematic input value
    - ConfigurationError: Path to the configuration file
    - DictionaryError: Path to the dictionary file
    - GPUError: GPU device and operation details
    - NetworkError: URL and HTTP status code
    - CacheError: Cache file path and operation type

Integration:
    These exceptions integrate seamlessly with Python's exception handling:

    - Can be caught individually or by base class
    - Work with try/except/finally blocks
    - Support exception chaining with 'from' clause
    - Compatible with logging frameworks
    - Provide structured error information for error reporting

Author: Tom's Enhanced Spelling Bee Solver
Version: 2.0
"""

from typing import Optional


class SpellingBeeSolverError(Exception):
    """Base exception class for all Spelling Bee Solver errors.

    Serves as the root of the exception hierarchy and provides common functionality
    for all solver-related exceptions. Includes support for both simple error
    messages and detailed context information.

    Attributes:
        message (str): Primary error message describing what went wrong.
        details (Optional[str]): Additional context information for debugging.
            May include file paths, configuration values, or other relevant data.

    Args:
        message (str): Clear, user-friendly description of the error.
        details (Optional[str]): Optional additional context information.

    Example:
        Basic usage::

            raise SpellingBeeSolverError("Operation failed")

        With details::

            raise SpellingBeeSolverError(
                "Configuration invalid",
                "Missing required section: solver"
            )

    Note:
        This base class should generally not be raised directly. Instead, use
        one of the specific subclasses that provide more targeted error handling.
    """

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class InvalidInputError(SpellingBeeSolverError):
    """Raised when input parameters are invalid or malformed.

    This exception is thrown when user-provided input fails validation checks.
    Common scenarios include incorrect puzzle letter counts, non-alphabetic
    characters, empty strings, or values outside expected ranges.

    Attributes:
        input_value (Optional[str]): The problematic input value that caused
            the validation failure. Useful for debugging and user feedback.

    Args:
        message (str): Description of why the input is invalid.
        input_value (Optional[str]): The actual input value that failed validation.

    Example:
        Letter count validation::

            if len(letters) != 7:
                raise InvalidInputError(
                    f"Expected 7 letters, got {len(letters)}",
                    input_value=letters
                )

        Character validation::

            if not letters.isalpha():
                raise InvalidInputError(
                    "Letters must contain only alphabetic characters",
                    input_value=letters
                )

    Use Cases:
        - Puzzle letter validation (count, characters, format)
        - Required letter validation
        - Configuration parameter validation
        - User interface input validation
    """

    def __init__(self, message: str, input_value: Optional[str] = None):
        self.input_value = input_value
        details = f"Input: {input_value}" if input_value else None
        super().__init__(message, details)


class ConfigurationError(SpellingBeeSolverError):
    """Raised when configuration is invalid, missing, or corrupted.

    This exception indicates problems with configuration files, missing required
    settings, invalid configuration values, or JSON parsing errors.

    Attributes:
        config_path (Optional[str]): Path to the configuration file that caused
            the error. Helps identify which config file needs attention.

    Args:
        message (str): Description of the configuration problem.
        config_path (Optional[str]): Path to the problematic configuration file.

    Example:
        Missing configuration file::

            if not config_file.exists():
                raise ConfigurationError(
                    "Configuration file not found",
                    config_path=str(config_file)
                )

        Invalid JSON::

            try:
                config = json.load(f)
            except json.JSONDecodeError as e:
                raise ConfigurationError(
                    f"Invalid JSON in configuration: {e}",
                    config_path=config_path
                ) from e

    Use Cases:
        - Missing configuration files
        - JSON parsing errors
        - Invalid configuration values
        - Missing required configuration sections
        - Configuration schema validation failures
    """

    def __init__(self, message: str, config_path: Optional[str] = None):
        self.config_path = config_path
        details = f"Config path: {config_path}" if config_path else None
        super().__init__(message, details)


class DictionaryError(SpellingBeeSolverError):
    """Raised when dictionary operations fail.

    This exception covers all dictionary-related failures including file loading
    errors, format problems, corruption detection, and processing failures.

    Attributes:
        dictionary_path (Optional[str]): Path to the dictionary file that caused
            the error. May be a local file path or URL.

    Args:
        message (str): Description of the dictionary operation that failed.
        dictionary_path (Optional[str]): Path or URL of the problematic dictionary.

    Example:
        File not found::

            if not dict_file.exists():
                raise DictionaryError(
                    "Dictionary file not found",
                    dictionary_path=str(dict_file)
                )

        Corrupted content::

            if file_size < 1000:
                raise DictionaryError(
                    f"Dictionary file too small ({file_size} bytes), possibly corrupted",
                    dictionary_path=dict_path
                )

    Use Cases:
        - Missing dictionary files
        - File permission errors
        - Corrupted or truncated files
        - Invalid file formats
        - Encoding problems
        - URL download failures
    """

    def __init__(self, message: str, dictionary_path: Optional[str] = None):
        self.dictionary_path = dictionary_path
        details = f"Dictionary: {dictionary_path}" if dictionary_path else None
        super().__init__(message, details)


class GPUError(SpellingBeeSolverError):
    """Raised when GPU operations fail.

    This exception handles all GPU and CUDA-related failures including device
    initialization errors, memory allocation failures, kernel execution problems,
    and driver compatibility issues.

    Attributes:
        gpu_details (Optional[str]): Additional information about the GPU
            operation or device state that caused the error.

    Args:
        message (str): Description of the GPU operation that failed.
        gpu_details (Optional[str]): Additional context about GPU state or operation.

    Example:
        CUDA initialization::

            try:
                device = cp.cuda.Device()
            except Exception as e:
                raise GPUError(
                    "CUDA device initialization failed",
                    gpu_details=f"Error: {e}, Available devices: {cp.cuda.runtime.getDeviceCount()}"
                ) from e

        Memory allocation::

            if not enough_memory:
                raise GPUError(
                    "Insufficient GPU memory for operation",
                    gpu_details=f"Required: {required_mb}MB, Available: {available_mb}MB"
                )

    Use Cases:
        - CUDA initialization failures
        - GPU memory allocation errors
        - Kernel execution failures
        - Driver compatibility problems
        - Device capability mismatches
        - GPU timeout errors
    """

    def __init__(self, message: str, gpu_details: Optional[str] = None):
        self.gpu_details = gpu_details
        super().__init__(message, gpu_details)


class NetworkError(SpellingBeeSolverError):
    """Raised when network operations fail.

    This exception handles all network-related failures including HTTP download
    errors, connection timeouts, DNS resolution failures, and HTTP status errors.

    Attributes:
        url (Optional[str]): The URL that caused the network error.
        status_code (Optional[int]): HTTP status code if applicable.

    Args:
        message (str): Description of the network operation that failed.
        url (Optional[str]): The URL involved in the failed operation.
        status_code (Optional[int]): HTTP status code for HTTP-related errors.

    Example:
        HTTP download failure::

            response = requests.get(url)
            if response.status_code != 200:
                raise NetworkError(
                    f"HTTP download failed: {response.reason}",
                    url=url,
                    status_code=response.status_code
                )

        Connection timeout::

            try:
                response = requests.get(url, timeout=30)
            except requests.Timeout:
                raise NetworkError(
                    "Request timed out",
                    url=url
                ) from e

    Use Cases:
        - HTTP download failures
        - Connection timeouts
        - DNS resolution errors
        - SSL/TLS certificate problems
        - HTTP status errors (404, 500, etc.)
        - Network connectivity issues
    """

    def __init__(
        self, message: str, url: Optional[str] = None, status_code: Optional[int] = None
    ):
        self.url = url
        self.status_code = status_code
        details = f"URL: {url}, Status: {status_code}" if url else None
        super().__init__(message, details)


class CacheError(SpellingBeeSolverError):
    """Raised when cache operations fail.

    This exception handles failures in file caching operations including cache
    directory creation, file write errors, cache corruption, and cleanup failures.

    Attributes:
        cache_path (Optional[str]): Path to the cache file or directory that
            caused the error.

    Args:
        message (str): Description of the cache operation that failed.
        cache_path (Optional[str]): Path to the problematic cache file or directory.

    Example:
        Cache write failure::

            try:
                with open(cache_path, 'w') as f:
                    f.write(content)
            except OSError as e:
                raise CacheError(
                    f"Failed to write cache file: {e}",
                    cache_path=cache_path
                ) from e

        Cache directory creation::

            try:
                cache_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise CacheError(
                    "Permission denied creating cache directory",
                    cache_path=str(cache_dir)
                )

    Use Cases:
        - Cache file write failures
        - Cache directory creation errors
        - Permission denied errors
        - Disk space exhaustion
        - Cache corruption detection
        - Cache cleanup failures
    """

    def __init__(self, message: str, cache_path: Optional[str] = None):
        self.cache_path = cache_path
        details = f"Cache path: {cache_path}" if cache_path else None
        super().__init__(message, details)
