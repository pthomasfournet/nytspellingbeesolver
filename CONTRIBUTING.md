# Contributing to NYT Spelling Bee Solver

Thank you for your interest in contributing to this project!

## Development Workflow

We use a simple two-branch workflow to keep the `main` branch stable:

```
main   ──────o────────o────────o──────>  (production/stable releases)
              │
dev    ───────┴──o──o──o──o──o──o────>  (active development)
```

### Branches

- **`main`**: Production-ready code. Only receives merges from `dev` after validation.
- **`dev`**: Active development branch. All new features and fixes start here.
- **`backup-before-cleanup`**: Historical backup (don't delete).

### Workflow

1. **Start development**
   ```bash
   git checkout dev
   git pull origin dev
   ```

2. **Make your changes**
   - Write code
   - Add tests
   - Update documentation

3. **Test your changes**
   ```bash
   # Run tests
   ./venv/bin/pytest tests/ -v

   # Run linting
   ./venv/bin/black src/
   ./venv/bin/isort src/
   ./venv/bin/autoflake --remove-all-unused-imports -r src/
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Your descriptive commit message"
   ```

5. **Push to dev**
   ```bash
   git push origin dev
   ```

6. **Merge to main** (after validation)
   ```bash
   git checkout main
   git merge dev
   git push origin main
   git checkout dev  # Switch back to dev
   ```

## Code Quality Standards

- **Python Style**: Follow PEP 8
- **Formatting**: Use `black` (line length: 88)
- **Import Sorting**: Use `isort`
- **Type Hints**: Recommended for new code
- **Tests**: Add tests for new features
- **Documentation**: Update docstrings and README

## Running Tests

```bash
# All tests
./venv/bin/pytest tests/ -v

# Specific test file
./venv/bin/pytest tests/test_basic.py -v

# With coverage
./venv/bin/pytest tests/ -v --cov=src/spelling_bee_solver
```

## Project Structure

```
spelling_bee_solver_project/
├── src/spelling_bee_solver/     # Main package
│   ├── unified_solver.py        # Core solver
│   ├── core/                    # Core functionality
│   │   ├── nyt_rejection_filter.py  # NYT filter
│   │   └── wiktionary_filter.py     # Wiktionary filter
│   ├── data/                    # Data files
│   └── word_filter_cache/       # Cache directory
├── tests/                       # Test suite
├── analysis/                    # Analysis scripts/reports
├── nytbee_parser/              # NYT puzzle parser
├── wiktionary_parser/          # Wiktionary parser
└── data/dictionaries/          # Dictionary files (gitignored)
```

## Validation Workflow

Before merging to `main`, validate with historical puzzles:

```bash
# Run validation on 2,613 historical puzzles
./venv/bin/python3 analysis/solve_all_puzzles.py \
  --output analysis/validation_results.json \
  --workers 12

# Check accuracy
python3 -c "import json; d=json.load(open('analysis/validation_results.json')); print(f'Accuracy: {d[\"statistics\"][\"accuracy_percent\"]:.2f}%')"
```

## Performance Metrics

Current solver performance (as of 2025-10-03):
- **Accuracy**: 93.28%
- **False Positive Rate**: 1.49%
- **False Negative Rate**: 8.79%
- **Dictionaries**: Webster's + ASPELL + SOWPODS (267,751 words)

## Making a Release

1. Ensure all tests pass on `dev`
2. Run validation on historical puzzles
3. Update version in `setup.py` (if applicable)
4. Merge `dev` → `main`
5. Tag the release:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

## Questions?

Open an issue on GitHub or contact the maintainer.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
