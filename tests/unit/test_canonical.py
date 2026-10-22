import datetime
import unittest

from amca.canonical import canonical_json, sha256
from amca.errors import InputError


class CanonicalTests(unittest.TestCase):
    def test_object_key_order_is_canonical(self):
        self.assertEqual(canonical_json({"b": 2, "a": 1}), b'{"a":1,"b":2}')
        self.assertEqual(sha256({"b": 2, "a": 1}), sha256({"a": 1, "b": 2}))

    def test_rejects_nonfinite_and_non_json_values(self):
        for value in (float("nan"), float("inf"), datetime.datetime.now(), {1: "bad"}):
            with self.subTest(value=value), self.assertRaises(InputError):
                canonical_json(value)

    def test_utf8_is_stable(self):
        self.assertEqual(canonical_json({"text": "é"}), '{"text":"é"}'.encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
