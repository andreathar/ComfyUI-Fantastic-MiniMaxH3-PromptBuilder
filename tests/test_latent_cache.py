import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class LatentCacheIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        package = types.ModuleType("cache_identity_test")
        package.__path__ = [str(root)]
        media = types.ModuleType("cache_identity_test.media_io")
        media.resolve = str
        spec = importlib.util.spec_from_file_location("cache_identity_test.latent_cache", root / "latent_cache.py")
        cls.cache = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {package.__name__: package, media.__name__: media}):
            spec.loader.exec_module(cls.cache)

    def test_same_basename_size_and_time_in_different_directories_do_not_share_latents(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = (Path(directory) / name / "reference.png" for name in ("a", "b"))
            for path, content in ((a, b"first"), (b, b"other")):
                path.parent.mkdir()
                path.write_bytes(content)
                os.utime(path, ns=(1700000000000000000, 1700000000000000000))
            self.assertNotEqual(self.cache.file_stamp(a), self.cache.file_stamp(b))

    def test_same_size_edit_within_a_second_invalidates_latents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference.png"
            path.write_bytes(b"first")
            os.utime(path, ns=(1700000000000000000, 1700000000100000000))
            before = self.cache.file_stamp(path)
            path.write_bytes(b"other")
            os.utime(path, ns=(1700000000000000000, 1700000000200000000))
            self.assertNotEqual(before, self.cache.file_stamp(path))


if __name__ == "__main__":
    unittest.main()
