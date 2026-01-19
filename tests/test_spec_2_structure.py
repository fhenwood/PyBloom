import unittest
from xbloom import XBloomRecipe, PourStep
from xbloom import parse_recipe_json

class TestSpecStructure(unittest.TestCase):
    """
    SECTION 2: RECIPE STRUCTURE VALIDATION
    """

    def test_pour_001_max_count(self):
        """TEST-POUR-001: Maximum pour count"""
        pours = [PourStep(10, 90, 3.0, 0)] * 20
        XBloomRecipe(pours=pours)
        pours = [PourStep(10, 90, 3.0, 0)] * 21
        with self.assertRaises(ValueError): XBloomRecipe(pours=pours)

    def test_pour_002_min_count(self):
        """TEST-POUR-002: Minimum pour count"""
        XBloomRecipe(pours=[]) # Passed

    def test_struct_001_pourlist(self):
        """TEST-STRUCT-001: PourList simple format"""
        data = {"pourList": [{"volume": 10}]}
        r = parse_recipe_json(data)
        self.assertEqual(len(r.pours), 1)
        self.assertEqual(r.pours[0].volume, 10)

    def test_struct_002_steps(self):
        """TEST-STRUCT-002: Steps detailed format"""
        data = {"steps": [{"volume": 10}, {"volume": 20}]}
        r = parse_recipe_json(data)
        self.assertEqual(len(r.pours), 2)
        self.assertEqual(r.pours[1].volume, 20)

    def test_struct_003_priority(self):
        """TEST-STRUCT-003: Structure priority"""
        # Checks if 'pourList' prioritized over 'steps' if both exist?
        # Current implementation: root.get('pourList') OR 'pours' OR 'steps'
        # Logic means 'pourList' wins.
        data = {"pourList": [{"volume": 1}], "steps": [{"volume": 2}]}
        r = parse_recipe_json(data)
        self.assertEqual(r.pours[0].volume, 1)

    # --- JSON Parsing ---
    def test_json_001_int_parsing(self):
        """TEST-JSON-001: Integer value parsing"""
        r = parse_recipe_json({"grinderSize": 50})
        self.assertIsInstance(r.grind_size, int)
        self.assertEqual(r.grind_size, 50)

    def test_json_002_double_parsing(self):
        """TEST-JSON-002: Double value parsing"""
        r = parse_recipe_json({"dose": 15.5})
        self.assertIsInstance(r.bean_weight, float)
        self.assertEqual(r.bean_weight, 15.5)

    def test_json_003_array_parsing(self):
        """TEST-JSON-003: Array value parsing"""
        r = parse_recipe_json({"pours": [{"volume":10}, {"volume":10}]})
        self.assertEqual(len(r.pours), 2)

    def test_json_004_map_parsing(self):
        """TEST-JSON-004: Map value parsing"""
        # Testing nested object "recipeVo"
        data = {"recipeVo": {"grinderSize": 70}}
        r = parse_recipe_json(data)
        self.assertEqual(r.grind_size, 70)

    def test_json_norm_001_aliases(self):
        """TEST-JSON-NORM-001: Grind size aliases"""
        r = parse_recipe_json({"grind_size": 25})
        self.assertEqual(r.grind_size, 25)

    def test_json_norm_002_aliases(self):
        """TEST-JSON-NORM-002: Water total aliases"""
        r = parse_recipe_json({"total_water": 100})
        self.assertEqual(r.total_water, 100)

    def test_json_norm_003_aliases(self):
        """TEST-JSON-NORM-003: Pause aliases"""
        r = parse_recipe_json({"pours": [{"pause": 5}]})
        self.assertEqual(r.pours[0].pausing, 5)
