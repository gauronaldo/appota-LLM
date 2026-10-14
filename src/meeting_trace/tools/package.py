"""Build a source ZIP and optionally verify it in a clean temporary checkout."""
import argparse
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from ..config import PATHS

ROOT = PATHS.root

ROOT_FILES = ['README.md', 'pyproject.toml', 'requirements.txt', 'run.cmd', 'run.ps1',
              '.env.example', '.gitignore', '.gitattributes', '.editorconfig']
SOURCE_DIRS = ['src', 'tests', 'data', '.github']
SHOWCASE_DOCS = ['docs/architecture.md', 'docs/development.md', 'docs/reports/TESTS.md',
                 'docs/submission/ANSWERS.md', 'docs/submission/AI_LOG.md', 'docs/submission/VIDEO_SCRIPT.md']
EXCLUDED_PARTS = {'__pycache__', '.pytest_cache', '.ruff_cache', '.git', '.venv', 'runtime', 'dist'}


def source_files():
    files = [ROOT / name for name in ROOT_FILES + SHOWCASE_DOCS]
    for name in SOURCE_DIRS:
        for path in (ROOT / name).rglob('*'):
            secret_file = path.name.startswith('.env') and path.name != '.env.example'
            if path.is_file() and not secret_file and not EXCLUDED_PARTS.intersection(path.relative_to(ROOT).parts) and path.suffix not in ('.pyc', '.pyo'):
                files.append(path)
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(description='Package source without venv, credentials, runtime exports, or Git metadata.')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist' / 'meeting-trace-mvp.zip')
    parser.add_argument('--verify', action='store_true', help='Run tests and frozen baseline checks in an extracted checkout.')
    args = parser.parse_args()
    output = args.output.resolve()
    if any(output.is_relative_to(ROOT / name) for name in SOURCE_DIRS):
        parser.exit(1, 'Save archives outside source directories.\n')
    output.parent.mkdir(parents=True, exist_ok=True)
    files = source_files()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
    if args.verify:
        with tempfile.TemporaryDirectory(prefix='meeting-trace-package-') as directory:
            clean = Path(directory).resolve()
            with zipfile.ZipFile(output) as archive:
                for member in archive.namelist():
                    (clean / member).resolve().relative_to(clean)
                archive.extractall(clean)
            commands = [
                [sys.executable, 'src', 'test'],
                [sys.executable, 'src', 'evaluate', '--split', 'dev', '--verify-only'],
                [sys.executable, 'src', 'evaluate', '--split', 'holdout', '--verify-only'],
            ]
            environment = os.environ.copy()
            environment['MEETING_TRACE_PROJECT_ROOT'] = str(clean)
            for command in commands:
                subprocess.run(command, cwd=clean, env=environment, check=True, timeout=60)
    print(f'Source ZIP: {output} ({len(files)} files)', flush=True)


if __name__ == '__main__':
    main()
