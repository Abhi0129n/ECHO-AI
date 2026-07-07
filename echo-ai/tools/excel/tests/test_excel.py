import os
import shutil
import unittest
from tools.excel.excel_service import ExcelService
from tools.excel.excel_utils import column_converter, validate_sheet, validate_cell, format_table

class TestExcelService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = os.path.abspath("uploads/test_excel_temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.excel_path = os.path.join(self.temp_dir, "test.xlsx")
        self.service = ExcelService()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_utils(self):
        # Column letter to index
        self.assertEqual(column_converter("A"), 1)
        self.assertEqual(column_converter("Z"), 26)
        self.assertEqual(column_converter("AA"), 27)
        # Column index to letter
        self.assertEqual(column_converter(1), "A")
        self.assertEqual(column_converter(26), "Z")
        self.assertEqual(column_converter(27), "AA")
        
        # Validations
        self.assertTrue(validate_sheet("Expenses"))
        self.assertFalse(validate_sheet("In:Out")) # Invalid colon character
        
        self.assertTrue(validate_cell("A1"))
        self.assertTrue(validate_cell("XFD1048576"))
        self.assertFalse(validate_cell("1A"))
        
        # Table Formatter
        headers = ["id", "name"]
        rows = [[1, "Alice"], [2, "Bob"]]
        formatted = format_table(headers, rows)
        self.assertEqual(formatted[0]["name"], "Alice")
        self.assertEqual(formatted[1]["id"], 2)

    def test_service_create_and_open(self):
        res = self.service.create_workbook(self.excel_path, ["Sales", "Inventory"])
        self.assertEqual(res.path, self.excel_path)
        self.assertIn("Sales", res.sheets)
        
        open_res = self.service.open_workbook(self.excel_path)
        self.assertEqual(open_res.path, self.excel_path)

    def test_service_write_read(self):
        self.service.create_workbook(self.excel_path)
        self.service.write_cell(self.excel_path, "Sheet1", "B2", "HelloExcel")
        val = self.service.read_cell(self.excel_path, "Sheet1", "B2")
        self.assertIsNotNone(val)

    def test_service_append(self):
        self.service.create_workbook(self.excel_path)
        self.service.append_row(self.excel_path, "Sheet1", [1, "John", "Doe"])
        self.service.append_column(self.excel_path, "Sheet1", ["A", "B", "C"])
        
        rows = self.service.read_sheet(self.excel_path, "Sheet1")
        self.assertTrue(len(rows) > 0)

if __name__ == "__main__":
    unittest.main()
