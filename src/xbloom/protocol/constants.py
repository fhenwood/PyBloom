from enum import IntEnum

class XBloomCommand(IntEnum):
    """XBloom Command IDs"""
    # App commands
    APP_BREWER_PAUSE = 8019
    APP_BREWER_QUIT = 8013
    APP_BREWER_RESTART = 8021
    APP_BREWER_SET_PATTERN = 8016
    APP_BREWER_SET_TEMPERATURE = 4510
    APP_BREWER_START = 4506
    APP_BREWER_STOP = 4507
    APP_GRINDER_IN = 8006
    APP_GRINDER_PAUSE = 8018
    APP_GRINDER_QUIT = 8012
    APP_GRINDER_RESTART = 8020
    APP_GRINDER_START = 3500
    APP_GRINDER_STOP = 3505
    APP_RECIPE_EXECUTE = 8002

    APP_RECIPE_SEND = 8004          # Alias for MANUAL (no grinding)
    APP_RECIPE_SEND_MANUAL = 8004   # Recipe without grinding
    APP_RECIPE_SEND_AUTO = 8001     # Recipe with grinding
    APP_RECIPE_STOP = 40519
    APP_RECIPE_START_QUIT = 8017
    APP_SET_BYPASS = 8102
    APP_SET_CUP = 8104
    APP_TEA_RECIP_CODE = 4513
    APP_TEA_RECIP_MAKE = 4512
    
    # Scale control
    SG_LEFT = 2500
    SG_LEFT_SINGLE = 2503
    SG_RIGHT = 2501
    SG_RIGHT_SINGLE = 2504
    SG_STOP = 2505
    SG_VIBRATE = 2502

class XBloomResponse(IntEnum):
    """XBloom Response/Status codes"""
    RD_AbnormalDoseOrWater = 8204
    RD_AbnormalGearPosition = 8203
    RD_BLOOM = 40510
    RD_BREWER_BEGIN = 9005
    RD_BREWER_COFFEE_START = 40502
    RD_BREWER_IN = 8007
    RD_BREWER_MODE = 8107
    RD_BREWER_PAUSE = 9010
    RD_BREWER_TEMPERATURE = 8108
    RD_BYPASS = 40520
    RD_BackToHome = 8022
    RD_BeforeVibration = 40527
    RD_Brewer_Stop = 40511
    RD_CURRENT_WEIGHT = 10507
    RD_CURRENT_WEIGHT2 = 20501
    RD_CalibrateStart = 50038
    RD_Calibrating = 50039
    RD_CurrentGrinder = 40526
    RD_EASYMODE_BEGIN = 8111
    RD_EASYMODE_RECIPE_NUM = 40525
    RD_EASYMODE_RECIPE_ORDER = 11512
    RD_EASYMODE_RECIPE_SEND = 11510
    RD_EASYMODE_RECIPE_STATE = 11518
    RD_EASYMODE_TYPE = 11511
    RD_ENJOY = 40512
    RD_ENJOY2 = 40513
    RD_ErrorIdling = 40517
    RD_ErrorLackOfWater = 40522
    RD_GRINDER_BEGIN = 9003
    RD_GRINDER_PAUSE = 9009
    RD_GRINDER_SIZE = 8105
    RD_GRINDER_SPEED = 8106
    RD_GearReport = 40505
    RD_Grinder_Stop = 40507
    RD_IN_BREWER = 9001
    RD_IN_GRINDER = 9000
    RD_IN_SCALE = 9002
    RD_LedType = 8103
    RD_MachineActivity = 8023
    RD_MachineInfo = 40521
    RD_MachineNotSleeping = 8011
    RD_MachineSleeping = 8009
    RD_OUT_BREWER = 9006
    RD_OUT_GRINDER = 9004
    RD_OUT_SCALE = 9008
    RD_Pods = 40501
    RD_TEA_RECIP_CHANGE_SOAK_TIME = 8113
    RD_TEA_RECIP_PAUSE = 40515
    RD_TEA_RECIP_RESTART = 9011
    RD_TEA_RECIP_SOAK = 9012
    RD_UNIT_CHANGE = 8015
    RD_WATER_VOLUME = 40523
    RD_WaterSource = 4508

# BLE UUIDs
SERVICE_UUID = "0000e0ff-3c17-d293-8e48-14fe2e4da212"
WRITE_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000ffe2-0000-1000-8000-00805f9b34fb"

def crc16(data: bytes) -> int:
    """Calculate CRC16 (Polynomial 0x8408)"""
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return crc
