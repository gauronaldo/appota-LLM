"""Filesystem configuration shared by web, CLI, and evaluation tools.

The src directory entry point needs no installation and does not depend on cwd.
Installed wheels can point at an external checkout using
MEETING_TRACE_PROJECT_ROOT to supply example data and benchmark fixtures.
"""
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @property
    def examples(self):
        return self.root / 'data' / 'examples'

    @property
    def fixtures(self):
        return self.root / 'tests' / 'fixtures'

    @property
    def benchmarks(self):
        return self.root / 'data' / 'benchmarks'

    @property
    def reports(self):
        return self.root / 'docs' / 'reports'


def project_paths():
    configured = os.environ.get('MEETING_TRACE_PROJECT_ROOT')
    if configured:
        return ProjectPaths(Path(configured).expanduser().resolve())
    for parent in Path(__file__).resolve().parents:
        if (parent / 'pyproject.toml').is_file() and (parent / 'src').is_dir():
            return ProjectPaths(parent)
    return ProjectPaths(Path.cwd().resolve())


PATHS = project_paths()
STATIC_DIR = Path(__file__).resolve().parent / 'web' / 'static'
