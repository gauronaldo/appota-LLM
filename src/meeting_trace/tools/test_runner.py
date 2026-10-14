"""Discover unit, integration, and regression tests with the src package."""
import sys
import unittest

from ..config import PATHS


def main():
    suite = unittest.defaultTestLoader.discover(
        str(PATHS.root / 'tests'), pattern='test_*.py', top_level_dir=str(PATHS.root))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
