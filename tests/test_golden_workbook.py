import unittest

from pipeline.common import configuration
from pipeline.golden_workbook import LABEL_COLUMNS, validate_cells


class GoldenWorkbookTests(unittest.TestCase):
    def fixture(self):
        rows = [{"review_id": "invented-" + str(i), "review_text": "Invented review text"} for i in range(50)]
        cells = {col + "5": field for col, field in dict(LABEL_COLUMNS, B="review_text", L="review_id").items()}
        for index, row in enumerate(rows, 6):
            cells["B" + str(index)] = row["review_text"]
            cells["L" + str(index)] = row["review_id"]
        return rows, cells

    def test_blank_remains_incomplete_and_valid_human_values_convert(self):
        rows, cells = self.fixture()
        self.assertEqual(validate_cells(cells, rows, configuration()), (0, []))
        for index in range(6, 56):
            for col, value in zip("CDEFGHI", ["other", "unclear", "1", "0", "true", "[]", "Invented review text"]):
                cells[col + str(index)] = value
        count, exported = validate_cells(cells, rows, configuration())
        self.assertEqual(count, 50)
        self.assertEqual([r["review_id"] for r in exported], [r["review_id"] for r in rows])
        self.assertEqual(exported[0]["needs_review"], "true")

    def test_changed_source_and_formula_answers_are_rejected(self):
        rows, cells = self.fixture()
        cells["B6"] = "Changed source"
        with self.assertRaisesRegex(ValueError, "text changed"):
            validate_cells(cells, rows, configuration())
        cells["B6"] = rows[0]["review_text"]
        cells["C6"] = {"formula": True}
        with self.assertRaisesRegex(ValueError, "not formulas"):
            validate_cells(cells, rows, configuration())

