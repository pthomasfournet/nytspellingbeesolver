# Contributing to NYT Spelling Bee Solver

## Development Workflow

This project uses a two-branch workflow to maintain stability in the main branch:

```
main   ──────o────────o────────o──────>  (production/stable releases)
              │
dev    ───────┴──o──o──o──o──o──o────>  (active development)
```

### Branches

- **main**: Production-ready code. Receives merges from dev after validation.
- **dev**: Active development branch. All new features and fixes originate here.
- **backup-before-cleanup**: Historical backup (preserved for reference).

### Workflow

1. **Initialize development environment**
   ```bash
   git checkout dev
   git pull origin dev
   ```

2. **Implement changes**
   - Write code
   - Add tests
   - Update documentation

3. **Validate changes**
   ```bash
   # Run tests
   ./venv/bin/pytest tests/ -v

   # Run linting
   ./venv/bin/black src/
   ./venv/bin/isort src/
   ./venv/bin/autoflake --remove-all-unused-imports -r src/
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "Descriptive commit message"
   ```

5. **Push to dev branch**
   ```bash
   git push origin dev
   ```

6. **Merge to main** (after validation)
   ```bash
   git checkout main
   git merge dev
   git push origin main
   git checkout dev  # Return to dev branch
   ```

## Code Quality Standards

- **Python Style**: PEP 8 compliance
- **Formatting**: black (line length: 88)
- **Import Sorting**: isort
- **Type Hints**: Recommended for new code
- **Tests**: Required for new features
- **Documentation**: Docstrings and README updates required

## Testing

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
│   │   ├── nyt_rejection_filter.py
│   │   └── wiktionary_filter.py
│   ├── data/                    # Data files
│   └── word_filter_cache/       # Cache directory
├── tests/                       # Test suite
├── analysis/                    # Analysis scripts/reports
├── nytbee_parser/              # NYT puzzle parser
├── wiktionary_parser/          # Wiktionary parser
└── data/dictionaries/          # Dictionary files (gitignored)
```

## Validation Workflow

Before merging to main, validate with historical puzzles:

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

## Release Process

1. Validate all tests pass on dev
2. Run validation on historical puzzles
3. Update version in setup.py (if applicable)
4. Merge dev to main
5. Tag the release:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

## Questions

Open an issue on GitHub or contact the maintainer.

## License

Contributions are licensed under the same license as the project.
