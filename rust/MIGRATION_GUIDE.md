# 🦀 Rust Migration Guide for NYT Spelling Bee Solver

Complete guide for migrating Python components to Rust for performance.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Phase 1: InputValidator (Current)](#phase-1-inputvalidator-current)
3. [Phase 2: Phonotactic Filter](#phase-2-phonotactic-filter)
4. [Phase 3: Candidate Generator](#phase-3-candidate-generator)
5. [Phase 4: Advanced Components](#phase-4-advanced-components)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### Why Rust?

- ⚡ **Performance**: 5-100x faster than Python for compute-intensive tasks
- 🔒 **Safety**: Compile-time guarantees prevent entire classes of bugs
- 🧵 **Concurrency**: Fearless parallelism with rayon
- 📦 **Zero-cost abstractions**: Fast without sacrificing ergonomics

### Migration Strategy

**Incremental approach**: Migrate one component at a time, validate performance, integrate.

```
Phase 1: InputValidator (Learning) ✅ CURRENT
    ↓
Phase 2: Phonotactic Filter (High Impact)
    ↓
Phase 3: Candidate Generator (Parallel Processing)
    ↓
Phase 4: Dictionary Manager, NYT Filter, etc.
```

---

## Phase 1: InputValidator (Current)

**Status:** ✅ Complete
**Location:** `rust/spelling_bee_validator/`
**Expected Speedup:** 10-20x

### What Was Migrated

- ✅ Letter validation (length, uniqueness, alphabetic)
- ✅ Required letter validation
- ✅ Puzzle validation (center + 6 others)
- ✅ Word validation logic
- ✅ Constants (MIN_WORD_LENGTH, etc.)

### Build & Test

```bash
cd rust/spelling_bee_validator

# Build (release mode for performance)
./build.sh

# Or manually:
maturin develop --release

# Test
pytest python_tests/test_integration.py -v

# Benchmark
python python_tests/benchmark.py
```

### Integration

**Option 1: Drop-in replacement**
```python
# Before
from src.spelling_bee_solver.core.input_validator import InputValidator

# After
from spelling_bee_validator import InputValidator  # Rust module
```

**Option 2: Hybrid with fallback**
```python
try:
    from spelling_bee_validator import InputValidator
    USING_RUST = True
except ImportError:
    from src.spelling_bee_solver.core.input_validator import InputValidator
    USING_RUST = False
```

### Lessons Learned

✅ **What worked well:**
- PyO3 makes Python bindings easy
- Error handling with `PyResult` is clean
- Drop-in replacement requires no Python code changes

⚠️ **Challenges:**
- Initial maturin setup learning curve
- Converting Python collections to Rust types
- Ensuring error messages match Python version

---

## Phase 2: Phonotactic Filter

**Status:** 📋 Planned
**Location:** `rust/phonotactic_filter/` (to be created)
**Expected Speedup:** 10-100x

### Why This Next?

1. **Pure algorithmic code** - No external dependencies
2. **Performance-critical** - Called thousands of times per solve
3. **Pattern matching heaven** - Rust's strength
4. **Self-contained** - Easy to test in isolation

### Implementation Plan

#### 1. Create Project Structure

```bash
cargo new --lib rust/phonotactic_filter
cd rust/phonotactic_filter
```

#### 2. Update Cargo.toml

```toml
[package]
name = "phonotactic_filter"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
```

#### 3. Key Implementation Details

**Triple letter detection** (currently ~100 lines Python → ~10 lines Rust):

```rust
pub fn has_triple_letters(letters: &str) -> bool {
    let bytes = letters.as_bytes();
    bytes.windows(3).any(|w| w[0] == w[1] && w[1] == w[2])
}
```

**Impossible doubles** (currently ~50 lines Python → ~5 lines Rust):

```rust
const IMPOSSIBLE_DOUBLES: &[&str] = &["hh", "jj", "qq", "vv", "xx", "yy"];

pub fn has_impossible_doubles(letters: &str) -> bool {
    IMPOSSIBLE_DOUBLES.iter().any(|&double| letters.contains(double))
}
```

**Parallel filtering** (new capability!):

```rust
use rayon::prelude::*;

pub fn filter_permutations_parallel(perms: Vec<String>) -> Vec<String> {
    perms.par_iter()
        .filter(|perm| is_valid_sequence(perm))
        .cloned()
        .collect()
}
```

#### 4. PyO3 Bindings

```rust
#[pyclass]
pub struct PhonotacticFilter {
    rules: PhonotacticRules,
    stats: HashMap<String, usize>,
}

#[pymethods]
impl PhonotacticFilter {
    #[new]
    fn new() -> Self { /* ... */ }

    fn is_valid_sequence(&mut self, letters: &str) -> bool { /* ... */ }

    fn filter_permutations(&mut self, perms: Vec<String>) -> Vec<String> { /* ... */ }
}
```

#### 5. Testing Strategy

```python
# Python integration test
def test_rust_vs_python():
    from phonotactic_filter import PhonotacticFilter as RustFilter
    from src.spelling_bee_solver.core.phonotactic_filter import PhonotacticFilter as PyFilter

    rust = RustFilter()
    python = PyFilter()

    test_words = ["hello", "hlllo", "xxyz", "world"]

    for word in test_words:
        assert rust.is_valid_sequence(word) == python.is_valid_sequence(word)
```

#### 6. Benchmarking

Expected results:
- Single validation: 10-50x faster
- Batch filtering (1000 words): 20-100x faster
- Parallel filtering: 50-200x faster (with rayon)

---

## Phase 3: Candidate Generator

**Status:** 📋 Planned
**Location:** `rust/candidate_generator/`
**Expected Speedup:** 5-50x (50-200x with parallelism)

### Why This Is High Impact

1. **Iterates 100k+ dictionary words** - Very hot path
2. **Heavy set operations** - Rust's HashSet is 2-3x faster
3. **Perfect for parallelism** - Use all CPU cores with rayon
4. **Memory-intensive** - Rust's zero-copy strings save RAM

### Implementation Plan

#### Core Algorithm (Parallel)

```rust
use rayon::prelude::*;
use rustc_hash::FxHashSet;

pub fn generate_candidates_parallel(
    dictionary: &FxHashSet<String>,
    letters: &str,
    required_letter: char,
    min_length: usize,
) -> Vec<String> {
    let letters_set: FxHashSet<char> = letters.chars().collect();

    dictionary
        .par_iter()  // 🚀 Parallel iteration!
        .filter(|word| {
            word.len() >= min_length
                && word.contains(required_letter)
                && word.chars().all(|c| letters_set.contains(&c))
        })
        .cloned()
        .collect()
}
```

#### Optimizations

**1. Use FxHashSet (faster than std HashMap)**
```rust
use rustc_hash::FxHashSet;  // 2-3x faster for small keys
```

**2. Zero-copy string slicing**
```rust
// No allocations - just borrows
let letters_set: FxHashSet<char> = letters.chars().collect();
word.chars().all(|c| letters_set.contains(&c))
```

**3. Early termination**
```rust
// Stop as soon as we find invalid character
word.chars().all(|c| letters_set.contains(&c))
```

---

## Phase 4: Advanced Components

### 4A. Anagram Generator (New Feature!)

**Status:** 📋 New Feature Enabled by Rust
**Expected Speedup:** 50-500x vs hypothetical Python

This feature is **impractical in Python** but becomes viable in Rust:

```rust
use rayon::prelude::*;

pub fn generate_anagrams(
    letters: &str,
    dictionary: &FxHashSet<String>,
) -> Vec<String> {
    let mut chars: Vec<char> = letters.chars().collect();

    permutohedron::heap_recursive(&mut chars, |perm| {
        let word: String = perm.iter().collect();
        if dictionary.contains(&word) {
            // Found valid anagram
        }
    });

    // Use parallel processing for 7! = 5,040 permutations
}
```

### 4B. Dictionary Manager

**Benefits:**
- Async HTTP downloads with `tokio` + `reqwest`
- Fast JSON parsing with `serde`
- Memory-mapped file I/O

```rust
use tokio;
use reqwest;

#[tokio::main]
async fn download_dictionary(url: &str) -> Result<FxHashSet<String>> {
    let body = reqwest::get(url).await?.text().await?;
    // Parse and return dictionary
}
```

### 4C. NYT Rejection Filter

**Benefits:**
- Compiled regex patterns (faster than Python `re`)
- Efficient set lookups

```rust
use regex::Regex;
use once_cell::sync::Lazy;

static FOREIGN_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"aa|ii|uu").unwrap()
});

#[inline]
pub fn is_foreign_word(word: &str) -> bool {
    FOREIGN_PATTERN.is_match(word)
}
```

---

## Best Practices

### 1. Always Use Release Mode for Benchmarks

```bash
# ❌ Wrong - debug mode is 10-100x slower!
maturin develop

# ✅ Correct - release mode with optimizations
maturin develop --release
```

### 2. Profile Before Optimizing

```bash
# Use cargo flamegraph for visual profiling
cargo install flamegraph
cargo flamegraph --bench my_bench
```

### 3. Use `#[inline]` for Hot Functions

```rust
#[inline]
pub fn is_valid_letter(c: char) -> bool {
    c.is_alphabetic()
}
```

### 4. Leverage Const Evaluation

```rust
// Computed at compile time!
const MAX_PERMUTATIONS: usize = factorial(7);  // 5,040

const fn factorial(n: usize) -> usize {
    match n {
        0 | 1 => 1,
        _ => n * factorial(n - 1),
    }
}
```

### 5. Use Appropriate Hash Functions

```rust
// For small keys (chars, small strings)
use rustc_hash::FxHashSet;  // Faster

// For larger keys or crypto
use std::collections::HashSet;  // More robust
```

### 6. Measure Memory Usage

```bash
# Use heaptrack or valgrind
heaptrack python script.py
heaptrack_gui heaptrack.python.*.zst
```

---

## Troubleshooting

### Build Issues

**Problem:** `error: linker 'cc' not found`

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install build-essential

# macOS (install Xcode Command Line Tools)
xcode-select --install
```

**Problem:** `maturin: command not found`

**Solution:**
```bash
pip install --upgrade maturin
```

### Import Issues

**Problem:** `ImportError: No module named 'spelling_bee_validator'`

**Solution:**
```bash
# Rebuild the module
cd rust/spelling_bee_validator
maturin develop --release

# Verify installation
python -c "import spelling_bee_validator; print('Success!')"
```

### Performance Issues

**Problem:** Rust is not faster than Python

**Checklist:**
1. ✅ Built in release mode? (`--release`)
2. ✅ Using efficient data structures? (FxHashSet, etc.)
3. ✅ Avoiding unnecessary allocations?
4. ✅ Profiled to find bottlenecks?

### Testing Issues

**Problem:** Tests fail with "module not found"

**Solution:**
```bash
export PYTHONPATH=/home/user/nytspellingbeesolver:$PYTHONPATH
cd /home/user/nytspellingbeesolver
pytest rust/spelling_bee_validator/python_tests/ -v
```

---

## Performance Expectations

### Summary Table

| Component | Python (ms) | Rust (ms) | Speedup | Priority |
|-----------|-------------|-----------|---------|----------|
| **InputValidator** | ~1 | ~0.05 | **20x** | ✅ Done |
| **Phonotactic Filter** | ~100 | ~1-10 | **10-100x** | 🔥 Next |
| **Candidate Generator** | ~500 | ~50-100 | **5-10x** | 🔥 Next |
| **Anagram Generator** | ~30,000 | ~100-500 | **60-300x** | 🚀 New! |
| **Dictionary Manager** | ~200 | ~50-100 | **2-4x** | ⭐ Later |
| **NYT Rejection Filter** | ~50 | ~10-20 | **2-5x** | ⭐ Later |
| **Overall Solve Time** | **2,000-5,000** | **200-1,000** | **5-10x** | 🎯 Goal |

---

## Next Steps

1. ✅ **Complete Phase 1** (InputValidator)
   - Build and test Rust module
   - Run benchmarks
   - Integrate into Python codebase

2. 🔥 **Start Phase 2** (Phonotactic Filter)
   - Create new Rust project
   - Implement core algorithms
   - Add parallel processing
   - Benchmark against Python

3. 🚀 **Plan Phase 3** (Candidate Generator)
   - Design parallel architecture
   - Implement with rayon
   - Optimize memory usage

4. 📚 **Document learnings**
   - Update this guide with findings
   - Add performance data
   - Share optimization techniques

---

## Resources

- [PyO3 User Guide](https://pyo3.rs/) - Python bindings for Rust
- [Maturin](https://www.maturin.rs/) - Build tool for Rust Python extensions
- [Rust Book](https://doc.rust-lang.org/book/) - Learn Rust
- [Rust Performance Book](https://nnethercote.github.io/perf-book/) - Optimization techniques
- [rayon](https://docs.rs/rayon/) - Data parallelism library

---

**Happy Rust Migration! 🦀✨**
