import unittest
from pipeline.runner import restore_source_whitespace
class QuoteWhitespaceTests(unittest.TestCase):
    def test_restore_only_whitespace_from_source(self):
        self.assertEqual(restore_source_whitespace("cannot log in or make an account", "I cannot log in or \nmake an account today"), "cannot log in or \nmake an account")
    def test_does_not_repair_fabricated_or_case_changed_words(self):
        for quote in ("Cannot log in", "cannot sign in"):
            self.assertEqual(restore_source_whitespace(quote, "cannot log in"), quote)
    def test_preserve_existing_exact_span(self):
        self.assertEqual(restore_source_whitespace("a  b", "a  b"), "a  b")
