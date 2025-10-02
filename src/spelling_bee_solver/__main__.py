"""
Entry point for running the Spelling Bee Solver as a package.

This allows the solver to be invoked with:
    python3 -m src.spelling_bee_solver
or:
    ./bee (via wrapper script)

This module properly handles package imports and avoids the RuntimeWarning
that occurs when executing a module that's already been imported.
"""

from .unified_solver import main

if __name__ == "__main__":
    main()
