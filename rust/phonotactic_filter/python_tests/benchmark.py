"""
Benchmark: Rust Phonotactic Filter vs Python Implementation

Measures performance improvement of Rust implementation over Python.
Expected speedup: 10-100x depending on operation complexity.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import implementations
try:
    from phonotactic_filter import PhonotacticFilter as RustFilter
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    print("❌ Rust module not available!")
    print("   Build it with: cd rust/phonotactic_filter && maturin develop --release")
    sys.exit(1)

from src.spelling_bee_solver.core.phonotactic_filter import (
    PhonotacticFilter as PyFilter
)


def benchmark_method(rust_filter, py_filter, method_name, *args, iterations=10000):
    """Benchmark a single method"""

    print(f"\n{'=' * 60}")
    print(f"Benchmark: {method_name}")
    print(f"Iterations: {iterations:,}")
    print(f"{'=' * 60}")

    # Warm up
    for _ in range(100):
        getattr(rust_filter, method_name)(*args)
        getattr(py_filter, method_name)(*args)

    # Benchmark Rust
    rust_start = time.perf_counter()
    for _ in range(iterations):
        getattr(rust_filter, method_name)(*args)
    rust_time = time.perf_counter() - rust_start

    # Benchmark Python
    py_start = time.perf_counter()
    for _ in range(iterations):
        getattr(py_filter, method_name)(*args)
    py_time = time.perf_counter() - py_start

    # Calculate speedup
    speedup = py_time / rust_time if rust_time > 0 else 0

    # Results
    print(f"🦀 Rust:   {rust_time:.4f}s ({rust_time/iterations*1000:.4f}ms per call)")
    print(f"🐍 Python: {py_time:.4f}s ({py_time/iterations*1000:.4f}ms per call)")
    print(f"\n⚡ Speedup: {speedup:.2f}x faster with Rust")

    # Performance rating
    if speedup >= 50:
        print(f"🔥🔥🔥 Performance: INCREDIBLE")
    elif speedup >= 20:
        print(f"🔥🔥 Performance: Excellent")
    elif speedup >= 10:
        print(f"🔥 Performance: Very Good")
    elif speedup >= 5:
        print(f"✅ Performance: Good")
    elif speedup >= 2:
        print(f"👍 Performance: Decent")
    else:
        print(f"⚠️  Performance: Minimal improvement")

    return {
        'method': method_name,
        'rust_time': rust_time,
        'python_time': py_time,
        'speedup': speedup,
        'iterations': iterations
    }


def benchmark_batch_filtering(iterations=100):
    """Benchmark batch filtering of permutations"""

    print(f"\n{'=' * 60}")
    print(f"Benchmark: Batch Permutation Filtering")
    print(f"Iterations: {iterations:,} (each with 1,000 permutations)")
    print(f"{'=' * 60}")

    # Generate test permutations (mix of valid and invalid)
    permutations = [
        "hello", "world", "python", "rust", "chrome",
        "hlllo", "xxyz", "bktest", "aeiou", "bcdfg",
        "strength", "through", "school", "knight", "queue",
        "aaa", "hajj", "navvy", "pktest", "dmtest",
    ] * 50  # 1,000 total permutations

    rust_filter = RustFilter()
    py_filter = PyFilter()

    # Warm up
    for _ in range(10):
        rust_filter.filter_permutations(permutations.copy())
        list(py_filter.filter_permutations(iter(permutations)))

    # Benchmark Rust
    rust_start = time.perf_counter()
    for _ in range(iterations):
        rust_filter.filter_permutations(permutations.copy())
    rust_time = time.perf_counter() - rust_start

    # Benchmark Python
    py_start = time.perf_counter()
    for _ in range(iterations):
        list(py_filter.filter_permutations(iter(permutations)))
    py_time = time.perf_counter() - py_start

    # Calculate speedup
    speedup = py_time / rust_time if rust_time > 0 else 0
    total_checked = iterations * len(permutations)

    # Results
    print(f"Total permutations checked: {total_checked:,}")
    print(f"\n🦀 Rust:   {rust_time:.4f}s ({rust_time/iterations*1000:.2f}ms per batch)")
    print(f"🐍 Python: {py_time:.4f}s ({py_time/iterations*1000:.2f}ms per batch)")
    print(f"\n⚡ Speedup: {speedup:.2f}x faster with Rust")
    print(f"📊 Throughput: Rust={total_checked/rust_time:,.0f} checks/sec, "
          f"Python={total_checked/py_time:,.0f} checks/sec")

    # Performance rating
    if speedup >= 50:
        print(f"🔥🔥🔥 Performance: INCREDIBLE")
    elif speedup >= 20:
        print(f"🔥🔥 Performance: Excellent")
    elif speedup >= 10:
        print(f"🔥 Performance: Very Good")
    elif speedup >= 5:
        print(f"✅ Performance: Good")
    elif speedup >= 2:
        print(f"👍 Performance: Decent")
    else:
        print(f"⚠️  Performance: Minimal improvement")

    return {
        'method': 'filter_permutations (batch)',
        'rust_time': rust_time,
        'python_time': py_time,
        'speedup': speedup,
        'iterations': iterations,
        'total_checked': total_checked
    }


def main():
    """Run all benchmarks"""

    print("=" * 60)
    print("Phonotactic Filter Benchmark: Rust vs Python")
    print("=" * 60)
    print("\n⚠️  IMPORTANT: Make sure Rust module is built in RELEASE mode!")
    print("   maturin develop --release\n")

    rust_filter = RustFilter()
    py_filter = PyFilter()

    results = []

    # Test 1: Simple valid word
    results.append(benchmark_method(
        rust_filter, py_filter,
        "is_valid_sequence", "hello",
        iterations=10000
    ))

    # Test 2: Word with triple letters (early rejection)
    results.append(benchmark_method(
        rust_filter, py_filter,
        "is_valid_sequence", "hlllo",
        iterations=10000
    ))

    # Test 3: Word with impossible doubles
    results.append(benchmark_method(
        rust_filter, py_filter,
        "is_valid_sequence", "xxyz",
        iterations=10000
    ))

    # Test 4: Word with complex cluster validation
    results.append(benchmark_method(
        rust_filter, py_filter,
        "is_valid_sequence", "strength",
        iterations=10000
    ))

    # Test 5: Word with invalid cluster
    results.append(benchmark_method(
        rust_filter, py_filter,
        "is_valid_sequence", "bktest",
        iterations=10000
    ))

    # Test 6: Batch filtering
    results.append(benchmark_batch_filtering(iterations=100))

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}\n")

    print(f"{'Method':<40} {'Speedup':>10}")
    print("-" * 60)
    for result in results:
        method = result['method']
        speedup = result['speedup']
        print(f"{method:<40} {speedup:>9.2f}x")

    avg_speedup = sum(r['speedup'] for r in results) / len(results)
    print("-" * 60)
    print(f"{'Average Speedup':<40} {avg_speedup:>9.2f}x")

    # Overall assessment
    print(f"\n{'=' * 60}")
    print("OVERALL ASSESSMENT")
    print(f"{'=' * 60}\n")

    if avg_speedup >= 50:
        print("🔥🔥🔥 INCREDIBLE Performance Improvement!")
        print(f"Rust is {avg_speedup:.0f}x faster on average - this is MASSIVE!")
    elif avg_speedup >= 20:
        print("🔥🔥 Excellent Performance Improvement!")
        print(f"Rust is {avg_speedup:.0f}x faster on average - well worth it!")
    elif avg_speedup >= 10:
        print("🔥 Very Good Performance Improvement!")
        print(f"Rust is {avg_speedup:.0f}x faster on average - significant win!")
    elif avg_speedup >= 5:
        print("✅ Good Performance Improvement!")
        print(f"Rust is {avg_speedup:.0f}x faster on average - noticeable benefit!")
    elif avg_speedup >= 2:
        print("👍 Decent Performance Improvement")
        print(f"Rust is {avg_speedup:.0f}x faster on average - worthwhile upgrade")
    else:
        print("⚠️  Minimal Performance Improvement")
        print(f"Rust is only {avg_speedup:.1f}x faster - PyO3 overhead may be limiting gains")

    print("\n" + "=" * 60)
    print("🎉 Benchmark Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
