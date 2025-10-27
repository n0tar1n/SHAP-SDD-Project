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
        input_clauses = [[1, -2, 3], [-1, 2], [1, 2, -3]]
        
        result = convert_to_sdd_format(input_clauses)
        expected = "p cnf 3 3\n1 -2 3 0\n-1 2 0\n1 2 -3 0\n"
        self.assertEqual(result, expected)

    def test_convert_to_sdd_format_empty(self):
        """Test conversion of empty clauses list to SDD format"""
        empty_clauses = []
        result = convert_to_sdd_format(empty_clauses)
        self.assertEqual(result, "p cnf 0 0\n")  

    def test_validate_json_marginals_valid(self):
        """Test validation of valid marginals"""
        from utils.helpers import validate_json_marginals
        
        valid_marginals = {"x1": 0.2, "x2": 0.8, "x3": 0.5}
        self.assertTrue(validate_json_marginals(valid_marginals))

    def test_validate_json_marginals_invalid_probability(self):
        """Test validation catches invalid probabilities"""
        from utils.helpers import validate_json_marginals
        
        invalid_marginals = {"x1": 1.5, "x2": 0.5}
        with self.assertRaises(ValueError) as cm:
            validate_json_marginals(invalid_marginals)
        self.assertIn("must be in [0,1]", str(cm.exception))

    def test_validate_json_marginals_invalid_name(self):
        """Test validation catches invalid variable names"""
        from utils.helpers import validate_json_marginals
        
        invalid_marginals = {"y1": 0.5, "x2": 0.3}
        with self.assertRaises(ValueError) as cm:
            validate_json_marginals(invalid_marginals)
        self.assertIn("must start with 'x'", str(cm.exception))

    def test_validate_json_entity_valid(self):
        """Test validation of valid entity"""
        from utils.helpers import validate_json_entity
        
        valid_entity = {"x1": 1, "x2": 0, "x3": 1}
        self.assertTrue(validate_json_entity(valid_entity))

    def test_validate_json_entity_invalid_value(self):
        """Test validation catches invalid entity values"""
        from utils.helpers import validate_json_entity
        
        invalid_entity = {"x1": 2, "x2": 0}
        with self.assertRaises(ValueError) as cm:
            validate_json_entity(invalid_entity)
        self.assertIn("must be 0 or 1", str(cm.exception))

    def test_validate_json_compatibility_valid(self):
        """Test compatibility validation with matching variables"""
        from utils.helpers import validate_json_compatibility
        
        marginals = {"x1": 0.5, "x2": 0.7}
        entity = {"x1": 1, "x2": 0}
        self.assertTrue(validate_json_compatibility(marginals, entity))

    def test_validate_json_compatibility_mismatch(self):
        """Test compatibility validation catches mismatched variables"""
        from utils.helpers import validate_json_compatibility
        
        marginals = {"x1": 0.5, "x2": 0.7, "x3": 0.3}
        entity = {"x1": 1, "x2": 0}
        with self.assertRaises(ValueError) as cm:
            validate_json_compatibility(marginals, entity)
        self.assertIn("Variable mismatch", str(cm.exception))

if __name__ == "__main__":
    unittest.main()