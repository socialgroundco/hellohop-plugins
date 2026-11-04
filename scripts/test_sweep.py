"""Exercise the pre-publication scan using isolated, asserted file mutations."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('sweep.py')

class SweepTest(unittest.TestCase):
    def run_scan(self, root):
        return subprocess.run([sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True)

    def test_positive_control_and_zero_hits_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'README.md').write_text('HelloHop\n')
            clean = self.run_scan(root)
            self.assertEqual(clean.returncode, 0, clean.stderr + clean.stdout)
            self.assertIn('positive control: 3/3 planted hits caught', clean.stdout)
            self.assertIn('scan: 1 files, 0 forbidden hits', clean.stdout)
            # The three deliberately retired names must be absent; synthetic
            # occurrences keep this ban live without printing them in the bundle.
            for word in ['wa' + 'gate', 'wh' + 'api', 'ra' + 'mow']:
                target = root / '.hidden.md'
                target.write_text(word.upper() + '\n' + word + '\n')
                self.assertEqual(target.read_text().lower().count(word), 2, 'injection applied')
                bad = self.run_scan(root)
                self.assertEqual(bad.returncode, 1, bad.stderr + bad.stdout)
                self.assertIn('scan: 2 files, 2 forbidden hits', bad.stdout)
                target.unlink()

    def test_missing_target_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_scan(Path(tmp) / 'missing')
            self.assertNotEqual(result.returncode, 0)

    def test_disabled_scanner_fails_its_own_positive_control(self):
        spec = importlib.util.spec_from_file_location('sweep', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = module.forbidden_hits
        module.forbidden_hits = lambda text: []
        self.assertIsNot(module.forbidden_hits, original, 'injection applied')
        with self.assertRaisesRegex(AssertionError, 'positive control'):
            module.assertBanIsLive()

if __name__ == '__main__':
    unittest.main()
