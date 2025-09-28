import sys
import os
import unittest
import tempfile

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from utils.helpers import parse_cnf_file, validate_clauses, convert_to_sdd_format

class TestHelpers(unittest.TestCase):
    
    def test_parse_cnf_file(self):
        """Test the parsing of a CNF DIMACS file"""
        # Create a temporary CNF file
        cnf_content = """c This is a comment
p cnf 3 3
1 -2 3 0
-1 2 0
1 2 -3 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cnf', delete=False) as temp_file:
            temp_file.write(cnf_content)
            temp_file_path = temp_file.name
        
        try:
            # Parse the CNF file
            clauses = parse_cnf_file(temp_file_path)
            
            # Expected clauses (without the trailing 0)
            expected_clauses = [
                [1, -2, 3],
                [-1, 2],
                [1, 2, -3]
            ]
            
            self.assertEqual(clauses, expected_clauses)
            
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)

    def test_parse_cnf_file_empty(self):
        """Test parsing an empty CNF file"""
        cnf_content = """p cnf 0 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cnf', delete=False) as temp_file:
            temp_file.write(cnf_content)
            temp_file_path = temp_file.name
        
        try:
            clauses = parse_cnf_file(temp_file_path)
            self.assertEqual(clauses, [])
        finally:
            os.unlink(temp_file_path)

    def test_validate_clauses_valid(self):
        """Test validation of valid clauses"""
        valid_clauses = [
            [1, -2, 3],
            [-1, 2],
            [1, 2, -3]
        ]
        
        # Should not raise any exception
        try:
            validate_clauses(valid_clauses)
        except ValueError:
            self.fail("validate_clauses raised ValueError for valid clauses")

    def test_validate_clauses_invalid_type(self):
        """Test validation of clauses with invalid type"""
        invalid_clauses = [
            [1, -2, 3],
            "invalid clause",  # This is not a list
            [1, 2, -3]
        ]
        
        with self.assertRaises(ValueError):
            validate_clauses(invalid_clauses)

    def test_validate_clauses_invalid_literal_type(self):
        """Test validation of clauses with invalid literal types"""
        invalid_clauses = [
            [1, -2, 3],
            [1, "not_an_int", 3],  # Contains a string instead of int
            [1, 2, -3]
        ]
        
        with self.assertRaises(ValueError):
            validate_clauses(invalid_clauses)

    def test_validate_clauses_empty(self):
        """Test validation of empty clauses list"""
        empty_clauses = []
        
        # Should not raise any exception
        try:
            validate_clauses(empty_clauses)
        except ValueError:
            self.fail("validate_clauses raised ValueError for empty clauses")

    def test_convert_to_sdd_format(self):
        """Test conversion of CNF clauses to SDD format"""
        input_clauses = [
            [1, -2, 3],
            [-1, 2],
            [1, 2, -3]
        ]
        
        # Currently, the function just returns the input as-is
        # You may need to update this test when the actual conversion logic is implemented
        result = convert_to_sdd_format(input_clauses)
        self.assertEqual(result, input_clauses)

    def test_convert_to_sdd_format_empty(self):
        """Test conversion of empty clauses list to SDD format"""
        empty_clauses = []
        result = convert_to_sdd_format(empty_clauses)
        self.assertEqual(result, empty_clauses)

if __name__ == "__main__":
    unittest.main()