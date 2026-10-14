"""Source layout entry points must work without package installation."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from meeting_trace.config import PATHS


class EntrypointTests(unittest.TestCase):
    def test_extract_command_works_outside_repository_cwd(self):
        with tempfile.TemporaryDirectory(prefix='meeting-trace-cli-') as directory:
            output = Path(directory) / 'result.json'
            result = subprocess.run([
                sys.executable, str(PATHS.root / 'src'), 'extract',
                str(PATHS.examples / '01_change_ab.txt'), '--output', str(output)
            ], cwd=directory, capture_output=True, text=True, encoding='utf-8', timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(len(data['items']), 2)
            self.assertEqual(data['metadata']['engine'], 'local')

    def test_python_module_entrypoint(self):
        result = subprocess.run([sys.executable, '-m', 'meeting_trace', '--help'],
                                cwd=PATHS.root / 'src', capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--port', result.stdout)

    def test_evaluation_command_loads_from_another_cwd(self):
        with tempfile.TemporaryDirectory(prefix='meeting-trace-evaluate-') as directory:
            result = subprocess.run([
                sys.executable, str(PATHS.root / 'src'), 'evaluate', '--help'
            ], cwd=directory, capture_output=True, text=True, encoding='utf-8', timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('--verify-only', result.stdout)
