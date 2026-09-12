import io
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

from qwenapi.auth import is_authorized
from qwenapi.processes import ProcessRegistry
from qwenapi.safe_extract import safe_extract_tar


class SecurityTests(unittest.TestCase):
    def test_auth_requires_exact_bearer_token(self):
        self.assertTrue(is_authorized("Bearer test-key", "test-key"))
        self.assertFalse(is_authorized("Bearer test-key-extra", "test-key"))
        self.assertFalse(is_authorized(None, "test-key"))

    def test_safe_extract_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "bad.tar"
            with tarfile.open(archive_path, "w") as archive:
                info = tarfile.TarInfo("../../outside.txt")
                info.size = len(b"blocked")
                archive.addfile(info, io.BytesIO(b"blocked"))
            with self.assertRaises(ValueError):
                safe_extract_tar(archive_path, Path(tmp) / "destination")

    def test_process_registry_owns_only_registered_child(self):
        process = subprocess.Popen(["python", "-c", "import time; time.sleep(30)"])
        registry = ProcessRegistry()
        registry.register("test-child", process)
        self.assertIn("test-child", registry.running())
        self.assertEqual(registry.terminate_all(), ["test-child"])
        self.assertIsNotNone(process.poll())


if __name__ == "__main__":
    unittest.main()
