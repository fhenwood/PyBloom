from typing import List
import struct
from dataclasses import asdict
from .types import XBloomRecipe, PourStep, PourPattern, VibrationPattern, CupType, MachineModel


def build_recipe_payload(recipe: XBloomRecipe) -> bytes:
    """
    Compiles an XBloomRecipe into the binary payload for BLE commands 8001/8004.
    
    Reverse-engineered through BLE traffic analysis and validated against
    XBRecipeWriter NFC card format.
    
    Payload Structure:
        LENGTH_BYTE (1 byte) - size of body only
        BODY - pour data
        FOOTER (2 bytes) - [grindSize, totalWater*10]
    
    Pour Data Format (per pour):
        Sub-steps (4 bytes each): [Volume, Temperature, Pattern, Vibration]
            - Volume is chunked into 127ml max per sub-step
            - Pattern: 0=Centered, 1=Circular, 2=Spiral
            - Vibration: 0=None, 1=Before, 2=After, 3=Both
        Metadata (4 bytes): [PauseByte, 0, RPM, FlowRate*10]
            - PauseByte = (-pause) & 0xFF (two's complement)
            - RPM only set for first pour (grinder speed)
            - FlowRate is multiplied by 10
    
    Protocol Notes:
        - This payload is sent with command 8001 (with grinding) or 8004 (without)
        - The dose (bean weight) is NOT in this payload - it's sent via bypass (8102)
        - Cup type is NOT in this payload - it's sent via set_cup (8104)
    
    Args:
        recipe: XBloomRecipe containing grind settings, pours, etc.
        
    Returns:
        Binary payload bytes ready to send via BLE
    """
    hex_parts: List[bytes] = []
    
    # Iterate pours
    for i, pour in enumerate(recipe.pours):
        # 1. Sub-steps (Volume chunks)
        # Java logic: splits volume into 127 units max per chunk
        # Each chunk: [Volume, Temp, Pattern, Vibration]
        sub_steps: List[bytes] = []
        
        remaining_vol = pour.volume
        
        # Helper to pack a sub-step
        def pack_sub_step(vol: int):
            # Volume, Temp, Pattern, Vibration
            return struct.pack('BBBB', 
                               vol, 
                               pour.temperature, 
                               int(pour.pattern), 
                               int(pour.vibration))

        # Chunking loop
        if remaining_vol > 127:
            chunks = remaining_vol // 127
            remainder = remaining_vol % 127
            for _ in range(chunks):
                sub_steps.append(pack_sub_step(127))
            if remainder > 0:
                sub_steps.append(pack_sub_step(remainder))
        else:
            sub_steps.append(pack_sub_step(remaining_vol))
            
        # Add all sub-steps
        hex_parts.extend(sub_steps)
        
        # 2. Step Metadata (Pause, RPM, Flow)
        # Java: i6 = (~pause) + 1  -> This is negation (-pause)
        # Byte 1: -Pause (two's complement for pause duration)
        # Byte 2: 0 (Reserved/Padding)
        # Byte 3: RPM (Only for first pour, else 0)
        # Byte 4: FlowRate * 10
        
        pause_byte = (-pour.pausing) & 0xFF
        flow_byte = int(pour.flow_rate * 10) & 0xFF
        rpm_byte = (recipe.rpm & 0xFF) if i == 0 else 0
        
        meta = struct.pack('BBBB', pause_byte, 0, rpm_byte, flow_byte)
        hex_parts.append(meta)
        
    # Combine all steps
    payload_body = b''.join(hex_parts)
    
    # 3. Footer (2 bytes only!)
    # [GrindSize, TotalWater * 10]
    # NOTE: dose and cup_type are NOT in the footer - sent via separate commands
    grind_byte = recipe.grind_size & 0xFF
    water_byte = (recipe.total_water * 10) & 0xFF
    footer = struct.pack('BB', grind_byte, water_byte)
    
    # 4. Final Structure
    # LENGTH_BYTE + BODY + FOOTER
    body_len = len(payload_body)
    final_payload = struct.pack('B', body_len) + payload_body + footer
    
    return final_payload

def parse_recipe_json(data: dict) -> XBloomRecipe:
    """
    Parse JSON data (from API or test.json) into XBloomRecipe.
    
    Args:
        data: Dictionary containing 'recipeVo' or direct recipe fields
    """
    # Handle wrapped response vs direct object
    root = data.get('recipeVo', data)
    
    pours = []
    # Aliases for list
    raw_pours = root.get('pourList') or root.get('pours') or root.get('steps') or []
    for p_data in raw_pours:
        # Resolve vibration mode
        # 1=Yes, 2=No (Based on App logic)
        vib_before = p_data.get('isEnableVibrationBefore', 2)
        vib_after = p_data.get('isEnableVibrationAfter', 2)
        
        if vib_before == 1 and vib_after == 1:
            vib = VibrationPattern.BOTH
        elif vib_before == 1:
            vib = VibrationPattern.BEFORE
        elif vib_after == 1:
            vib = VibrationPattern.AFTER
        else:
            vib = VibrationPattern.NONE
            
        step = PourStep(
            volume=int(p_data.get('volume', 0)),
            temperature=int(p_data.get('temperature', 93)),
            flow_rate=float(p_data.get('flowRate') or p_data.get('flow_rate') or 0),
            pausing=int(p_data.get('pausing') or p_data.get('pause') or 0),
            pattern=PourPattern(p_data.get('pattern', 2)), # Default to Spiral?
            vibration=vib
        )
        pours.append(step)
        
    dose_val = root.get('dose', 15.0)
    if isinstance(dose_val, str):
        try:
            dose_val = float(dose_val.strip().lower().replace('g', ''))
        except ValueError:
            dose_val = 15.0
            
    cup_val = root.get('cupType', 0)
    if isinstance(cup_val, str):
        if cup_val.upper() == 'TEA':
            cup_val = CupType.TEA
        elif cup_val.upper() == 'OTHER':
            cup_val = CupType.OTHER
        elif cup_val.upper() == 'XPOD':
            cup_val = CupType.X_POD
        elif cup_val.upper() == 'X_DRIPPER' or cup_val.upper() == 'XDripper':
             cup_val = CupType.X_DRIPPER
        else:
            try:
                 cup_val = int(cup_val)
            except:
                 cup_val = 0
            
    # Aliases
    gs = root.get('grinderSize') or root.get('grind_size') or 60
    gw = root.get('grandWater') or root.get('total_water') or 15
    rp = root.get('rpm') or 60
    nm = root.get('theName') or root.get('name') or "Unknown"
    tid = root.get('tableId') or root.get('id') or 0
    
    mt_val = root.get('machineType', 1)
    try:
        if isinstance(mt_val, str):
            if mt_val.isdigit():
                 mt = MachineModel(int(mt_val))
            elif "STUDIO" in mt_val.upper():
                 mt = MachineModel.STUDIO
            else:
                 mt = MachineModel.ORIGINAL
        else:
            mt = MachineModel(int(mt_val))
    except:
        mt = MachineModel.ORIGINAL

    return XBloomRecipe(
        grind_size=int(gs),
        total_water=int(gw),
        rpm=int(rp),
        cup_type=int(cup_val),
        name=str(nm),
        bean_weight=float(dose_val),
        id=int(tid),
        adapted_model=str(root.get('adaptedModel', "Original")),
        machine_type=mt,
        pours=pours
    )
