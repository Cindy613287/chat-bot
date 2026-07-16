import tempfile
import unittest
from pathlib import Path

from app.knowledge import KnowledgeBase


class KnowledgeBaseTests(unittest.TestCase):
    def test_upload_load_and_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            base = KnowledgeBase(Path(directory))
            base.save_upload("课程.txt", "课程内容".encode())
            self.assertIn("课程内容", base.load_content(max_chars=100))
            base.delete("课程.txt")
            self.assertEqual(base.list_files(), [])

    def test_rejects_unsafe_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            base = KnowledgeBase(Path(directory))
            with self.assertRaises(ValueError):
                base.save_upload("../secret.txt", b"secret")


if __name__ == "__main__":
    unittest.main()
