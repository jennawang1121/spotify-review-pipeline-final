import unittest

from pipeline.scope import select_ids


class ScopeTests(unittest.TestCase):
    def test_selection_is_order_independent_nested_and_not_based_on_text(self):
        rows = [{"review_id": str(i), "review_text": "Invented example " + str(i)} for i in range(30)]
        rows.append({"review_id": "empty", "review_text": " \n"})
        first = select_ids(rows, 10, "test-seed")
        self.assertEqual(first, select_ids(reversed(rows), 10, "test-seed"))
        self.assertTrue(first < select_ids(rows, 20, "test-seed"))
        changed = [dict(row, review_text="A different nonempty sentence") for row in rows[:-1]]
        self.assertEqual(first, select_ids(changed, 10, "test-seed"))
        self.assertNotIn("empty", first)
        with self.assertRaises(ValueError):
            select_ids(rows, 31, "test-seed")


if __name__ == "__main__":
    unittest.main()
