import unittest
from xbloom import parse_recipe_json
from xbloom import CupType, MachineModel

class TestSpecCupMachine(unittest.TestCase):
    """
    SECTION 3 & 4: CUP TYPE AND MACHINE
    """

    def test_cup_001_mapping(self):
        """TEST-CUP-001: Cup type mapping"""
        self.assertEqual(int(CupType.TEA), 4)
        r = parse_recipe_json({"cupType": "TEA"})
        self.assertEqual(r.cup_type, CupType.TEA)
        r = parse_recipe_json({"cupType": 4})
        self.assertEqual(r.cup_type, CupType.TEA)

    @unittest.skip("Hardware verification required")
    def test_cup_002_overflow(self):
        """TEST-CUP-002: Cup type affects overflow protection"""
        pass
        
    @unittest.skip("Hardware verification required")
    def test_cup_003_tea_pause(self):
        """TEST-CUP-003: Tea mode extended pauses"""
        pass

    def test_machine_001_adapted(self):
        """TEST-MACHINE-001: adaptedModel values"""
        r = parse_recipe_json({"adaptedModel": "Studio"})
        self.assertEqual(r.adapted_model, "Studio")

    def test_machine_002_types(self):
        """TEST-MACHINE-002: machineType values"""
        r = parse_recipe_json({"machineType": 2})
        self.assertEqual(r.machine_type, MachineModel.STUDIO)
        
        r = parse_recipe_json({"machineType": "STUDIO"})
        self.assertEqual(r.machine_type, MachineModel.STUDIO)
        
        r = parse_recipe_json({"machineType": 1})
        self.assertEqual(r.machine_type, MachineModel.ORIGINAL)

    @unittest.skip("Logic not implemented")
    def test_machine_003_features(self):
        """TEST-MACHINE-003: Feature availability by model"""
        pass
