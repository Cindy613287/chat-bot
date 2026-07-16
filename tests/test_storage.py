import hashlib
import tempfile
import unittest
from pathlib import Path

from app.storage import UserStore, hash_password, verify_password


class PasswordTests(unittest.TestCase):
    def test_password_round_trip(self):
        encoded = hash_password("correct-horse")
        self.assertTrue(verify_password("correct-horse", encoded))
        self.assertFalse(verify_password("wrong-password", encoded))

    def test_legacy_hash_is_supported(self):
        legacy = hashlib.sha256("old-password".encode()).hexdigest()
        self.assertTrue(verify_password("old-password", legacy))


class UserStoreTests(unittest.TestCase):
    def test_register_authenticate_and_persist(self):
        with tempfile.TemporaryDirectory() as directory:
            store = UserStore(Path(directory) / "memory.json")
            created, _ = store.register("小明", "secure-pass")
            self.assertTrue(created)
            self.assertTrue(store.authenticate("小明", "secure-pass"))
            self.assertFalse(store.authenticate("小明", "bad-password"))


if __name__ == "__main__":
    unittest.main()
