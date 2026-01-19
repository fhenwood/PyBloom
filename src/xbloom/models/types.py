from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import List

class DeviceState(Enum):
    """XBloom device operational states"""
    UNKNOWN = "unknown"
    IDLE = "idle"
    GRINDING = "grinding"
    BREWING = "brewing"
    PAUSED = "paused"
    ERROR = "error"
    SLEEPING = "sleeping"

class PourPattern(IntEnum):
    """
    Pour styles supported by the machine.
    CENTER = 0, CIRCULAR = 1, SPIRAL = 2
    """
    CENTER = 0
    CIRCULAR = 1
    SPIRAL = 2

class CupType(IntEnum):
    """
    Cup Types from CupType.kt
    """
    X_POD = 1
    X_DRIPPER = 2
    OTHER = 3
    TEA = 4

class VibrationPattern(IntEnum):
    """Vibration settings for pours"""
    NONE = 0
    BEFORE = 1
    AFTER = 2
    BOTH = 3

class MachineModel(IntEnum):
    """Machine hardware models"""
    ORIGINAL = 1
    STUDIO = 2
    UNKNOWN = 0

@dataclass
class GrinderStatus:
    """Grinder state and settings"""
    is_running: bool = False
    speed: int = 0
    size: int = 0  # Grind size setting
    position: int = 0  # Gear position

@dataclass
class BrewerStatus:
    """Brewer state and settings"""
    is_running: bool = False
    temperature: float = 0.0  # Current temperature in °C
    target_temperature: float = 92.0  # Target temperature
    mode: int = 0

@dataclass
class ScaleStatus:
    """Scale state and readings"""
    weight: float = 0.0  # Weight in grams
    is_tared: bool = False

@dataclass
class DeviceStatus:
    """Complete device status"""
    state: DeviceState = DeviceState.UNKNOWN
    connected: bool = False
    grinder: GrinderStatus = field(default_factory=GrinderStatus)
    brewer: BrewerStatus = field(default_factory=BrewerStatus)
    scale: ScaleStatus = field(default_factory=ScaleStatus)
    
    # Machine Info
    serial_number: str = ""
    model: str = ""
    version: str = ""
    water_level_ok: bool = False
    water_volume: int = 0
    
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class PourStep:
    volume: int
    temperature: int
    flow_rate: float = 3.0
    pausing: int = 0
    pattern: PourPattern = PourPattern.SPIRAL
    vibration: VibrationPattern = VibrationPattern.NONE
    # Additional fields if needed
    
    def __post_init__(self):
        # TEST-FLOW-001: Valid flow rate range 3.0-3.5 (approx)
        # Spec says <3.0 or >3.5 rejected. 
        if self.flow_rate < 3.0 or self.flow_rate > 3.5:
             # Allow 0 for pause steps or non-pouring? No, pour step sends water.
             if self.flow_rate != 0: # If flow 0 is possible?
                 raise ValueError(f"Flow rate {self.flow_rate} out of range (3.0-3.5)")
        
        # TEST-TEMP-001: 40-100 (Includes BP=100)
        # 0 = Room Temp (RT) ?
        if self.temperature != 0 and (self.temperature < 40 or self.temperature > 100):
             raise ValueError(f"Temperature {self.temperature} out of range (40-100)")
             
        # TEST-VOL-001: Volume limits (Must be positive)
        if self.volume < 0:
             raise ValueError("Volume must be non-negative")
             
        # TEST-PAUSE-001: Pause limits
        if self.pausing < 0:
             raise ValueError("Pause must be non-negative")

@dataclass
class XBloomRecipe:
    grind_size: int = 60
    total_water: int = 0 # This seems to be Ratio in some contexts, or raw water?
    rpm: int = 60
    cup_type: int = 0
    name: str = "Unknown"
    bean_weight: float = 15.0
    id: int = 0
    adapted_model: str = "Original" # String in JSON? Or ID? User said "Models are 1=Original..." probably ID.
    machine_type: MachineModel = MachineModel.ORIGINAL
    pours: List[PourStep] = field(default_factory=list)
    
    def __post_init__(self):
        # TEST-GRIND-001: 1-80 (Studio), but Official recipes use up to 150?
        # Adjusted to 150 based on Recipes.json analysis
        if not (0 <= self.grind_size <= 150):
             if self.grind_size != 0:
                 raise ValueError(f"Grind size {self.grind_size} out of range (1-150)")
        
        # TEST-RPM-001
        valid_rpms = {0, 60, 70, 80, 90, 100, 110, 120} # 0 for off
        if self.rpm not in valid_rpms:
             raise ValueError(f"RPM {self.rpm} invalid (Must be multiple of 10 in 60-120)")
             
        # TEST-POUR-001: Max 10 pours (Official data has 16)
        # Adjusted to 20
        if len(self.pours) > 20:
             raise ValueError("Max 20 pours allowed")
             
        # TEST-DOSE-001: Valid dose range (0-50g approx?)
        if self.bean_weight < 0 or self.bean_weight > 100:
             raise ValueError(f"Bean weight {self.bean_weight} invalid (0-100)")
