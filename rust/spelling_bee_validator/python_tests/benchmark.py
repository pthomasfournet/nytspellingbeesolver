"""
Benchmark Rust vs Python InputValidator

Compares performance of Rust and Python implementations.
"""

import time
import statistics

# Try to import both implementations
try:
    from spelling_bee_validator import InputValidator as RustValidator
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    print("⚠️  Rust module not available. Build with: maturin develop")

try:
    import sys
    sys.path.insert(0, '/home/user/nytspellingbeesolver')
    from src.spelling_bee_solver.core.input_validator import InputValidator as PythonValidator
    PYTHON_AVAILABLE = True
except ImportError:
    PYTHON_AVAILABLE = False
    print("⚠️  Python module not available")


def benchmark_validate_letters(validator, iterations=10000):
    """Benchmark validate_letters method"""
    test_cases = [
        "NACUOTP",
        "ABCDEFG",
        "ZYXWVUT",
        "LMNOPQR",
        "RSTUVWX",
    ]

    start = time.perf_counter()
    for _ in range(iterations):
        for letters in test_cases:
            validator.validate_letters(letters)
    end = time.perf_counter()

    return end - start


def benchmark_validate_required_letter(validator, iterations=10000):
    """Benchmark validate_required_letter method"""
    test_cases = [
        ("N", "nacuotp"),
        ("A", "abcdefg"),
        ("Z", "zyxwvut"),
        ("L", "lmnopqr"),
    ]

    start = time.perf_counter()
    for _ in range(iterations):
        for required, letters in test_cases:
            validator.validate_required_letter(required, letters)
    end = time.perf_counter()

    return end - start


def benchmark_validate_and_normalize(validator, iterations=10000):
    """Benchmark validate_and_normalize method"""
    test_cases = [
        ("NACUOTP", "N"),
        ("ABCDEFG", "A"),
        ("ZYXWVUT", "Z"),
    ]

    start = time.perf_counter()
    for _ in range(iterations):
        for letters, required in test_cases:
            validator.validate_and_normalize(letters, required)
    end = time.perf_counter()

    return end - start


def benchmark_validate_puzzle(validator, iterations=10000):
    """Benchmark validate_puzzle method"""
    test_cases = [
        ("N", "ACUOTP"),
        ("A", "BCDEFG"),
        ("Z", "YXWVUT"),
    ]

    start = time.perf_counter()
    for _ in range(iterations):
        for center, others in test_cases:
            validator.validate_puzzle(center, others)
    end = time.perf_counter()

    return end - start


def benchmark_is_valid_word(validator, iterations=10000):
    """Benchmark is_valid_word method"""
    letters_set = ["n", "a", "c", "u", "o", "t", "p"]
    required = "n"
    test_words = [
        "noun",
        "count",
        "upon",
        "canon",
        "catnap",
    ]

    start = time.perf_counter()
    for _ in range(iterations):
        for word in test_words:
            validator.is_valid_word(word, letters_set, required)
    end = time.perf_counter()

    return end - start


def run_benchmark(name, benchmark_func, rust_validator, python_validator, iterations=10000):
    """Run a benchmark and print results"""
    print(f"\n{'='*60}")
    print(f"Benchmark: {name}")
    print(f"Iterations: {iterations:,}")
    print(f"{'='*60}")

    if RUST_AVAILABLE:
        rust_time = benchmark_func(rust_validator, iterations)
        print(f"🦀 Rust:   {rust_time:.4f}s ({rust_time * 1000 / iterations:.4f}ms per call)")
    else:
        rust_time = None
        print("🦀 Rust:   Not available")

    if PYTHON_AVAILABLE:
        python_time = benchmark_func(python_validator, iterations)
        print(f"🐍 Python: {python_time:.4f}s ({python_time * 1000 / iterations:.4f}ms per call)")
    else:
        python_time = None
        print("🐍 Python: Not available")

    if rust_time and python_time:
        speedup = python_time / rust_time
        print(f"\n⚡ Speedup: {speedup:.2f}x faster with Rust")

        if speedup < 5:
            emoji = "🔸"
        elif speedup < 10:
            emoji = "🔥"
        elif speedup < 20:
            emoji = "🚀"
        else:
            emoji = "⚡"

        print(f"{emoji} Performance: {'Excellent' if speedup > 10 else 'Good' if speedup > 5 else 'Moderate'}")


def main():
    """Run all benchmarks"""
    print("=" * 60)
    print("InputValidator Benchmark: Rust vs Python")
    print("=" * 60)

    if not RUST_AVAILABLE:
        print("\n❌ Rust module not built. Build it first:")
        print("   cd rust/spelling_bee_validator")
        print("   pip install maturin")
        print("   maturin develop --release")
        return

    if not PYTHON_AVAILABLE:
        print("\n❌ Python module not found")
        return

    rust_validator = RustValidator()
    python_validator = PythonValidator()

    # Run benchmarks
    run_benchmark(
        "validate_letters",
        benchmark_validate_letters,
        rust_validator,
        python_validator,
        iterations=10000
    )

    run_benchmark(
        "validate_required_letter",
        benchmark_validate_required_letter,
        rust_validator,
        python_validator,
        iterations=10000
    )

    run_benchmark(
        "validate_and_normalize",
        benchmark_validate_and_normalize,
        rust_validator,
        python_validator,
        iterations=10000
    )

    run_benchmark(
        "validate_puzzle",
        benchmark_validate_puzzle,
        rust_validator,
        python_validator,
        iterations=10000
    )

    run_benchmark(
        "is_valid_word",
        benchmark_is_valid_word,
        rust_validator,
        python_validator,
        iterations=10000
    )

    print(f"\n{'='*60}")
    print("Benchmark Complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
