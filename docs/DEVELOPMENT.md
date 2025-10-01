# Development Environment

This project uses a comprehensive set of development tools to ensure code
quality, security, and maintainability.

## Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Development Tools

### Code Quality & Linting

- **pylint**: Comprehensive Python linter (current score: 9.76/10)
- **ruff**: Fast Python linter and formatter
- **flake8**: Style guide enforcement
- **mypy**: Static type checking

### Code Formatting

- **black**: Uncompromising Python code formatter
- **isort**: Import statement organizer

### Security

- **bandit**: Security issue scanner for Python code

### Dead Code Detection

- **vulture**: Finds unused code

## Usage Commands

### Code Quality Check

```bash
pylint --score=y spelling_bee_solver.py
```

### Auto-format Code

```bash
black spelling_bee_solver.py
ruff check spelling_bee_solver.py --fix
```

### Security Scan

```bash
bandit spelling_bee_solver.py
```

### Dead Code Analysis with Vulture

```bash
vulture spelling_bee_solver.py
```

### Type Checking

```bash
mypy spelling_bee_solver.py
```

## Features Updated

- **Obscure Word Display**: Now shows obscure words (confidence < 20%)
  tagged with "(obscure)" instead of hiding them
- **Comprehensive Scoring**: Multi-dictionary confidence system with penalty
  for foreign/technical terms
- **Clean Dependencies**: Professional virtual environment with development
  tools

## Code Quality Metrics

- Pylint Score: 9.76/10
- Bandit Security: No issues identified
- Black Formatting: Applied
- Dead Code: Removed
