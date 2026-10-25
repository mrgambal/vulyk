"""Regression tests for social-auth nonce storage."""

import unittest

from vulyk.social_storage import MongoengineNonceMixinWithAtomicUse


class FakeNonceCollection:
    """Small in-memory stand-in for MongoEngine's atomic upsert operation."""

    def __init__(self) -> None:
        self.records: set[tuple[tuple[str, str | int], ...]] = set()

    def __call__(self, **filters: str | int) -> "FakeNonceQuery":
        return FakeNonceQuery(self.records, tuple(sorted(filters.items())))


class FakeNonceQuery:
    def __init__(self, records: set[tuple[tuple[str, str | int], ...]], key: tuple[tuple[str, str | int], ...]) -> None:
        self.records = records
        self.key = key

    def modify(self, *, set__salt: str, upsert: bool, new: bool) -> object | None:
        if self.key in self.records:
            return object()
        if upsert:
            self.records.add(self.key)
        return None


class TestNonceUse(unittest.TestCase):
    collection: FakeNonceCollection
    nonce_model: type

    def setUp(self) -> None:
        self.collection = FakeNonceCollection()
        self.nonce_model = type("Nonce", (MongoengineNonceMixinWithAtomicUse,), {"objects": self.collection})

    def test_first_use_creates_nonce(self):
        self.assertTrue(self.nonce_model.use("server", 123, "salt"))
        self.assertEqual(len(self.collection.records), 1)

    def test_repeated_use_does_not_create_duplicate(self):
        self.assertTrue(self.nonce_model.use("server", 123, "salt"))
        self.assertFalse(self.nonce_model.use("server", 123, "salt"))
        self.assertEqual(len(self.collection.records), 1)


if __name__ == "__main__":
    unittest.main()
